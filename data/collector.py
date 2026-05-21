"""
marketview/data/collector.py
시황 데이터 수집 모듈

KOSPI/KOSDAQ  : FinanceDataReader (인증 불필요)
SOX           : Yahoo Finance (^SOX)
업종별 등락률  : pykrx 우선 → Naver Finance 폴백
투자자 수급    : pykrx (KRX_ID/KRX_PW 필요)
국채 금리      : pykrx 우선 → Naver Finance 폴백
미국 지수      : Yahoo Finance
뉴스          : 한국경제 RSS
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

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def _date_range_fdr(days: int = 14):
    today = datetime.now(KST)
    return (today - timedelta(days=days)).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


def _date_range_krx(days: int = 14):
    today = datetime.now(KST)
    return (today - timedelta(days=days)).strftime("%Y%m%d"), today.strftime("%Y%m%d")


def _find_col(df, keywords: list):
    for col in df.columns:
        if all(k in str(col) for k in keywords):
            return col
    return None


def _last_trading_date() -> str:
    """pykrx에서 가장 최근 거래일 반환"""
    from pykrx import stock
    fromdate, todate = _date_range_krx(14)
    df = stock.get_index_ohlcv_by_date(fromdate, todate, "1001")
    if df is None or df.empty:
        raise ValueError("거래일 확인 실패")
    return df.index[-1].strftime("%Y%m%d")


# ── 국내 지수 ──────────────────────────────────────────────────────────────

def get_krx_indices() -> dict:
    result = {}

    # KOSPI / KOSDAQ — FDR (인증 불필요)
    import FinanceDataReader as fdr
    start, end = _date_range_fdr(14)
    for sym, name in [("KS11", "KOSPI"), ("KQ11", "KOSDAQ")]:
        try:
            df = fdr.DataReader(sym, start=start, end=end)
            if df is None or df.empty or len(df) < 2:
                raise ValueError("데이터 없음")
            close = float(df["Close"].iloc[-1])
            prev  = float(df["Close"].iloc[-2])
            chg   = close - prev
            pct   = chg / prev * 100
            result[name] = {"name": name, "close": round(close, 2),
                            "change": round(chg, 2), "pct": round(pct, 2)}
            print(f"✅ {name}: {result[name]['close']}")
        except Exception as e:
            print(f"[FDR {name}] 오류: {e}")
            result[name] = {"name": name, "close": 0, "change": 0, "pct": 0}

    return result


# ── 필라델피아 반도체 지수 ─────────────────────────────────────────────────

def get_sox_index() -> dict:
    """필라델피아 반도체 지수 (^SOX) — Yahoo Finance"""
    try:
        url = ("https://query1.finance.yahoo.com/v8/finance/chart/%5ESOX"
               "?interval=1d&range=5d")
        resp = requests.get(url, headers=_HEADERS, timeout=10)
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
        pct = chg / prev * 100
        result = {"name": "SOX", "close": round(curr, 2),
                  "change": round(chg, 2), "pct": round(pct, 2)}
        print(f"✅ SOX: {result['close']}")
        return result
    except Exception as e:
        print(f"[SOX] 오류: {e}")
        return {"name": "SOX", "close": 0, "change": 0, "pct": 0}


# ── 업종별 등락률 ──────────────────────────────────────────────────────────

def _sectors_pykrx() -> list:
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
        except Exception:
            pass
    return sectors


def _sectors_naver() -> list:
    from bs4 import BeautifulSoup
    url = "https://finance.naver.com/sise/sise_group.naver?type=upjong"
    r = requests.get(url, headers=_HEADERS, timeout=8)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html.parser")
    sectors = []
    for row in soup.select("table.type_1 tr"):
        cols = row.select("td")
        if len(cols) < 2:
            continue
        name = cols[0].get_text(strip=True)
        pct_str = cols[1].get_text(strip=True).replace("%", "").replace(",", "").strip()
        if not name or not pct_str:
            continue
        try:
            pct = float(pct_str)
            sectors.append({"name": name, "pct": round(pct, 2)})
        except ValueError:
            pass
    return sectors


def get_sector_data() -> list:
    """업종별 등락률 — pykrx 우선, Naver 폴백"""
    try:
        sectors = _sectors_pykrx()
        if sectors:
            print(f"✅ 업종 {len(sectors)}개 (pykrx)")
            return sorted(sectors, key=lambda x: x["pct"], reverse=True)
    except Exception as e:
        print(f"[섹터 pykrx] 오류: {e}")

    try:
        sectors = _sectors_naver()
        if sectors:
            print(f"✅ 업종 {len(sectors)}개 (Naver)")
            return sorted(sectors, key=lambda x: x["pct"], reverse=True)
    except Exception as e:
        print(f"[섹터 Naver] 오류: {e}")

    return []


# ── 투자자 수급 ────────────────────────────────────────────────────────────

def get_investor_data() -> dict:
    """투자자 순매수 (KOSPI 유가증권, 억원) + 전일대비
    pykrx get_market_trading_value_by_date 공개 API 사용"""
    _empty = {"외국인": 0, "기관": 0, "개인": 0,
              "외국인_chg": None, "기관_chg": None, "개인_chg": None}
    try:
        from pykrx import stock
        fromdate, todate = _date_range_krx(14)

        df = stock.get_market_trading_value_by_date(fromdate, todate, "KOSPI")
        if df is None or df.empty or len(df) < 2:
            raise ValueError("데이터 없음")

        print(f"[투자자] 컬럼: {list(df.columns)}")
        print(f"[투자자] 최근 거래일: {df.index[-1].strftime('%Y%m%d')}")

        def _to_awk(v: float) -> int:
            a = abs(v)
            if a == 0:
                return 0
            if a > 1e10:    # 원(KRW) 단위 → 억원
                return int(v / 1e8)
            if a > 5e4:     # 백만원 단위 → 억원
                return int(v / 100)
            return int(v)   # 이미 억원

        result = {}
        for label, candidates in [
            ("외국인", ["외국인합계", "외국인"]),
            ("기관",   ["기관합계",   "기관"]),
            ("개인",   ["개인"]),
        ]:
            col = next((c for c in candidates if c in df.columns), None)
            if col is None:
                print(f"[투자자] '{label}' 컬럼 없음 — 가용: {list(df.columns)}")
                result[label] = 0
                result[f"{label}_chg"] = None
                continue

            today_raw = float(df[col].iloc[-1])
            prev_raw  = float(df[col].iloc[-2])
            print(f"[투자자 raw] {label}: {today_raw:.0f}")

            today_bil = _to_awk(today_raw)
            prev_bil  = _to_awk(prev_raw)
            chg       = today_bil - prev_bil

            result[label] = today_bil
            result[f"{label}_chg"] = chg
            print(f"✅ {label}: {today_bil:+,}억 (전일대비 {chg:+,}억)")

        return result
    except Exception as e:
        print(f"[투자자] 오류: {e}")
        import traceback; traceback.print_exc()
        return _empty


# ── 국채 금리 ──────────────────────────────────────────────────────────────

def _bond_pykrx() -> dict:
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


def _bond_naver() -> dict:
    from bs4 import BeautifulSoup
    url = ("https://finance.naver.com/marketindex/interestDailyQuote.naver"
           "?marketindexCd=IRR_GOVT03Y&page=1")
    r = requests.get(url, headers=_HEADERS, timeout=8)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html.parser")
    rows = soup.select("table tbody tr")
    if not rows:
        raise ValueError("데이터 없음")
    cols = [td.get_text(strip=True) for td in rows[0].select("td")]
    # cols: [날짜, 금리, 전일비, 등락률]
    rate   = float(cols[1])
    change = float(cols[2]) if len(cols) > 2 else 0.0
    return {"rate": round(rate, 2), "change": round(change, 3)}


def get_bond_rate() -> dict:
    """국채 3년 금리 — pykrx 우선, Naver 폴백"""
    try:
        result = _bond_pykrx()
        print(f"✅ 국채 3년: {result['rate']}% (pykrx)")
        return result
    except Exception as e:
        print(f"[국채 pykrx] 오류: {e}")

    try:
        result = _bond_naver()
        print(f"✅ 국채 3년: {result['rate']}% (Naver)")
        return result
    except Exception as e:
        print(f"[국채 Naver] 오류: {e}")

    return {"rate": 0, "change": 0}


def _deposit_naver() -> dict:
    """네이버 금융 투자자예탁금 스크래핑 (조원 단위 반환)"""
    from bs4 import BeautifulSoup
    import re
    url = "https://finance.naver.com/sise/sise_deposit.naver"
    r = requests.get(url, headers=_HEADERS, timeout=8)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html.parser")

    # 예탁금 테이블에서 최근 2행 추출
    rows = soup.select("table.type_1 tr, table.tb_type1 tr, table tr")
    values = []
    for row in rows:
        cols = [td.get_text(strip=True) for td in row.select("td")]
        if len(cols) < 2:
            continue
        for text in cols:
            clean = re.sub(r"[^\d.]", "", text)
            if not clean:
                continue
            try:
                val = float(clean)
                # 고객예탁금 합리적 범위: 30~150조원
                if 30 < val < 150:
                    values.append(val)
            except ValueError:
                pass
        if len(values) >= 2:
            break

    if not values:
        raise ValueError("예탁금 값 없음")

    amount = values[0]
    chg = round(values[0] - values[1], 2) if len(values) >= 2 else None
    return {"amount": round(amount, 2), "change": chg}


def _deposit_krx() -> dict:
    """KRX 투자자예탁금 직접 조회 (pykrx 세션, 조원 단위 반환)"""
    import re
    from pykrx import stock
    from pykrx.website.comm.webio import get_session

    fromdate, todate = _date_range_krx(7)
    idx_df = stock.get_index_ohlcv_by_date(fromdate, todate, "1001")
    if idx_df is None or idx_df.empty:
        raise ValueError("거래일 확인 실패")
    dates = [d.strftime("%Y%m%d") for d in idx_df.index]
    today_date = dates[-1]
    prev_date  = dates[-2] if len(dates) >= 2 else None

    krxs = get_session()
    if krxs is None:
        raise ValueError("KRX 세션 없음")
    headers = krxs.get_headers()

    def _fetch(date: str):
        resp = krxs.session.post(
            "https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd",
            data={"bld": "dbms/MDC/STAT/standard/MDCSTAT04701",
                  "locale": "ko_KR", "trdDd": date},
            headers=headers, timeout=15,
        )
        j = resp.json()
        output = j.get("output", [])
        print(f"[예탁금 KRX {date}] 행={len(output)}"
              + (f", 첫행={output[0]}" if output else ""))
        return output

    def _parse_jo(rows, key=None):
        """output 행에서 예탁금 값(조원) 추출"""
        for row in rows:
            for k, v in row.items():
                if key and k != key:
                    continue
                raw = re.sub(r"[^\d]", "", str(v))
                if not raw:
                    continue
                try:
                    num = int(raw)
                    # 단위 자동 판별: 예탁금은 40~100조원 범위
                    if num > 1e12:       # 원 단위
                        return round(num / 1e12, 2)
                    elif num > 1e8:      # 억원 단위
                        return round(num / 1e4, 2)
                    elif num > 1e4:      # 백만원 단위
                        return round(num / 1e6, 2)
                    elif 30 < num < 150: # 이미 조원
                        return round(num, 2)
                except ValueError:
                    pass
        return None

    today_rows = _fetch(today_date)
    if not today_rows:
        raise ValueError("output 없음")

    amount = _parse_jo(today_rows)
    if amount is None:
        raise ValueError(f"금액 파싱 실패, 첫행: {today_rows[0]}")

    chg = None
    if prev_date:
        try:
            prev_rows = _fetch(prev_date)
            prev_amount = _parse_jo(prev_rows)
            if prev_amount is not None:
                chg = round(amount - prev_amount, 2)
        except Exception:
            pass

    return {"amount": amount, "change": chg}


def get_deposit() -> dict:
    """고객예탁금 (투자자예탁금) — 조원 단위 반환
    네이버 금융 우선, KRX API 폴백"""
    try:
        result = _deposit_naver()
        print(f"✅ 고객예탁금: {result['amount']:.2f}조 (Naver)")
        return result
    except Exception as e:
        print(f"[예탁금 Naver] 오류: {e}")

    try:
        result = _deposit_krx()
        print(f"✅ 고객예탁금: {result['amount']:.2f}조 (KRX)")
        return result
    except Exception as e:
        print(f"[예탁금 KRX] 오류: {e}")

    return {"amount": None, "change": None}


# ── 미국 지수 ──────────────────────────────────────────────────────────────

def get_us_indices() -> dict:
    symbols = {"DOW": "^DJI", "NASDAQ": "^IXIC", "SP500": "^GSPC"}
    results = {}

    for name, sym in symbols.items():
        try:
            url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
                   f"?interval=1d&range=5d")
            resp = requests.get(url, headers=_HEADERS, timeout=10)
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
            pct = chg / prev * 100
            results[name] = {"name": name, "close": round(curr, 2),
                             "change": round(chg, 2), "pct": round(pct, 2)}
            print(f"✅ {name}: {results[name]['close']}")
        except Exception as e:
            print(f"[Yahoo {name}] 오류: {e}")
            results[name] = {"name": name, "close": 0, "change": 0, "pct": 0}

    return results


# ── 뉴스 ───────────────────────────────────────────────────────────────────

NEWS_RSS = [
    "https://www.hankyung.com/feed/all-news",
    "https://www.mk.co.kr/rss/30000001/",
]


def get_market_news() -> list:
    for url in NEWS_RSS:
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=8)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            news = []
            for item in root.findall(".//item")[:5]:
                title = item.findtext("title", "").strip()
                link  = item.findtext("link", "").strip()
                if title:
                    news.append({"title": title, "link": link})
            if news:
                print(f"✅ 뉴스 {len(news)}건 ({url.split('/')[2]})")
                return news
        except Exception as e:
            print(f"[뉴스 {url.split('/')[2]}] 오류: {e}")
    return []


# ── 전체 수집 ──────────────────────────────────────────────────────────────

def collect_all() -> dict:
    print("📡 데이터 수집 시작...")

    print("📊 국내 지수 수집 중...")
    kr_data = get_krx_indices()

    print("📈 SOX 지수 수집 중...")
    kr_data["SOX"] = get_sox_index()

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

    return {
        "date":      datetime.now(KST).strftime("%Y년 %m월 %d일"),
        "kr":        kr_data,
        "us":        us_data,
        "sectors":   sectors,
        "investors": investors,
        "bond":      bond,
        "deposit":   get_deposit(),
        "news":      news,
    }
