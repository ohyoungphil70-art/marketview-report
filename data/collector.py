"""
marketview/data/collector.py
시황 데이터 수집 모듈

국내 지수(KOSPI/KOSDAQ): FinanceDataReader (인증 불필요)
국내 지수(KRX300) / 업종 / 투자자수급 / 국채금리: pykrx
  → KRX_ID + KRX_PW 환경변수 설정 시 실데이터, 없으면 graceful fallback
미국 지수: Yahoo Finance
뉴스: 한국경제 RSS
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

load_dotenv()

KST = pytz.timezone("Asia/Seoul")

KOSPI_SECTORS = [
    ("전기전자", "1011"),
    ("화학",    "1006"),
    ("의약품",  "1007"),
    ("운수장비","1013"),
    ("금융업",  "1019"),
    ("건설업",  "1016"),
    ("철강금속","1009"),
    ("통신업",  "1018"),
]


def _date_range(days: int = 10):
    today = datetime.now(KST)
    return (
        (today - timedelta(days=days)).strftime("%Y-%m-%d"),
        today.strftime("%Y-%m-%d"),
    )


def _date_range_krx(days: int = 14):
    today = datetime.now(KST)
    return (
        (today - timedelta(days=days)).strftime("%Y%m%d"),
        today.strftime("%Y%m%d"),
    )


def _find_col(df, keywords: list):
    for col in df.columns:
        if all(k in str(col) for k in keywords):
            return col
    return None


# ── 국내 지수 ──────────────────────────────────────────────────────────────

def _fdr_index(symbol: str, name: str) -> dict:
    """FinanceDataReader로 지수 OHLC 조회"""
    import FinanceDataReader as fdr
    start, end = _date_range(14)
    df = fdr.DataReader(symbol, start=start, end=end)
    if df is None or df.empty or len(df) < 2:
        raise ValueError(f"{name} 데이터 없음")
    close = float(df["Close"].iloc[-1])
    prev  = float(df["Close"].iloc[-2])
    if prev == 0:
        raise ValueError("전일 종가 0")
    chg = close - prev
    pct = (chg / prev) * 100
    return {
        "name": name,
        "close": round(close, 2),
        "change": round(chg, 2),
        "pct":   round(pct, 2),
    }


def _pykrx_index(ticker: str, name: str) -> dict:
    """pykrx로 지수 OHLC 조회 (KRX 계정 필요)"""
    from pykrx import stock
    fromdate, todate = _date_range_krx(14)
    df = stock.get_index_ohlcv_by_date(fromdate, todate, ticker)
    if df is None or df.empty or len(df) < 2:
        raise ValueError(f"{name} 데이터 없음")
    close = float(df["종가"].iloc[-1])
    prev  = float(df["종가"].iloc[-2])
    if prev == 0:
        raise ValueError("전일 종가 0")
    chg = close - prev
    pct = (chg / prev) * 100
    return {
        "name": name,
        "close": round(close, 2),
        "change": round(chg, 2),
        "pct":   round(pct, 2),
    }


def get_krx_indices() -> dict:
    """국내 지수 수집
    KOSPI/KOSDAQ: FinanceDataReader (인증 불필요)
    KRX300: pykrx (KRX 계정 필요, 없으면 0)
    """
    result = {}

    # KOSPI — FDR
    for sym, name in [("KS11", "KOSPI"), ("KQ11", "KOSDAQ")]:
        try:
            import FinanceDataReader as fdr  # noqa: F401
            result[name] = _fdr_index(sym, name)
            print(f"✅ {name}: {result[name]['close']}")
        except Exception as e:
            print(f"[FDR {name}] 오류: {e}")
            result[name] = {"name": name, "close": 0, "change": 0, "pct": 0}

    # KRX300 — pykrx
    try:
        result["KRX300"] = _pykrx_index("5042", "KRX300")
        print(f"✅ KRX300: {result['KRX300']['close']}")
    except Exception as e:
        print(f"[KRX300] pykrx 오류: {e}")
        result["KRX300"] = {"name": "KRX300", "close": 0, "change": 0, "pct": 0}

    return result


# ── 업종 ───────────────────────────────────────────────────────────────────

def get_sector_data() -> list:
    """KOSPI 업종별 등락률 — pykrx (KRX 계정 필요)"""
    try:
        from pykrx import stock
        fromdate, todate = _date_range_krx(14)
        sectors = []
        for display_name, ticker in KOSPI_SECTORS:
            try:
                df = stock.get_index_ohlcv_by_date(fromdate, todate, ticker)
                if df is None or df.empty or len(df) < 2:
                    continue
                close = float(df["종가"].iloc[-1])
                prev  = float(df["종가"].iloc[-2])
                if prev == 0:
                    continue
                pct = (close - prev) / prev * 100
                sectors.append({"name": display_name, "pct": round(pct, 2)})
            except Exception as e:
                print(f"[섹터 {display_name}] 오류: {e}")
        return sorted(sectors, key=lambda x: x["pct"], reverse=True)
    except Exception as e:
        print(f"[섹터] 오류: {e}")
        return []


# ── 투자자 수급 ────────────────────────────────────────────────────────────

def get_investor_data() -> dict:
    """투자자 순매수 (KOSPI, 억원) — pykrx (KRX 계정 필요)"""
    try:
        from pykrx import stock
        fromdate, todate = _date_range_krx(7)

        idx_df = stock.get_index_ohlcv_by_date(fromdate, todate, "1001")
        if idx_df is None or idx_df.empty:
            raise ValueError("거래일 확인 실패")
        last_date = idx_df.index[-1].strftime("%Y%m%d")

        result = {}
        for label, investor in [("외국인", "외국인합계"),
                                  ("기관",   "기관합계"),
                                  ("개인",   "개인")]:
            try:
                df = stock.get_market_net_purchases_of_equities_by_ticker(
                    last_date, market="KOSPI", investor=investor
                )
                if df is None or df.empty:
                    result[label] = 0
                    continue
                col = (
                    _find_col(df, ["순매수거래대금"])
                    or _find_col(df, ["순매수", "대금"])
                    or _find_col(df, ["순매수"])
                )
                if col is None:
                    num_cols = df.select_dtypes("number").columns
                    col = num_cols[-1] if len(num_cols) else None
                if col is None:
                    result[label] = 0
                    continue
                total = int(df[col].sum() / 1e8)
                result[label] = total
                print(f"✅ {label} 순매수: {total:+,}억")
            except Exception as e:
                print(f"[투자자 {label}] 오류: {e}")
                result[label] = 0
        return result
    except Exception as e:
        print(f"[투자자] 오류: {e}")
        return {"외국인": 0, "기관": 0, "개인": 0}


# ── 국채 금리 ──────────────────────────────────────────────────────────────

def get_bond_rate() -> dict:
    """국채 3년 금리 — pykrx bond (KRX 계정 필요)"""
    try:
        from pykrx import bond as krx_bond
        fromdate, todate = _date_range_krx(14)
        df = krx_bond.get_otc_treasury_yields(fromdate, todate)
        if df is None or df.empty:
            raise ValueError("데이터 없음")
        col = _find_col(df, ["3"]) or _find_col(df, ["3년"])
        if col is None:
            raise ValueError(f"3년 컬럼 없음: {list(df.columns)}")
        rate = float(df[col].iloc[-1])
        prev = float(df[col].iloc[-2]) if len(df) >= 2 else rate
        return {"rate": round(rate, 2), "change": round(rate - prev, 3)}
    except Exception as e:
        print(f"[국채] 오류: {e}")
        return {"rate": 0, "change": 0}


def get_deposit() -> dict:
    return {"amount": None}


# ── 미국 지수 ──────────────────────────────────────────────────────────────

def get_us_indices() -> dict:
    """미국 3대 지수 — Yahoo Finance"""
    symbols = {"DOW": "^DJI", "NASDAQ": "^IXIC", "SP500": "^GSPC"}
    results = {}
    headers = {"User-Agent": "Mozilla/5.0"}

    for name, sym in symbols.items():
        try:
            url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
                   f"?interval=1d&range=5d")
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            j = resp.json()
            closes = [c for c in
                      j["chart"]["result"][0]["indicators"]["quote"][0]["close"]
                      if c is not None]
            if len(closes) < 2:
                raise ValueError("데이터 부족")
            prev, curr = closes[-2], closes[-1]
            if prev == 0:
                raise ValueError("전일 종가 0")
            chg = curr - prev
            pct = (chg / prev) * 100
            results[name] = {
                "name": name,
                "close": round(curr, 2),
                "change": round(chg, 2),
                "pct":   round(pct, 2),
            }
            print(f"✅ {name}: {results[name]['close']}")
        except Exception as e:
            print(f"[Yahoo {name}] 오류: {e}")
            results[name] = {"name": name, "close": 0, "change": 0, "pct": 0}

    return results


# ── 뉴스 ───────────────────────────────────────────────────────────────────

NEWS_RSS_URLS = [
    "https://www.hankyung.com/feed/all-news",
    "https://www.mk.co.kr/rss/30000001/",
]


def get_market_news() -> list:
    """주요 뉴스 — 한국경제/매일경제 RSS"""
    headers = {"User-Agent": "Mozilla/5.0"}
    for url in NEWS_RSS_URLS:
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            news = []
            for item in root.findall(".//item")[:5]:
                title = item.findtext("title", "").strip()
                link  = item.findtext("link", "").strip()
                if title:
                    news.append({"title": title, "link": link})
            if news:
                print(f"✅ 뉴스 {len(news)}건 수집 ({url.split('/')[2]})")
                return news
        except Exception as e:
            print(f"[뉴스 {url.split('/')[2]}] 오류: {e}")
    return []


# ── 전체 수집 ──────────────────────────────────────────────────────────────

def collect_all() -> dict:
    print("📡 데이터 수집 시작...")

    print("📊 국내 지수 수집 중...")
    kr_data = get_krx_indices()

    print("📈 업종 데이터 수집 중...")
    sectors = get_sector_data()

    print("💰 투자자 수급 수집 중...")
    investors = get_investor_data()

    print("📉 국채 금리 수집 중...")
    bond = get_bond_rate()

    print("🇺🇸 미국 지수 수집 중...")
    us_data = get_us_indices()

    print("📰 뉴스 수집 중...")
    news = get_market_news()

    result = {
        "date":      datetime.now(KST).strftime("%Y년 %m월 %d일"),
        "kr":        kr_data,
        "us":        us_data,
        "sectors":   sectors,
        "investors": investors,
        "bond":      bond,
        "deposit":   get_deposit(),
        "news":      news,
    }

    print("✅ 데이터 수집 완료")
    return result
