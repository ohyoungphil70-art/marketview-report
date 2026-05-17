"""
marketview/data/collector.py
KRX API + 네이버금융 + 뉴스 데이터 수집 모듈
"""
import requests
import json
from datetime import datetime, timedelta
import pytz

KST = pytz.timezone("Asia/Seoul")

def get_krx_indices():
    today = datetime.now(KST)
    wd = today.weekday()
    if wd == 0:
        target = today - timedelta(days=3)
    elif wd == 6:
        target = today - timedelta(days=2)
    else:
        target = today - timedelta(days=1)
    trd_dd = target.strftime("%Y%m%d")
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "http://data.krx.co.kr/",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    index_map = {
        "KOSPI":  {"bld": "dbms/MDC/STAT/standard/MDCSTAT00101", "idxIndCd": "1"},
        "KOSDAQ": {"bld": "dbms/MDC/STAT/standard/MDCSTAT00101", "idxIndCd": "2"},
        "KRX300": {"bld": "dbms/MDC/STAT/standard/MDCSTAT00101", "idxIndCd": "6"},
    }
    results = {}
    for name, cfg in index_map.items():
        try:
            data = {"bld": cfg["bld"], "idxIndCd": cfg["idxIndCd"], "trdDd": trd_dd}
            resp = requests.post(url, headers=headers, data=data, timeout=10)
            j = resp.json()
            row = j.get("output", [{}])[0]
            results[name] = {
                "name":   name,
                "close":  float(row.get("CLSPRC_IDX", "0").replace(",", "")),
                "change": float(row.get("FLUC_PT", "0").replace(",", "")),
                "pct":    float(row.get("FLUC_RT", "0").replace(",", "")),
                "date":   trd_dd,
            }
        except Exception as e:
            print(f"[KRX {name}] 오류: {e}")
            results[name] = {"name": name, "close": 0, "change": 0, "pct": 0, "date": ""}
    return results

def get_us_indices():
    symbols = {"DOW": "^DJI", "NASDAQ": "^IXIC", "SP500": "^GSPC"}
    results = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    for name, sym in symbols.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=2d"
            resp = requests.get(url, headers=headers, timeout=10)
            j = resp.json()
            close_arr = j["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            prev  = close_arr[-2] if len(close_arr) >= 2 else close_arr[-1]
            curr  = close_arr[-1]
            chg   = curr - prev
            pct   = (chg / prev) * 100
            results[name] = {"name": name, "close": round(curr,2), "change": round(chg,2), "pct": round(pct,2)}
        except Exception as e:
            print(f"[Yahoo {name}] 오류: {e}")
            results[name] = {"name": name, "close": 0, "change": 0, "pct": 0}
    return results

def get_sector_data():
    today = datetime.now(KST)
    wd = today.weekday()
    if wd == 0:
        target = today - timedelta(days=3)
    elif wd == 6:
        target = today - timedelta(days=2)
    else:
        target = today - timedelta(days=1)
    trd_dd = target.strftime("%Y%m%d")
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "http://data.krx.co.kr/",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    data = {"bld": "dbms/MDC/STAT/standard/MDCSTAT03901", "trdDd": trd_dd, "idxIndCd": "1", "cptlSizeGbCd": "0"}
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        rows = resp.json().get("output", [])
        sectors = []
        for r in rows[:10]:
            try:
                sectors.append({"name": r.get("IDX_IND_NM",""), "pct": float(r.get("FLUC_RT","0").replace(",",""))})
            except:
                pass
        return sorted(sectors, key=lambda x: x["pct"], reverse=True)
    except Exception as e:
        print(f"[KRX 업종] 오류: {e}")
        return [{"name": "반도체","pct":0},{"name": "자동차","pct":0},{"name": "바이오","pct":0},
                {"name": "2차전지","pct":0},{"name": "금융","pct":0},{"name": "화학","pct":0}]

def get_investor_data():
    today = datetime.now(KST)
    wd = today.weekday()
    if wd == 0:
        target = today - timedelta(days=3)
    elif wd == 6:
        target = today - timedelta(days=2)
    else:
        target = today - timedelta(days=1)
    trd_dd = target.strftime("%Y%m%d")
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "http://data.krx.co.kr/",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    data = {"bld": "dbms/MDC/STAT/standard/MDCSTAT02203", "trdDd": trd_dd, "mktId": "STK"}
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        rows = resp.json().get("output", [])
        inv = {"외국인": 0, "기관": 0, "개인": 0}
        for r in rows:
            nm = r.get("INVST_TP_NM", "")
            try:
                val = float(r.get("NETBUY_TRDVAL","0").replace(",","")) / 100_000_000
            except:
                val = 0
            if "외국인" in nm: inv["외국인"] = round(val)
            elif "기관" in nm: inv["기관"] = round(val)
            elif "개인" in nm: inv["개인"] = round(val)
        return inv
    except Exception as e:
        print(f"[KRX 투자자] 오류: {e}")
        return {"외국인": 0, "기관": 0, "개인": 0}

def get_bond_rate():
    try:
        url = "https://m.stock.naver.com/front-api/v1/index/marketIndex?category=BOND"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=8)
        items = resp.json().get("result", {}).get("items", [])
        for item in items:
            if "3" in item.get("symbol","") and "국고" in item.get("name",""):
                return {"rate": float(item.get("closePrice",0)), "change": float(item.get("compareToPreviousPrice",0))}
        return {"rate": 0.0, "change": 0.0}
    except Exception as e:
        print(f"[채권금리] 오류: {e}")
        return {"rate": 0.0, "change": 0.0}

def get_deposit():
    try:
        api_url = "https://data.kofia.or.kr/api/v1/market/deposit/search.json"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(api_url, headers=headers, timeout=8)
        data = resp.json()
        latest = data.get("result", [{}])[0]
        val = float(latest.get("deposit", 0)) / 10_000
        return {"amount": round(val, 1)}
    except:
        return {"amount": 0.0}

def get_market_news():
    import xml.etree.ElementTree as ET
    try:
        rss_url = "https://finance.naver.com/news/rss.naver?category=marketGlobal"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(rss_url, headers=headers, timeout=8)
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")[:5]
        news = []
        for item in items:
            title = item.findtext("title","").strip()
            link  = item.findtext("link","").strip()
            if title:
                news.append({"title": title, "link": link})
        return news
    except Exception as e:
        print(f"[뉴스] 오류: {e}")
        return []

def collect_all():
    print("📡 데이터 수집 시작...")
    result = {
        "date":      datetime.now(KST).strftime("%Y년 %m월 %d일"),
        "kr":        get_krx_indices(),
        "us":        get_us_indices(),
        "sectors":   get_sector_data(),
        "investors": get_investor_data(),
        "bond":      get_bond_rate(),
        "deposit":   get_deposit(),
        "news":      get_market_news(),
    }
    print("✅ 데이터 수집 완료")
    return result
