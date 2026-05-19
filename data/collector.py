"""
marketview/data/collector.py
시황 데이터 수집 모듈
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

load_dotenv()

KST = pytz.timezone("Asia/Seoul")

# KOSPI 업종 인덱스 티커 (KRX 공식 분류)
KOSPI_SECTORS = [
    ("전기전자", "1011"),   # 삼성전자, SK하이닉스 포함
    ("화학",    "1006"),
    ("의약품",  "1007"),   # 바이오 포함
    ("운수장비","1013"),   # 자동차 포함
    ("금융업",  "1019"),
    ("건설업",  "1016"),
    ("철강금속","1009"),
    ("통신업",  "1018"),
]


def _date_range(days: int = 10):
    today = datetime.now(KST)
    return (today - timedelta(days=days)).strftime("%Y%m%d"), today.strftime("%Y%m%d")


def _find_col(df, keywords: list):
    """DataFrame에서 keywords를 모두 포함하는 첫 번째 컬럼명 반환"""
    for col in df.columns:
        if all(k in str(col) for k in keywords):
            return col
    return None


def get_krx_indices() -> dict:
    """국내 지수 — pykrx 실제 데이터"""
    try:
        from pykrx import stock
        fromdate, todate = _date_range(14)
        indices = {"KOSPI": "1001", "KOSDAQ": "2001", "KRX300": "5042"}
        result = {}

        for name, ticker in indices.items():
            try:
                df = stock.get_index_ohlcv_by_date(fromdate, todate, ticker)
                if df is None or df.empty or len(df) < 2:
                    raise ValueError("데이터 없음")
                close = float(df["종가"].iloc[-1])
                prev  = float(df["종가"].iloc[-2])
                chg   = close - prev
                pct   = (chg / prev) * 100
                result[name] = {
                    "name": name,
                    "close": round(close, 2),
                    "change": round(chg, 2),
                    "pct":   round(pct, 2),
                }
                print(f"✅ {name}: {result[name]['close']}")
            except Exception as e:
                print(f"[KRX {name}] 오류: {e}")
                result[name] = {"name": name, "close": 0, "change": 0, "pct": 0}

        return result

    except ImportError:
        print("[KRX] pykrx 미설치 — requirements.txt를 확인하세요")
    except Exception as e:
        print(f"[KRX] 오류: {e}")

    return {k: {"name": k, "close": 0, "change": 0, "pct": 0}
            for k in ("KOSPI", "KOSDAQ", "KRX300")}


def get_sector_data() -> list:
    """KOSPI 업종별 등락률 — pykrx 업종 인덱스"""
    try:
        from pykrx import stock
        fromdate, todate = _date_range(14)
        sectors = []

        for display_name, ticker in KOSPI_SECTORS:
            try:
                df = stock.get_index_ohlcv_by_date(fromdate, todate, ticker)
                if df is None or df.empty or len(df) < 2:
                    continue
                close = float(df["종가"].iloc[-1])
                prev  = float(df["종가"].iloc[-2])
                pct   = ((close - prev) / prev) * 100
                sectors.append({"name": display_name, "pct": round(pct, 2)})
            except Exception as e:
                print(f"[섹터 {display_name}] 오류: {e}")

        return sorted(sectors, key=lambda x: x["pct"], reverse=True)

    except Exception as e:
        print(f"[섹터] 오류: {e}")
        return []


def get_investor_data() -> dict:
    """투자자 순매수 (KOSPI, 억원) — pykrx"""
    try:
        from pykrx import stock
        fromdate, todate = _date_range(7)

        # 가장 최근 거래일 확인
        idx_df = stock.get_index_ohlcv_by_date(fromdate, todate, "1001")
        if idx_df is None or idx_df.empty:
            raise ValueError("거래일 확인 실패")
        last_date = idx_df.index[-1].strftime("%Y%m%d")

        inv_keys = {
            "외국인": "외국인합계",
            "기관":   "기관합계",
            "개인":   "개인",
        }
        result = {}

        for label, investor in inv_keys.items():
            try:
                df = stock.get_market_net_purchases_of_equities_by_ticker(
                    last_date, market="KOSPI", investor=investor
                )
                if df is None or df.empty:
                    result[label] = 0
                    continue
                # pykrx 버전별 컬럼명 차이 대응
                col = (_find_col(df, ["순매수거래대금"])
                       or _find_col(df, ["순매수", "대금"])
                       or _find_col(df, ["순매수"]))
                if col is None:
                    num_cols = df.select_dtypes("number").columns
                    col = num_cols[-1] if len(num_cols) else None
                if col is None:
                    result[label] = 0
                    continue
                total = int(df[col].sum() / 1e8)   # 억 단위
                result[label] = total
                print(f"✅ {label} 순매수: {total:+,}억")
            except Exception as e:
                print(f"[투자자 {label}] 오류: {e}")
                result[label] = 0

        return result

    except Exception as e:
        print(f"[투자자] 오류: {e}")
        return {"외국인": 0, "기관": 0, "개인": 0}


def get_bond_rate() -> dict:
    """국채 3년 금리 — pykrx bond"""
    try:
        from pykrx import bond as krx_bond
        fromdate, todate = _date_range(14)
        df = krx_bond.get_otc_treasury_yields(fromdate, todate)

        if df is None or df.empty:
            raise ValueError("데이터 없음")

        # 컬럼명이 '국고채3년' 또는 '국고채 3년' 등으로 다를 수 있음
        col = _find_col(df, ["3"]) or _find_col(df, ["3년"])
        if col is None:
            raise ValueError(f"3년 컬럼 없음 ({list(df.columns)})")

        rate = float(df[col].iloc[-1])
        prev = float(df[col].iloc[-2]) if len(df) >= 2 else rate
        return {"rate": round(rate, 2), "change": round(rate - prev, 3)}

    except Exception as e:
        print(f"[국채] 오류: {e}")
        return {"rate": 0, "change": 0}


def get_deposit() -> dict:
    """투자자예탁금 — 무료 공개 API 없음, 미제공"""
    return {"amount": None}


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
                raise ValueError("전일 종가 0 — 계산 불가")
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


def get_market_news() -> list:
    """주요 뉴스 — 네이버 금융 RSS"""
    try:
        url = "https://finance.naver.com/news/rss.naver?category=marketGlobal"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        news = []
        for item in root.findall(".//item")[:5]:
            title = item.findtext("title", "").strip()
            link  = item.findtext("link", "").strip()
            if title:
                news.append({"title": title, "link": link})
        return news
    except Exception as e:
        print(f"[뉴스] 오류: {e}")
        return []


def collect_all() -> dict:
    """전체 시장 데이터 수집"""
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
