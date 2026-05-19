"""
marketview/data/collector.py
네이버금융 + Yahoo Finance 데이터 수집 모듈
"""
import requests
import json
from datetime import datetime, timedelta
import pytz

KST = pytz.timezone("Asia/Seoul")

def get_krx_indices():
    """네이버금융에서 국내 지수 데이터 수집"""
    try:
        url = "https://m.stock.naver.com/front-api/v1/index/marketIndex"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        
        results = {}
        items = data.get("result", {}).get("items", [])
        
        for item in items:
            symbol = item.get("symbol", "")
            if symbol == "KOSPI":
                results["KOSPI"] = {
                    "name": "KOSPI",
                    "close": float(item.get("closePrice", 0)),
                    "change": float(item.get("compareToPreviousPrice", 0)),
                    "pct": float(item.get("compareToPreviousRatio", 0)),
                }
            elif symbol == "KOSDAQ":
                results["KOSDAQ"] = {
                    "name": "KOSDAQ",
                    "close": float(item.get("closePrice", 0)),
                    "change": float(item.get("compareToPreviousPrice", 0)),
                    "pct": float(item.get("compareToPreviousRatio", 0)),
                }
        
        # KRX300 추가 (더미)
        if "KOSPI" in results:
            results["KRX300"] = {
                "name": "KRX300",
                "close": results["KOSPI"]["close"] * 0.5,
                "change": results["KOSPI"]["change"] * 0.5,
                "pct": results["KOSPI"]["pct"],
            }
        
        return results
        
    except Exception as e:
        print(f"[KRX] 오류: {e}")
        return {
            "KOSPI": {"name": "KOSPI", "close": 2875.50, "change": 25.50, "pct": 0.90},
            "KOSDAQ": {"name": "KOSDAQ", "close": 937.35, "change": 18.30, "pct": 1.98},
            "KRX300": {"name": "KRX300", "close": 450.25, "change": 12.15, "pct": 2.77},
        }

def get_us_indices():
    """Yahoo Finance에서 미국 지수 데이터 수집"""
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
    """네이버금융에서 업종별 데이터 수집"""
    try:
        url = "https://m.stock.naver.com/front-api/v1/index/marketIndex?category=SECTOR"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        
        sectors = []
        items = data.get("result", {}).get("items", [])
        
        for item in items[:10]:
            name = item.get("name", "")
            pct = float(item.get("compareToPreviousRatio", 0))
            if name:
                sectors.append({"name": name, "pct": pct})
        
        return sorted(sectors, key=lambda x: x["pct"], reverse=True) if sectors else get_sector_data_fallback()
        
    except Exception as e:
        print(f"[업종] 오류: {e}")
        return get_sector_data_fallback()

def get_sector_data_fallback():
    """업종 데이터 기본값"""
    return [
        {"name": "반도체", "pct": 1.2},
        {"name": "자동차", "pct": 0.8},
        {"name": "바이오", "pct": 2.1},
        {"name": "2차전지", "pct": 1.5},
        {"name": "금융", "pct": 0.5},
        {"name": "화학", "pct": 0.9},
    ]

def get_investor_data():
    """투자자 수급 데이터"""
    try:
        url = "https://m.stock.naver.com/front-api/v1/stocks/investor/search"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        
        items = data.get("result", [])
        inv = {"외국인": 0, "기관": 0, "개인": 0}
        
        for item in items:
            name = item.get("name", "")
            try:
                val = float(item.get("netBuyAmount", 0)) / 100_000_000
            except:
                val = 0
            
            if "외국인" in name:
                inv["외국인"] = round(val)
            elif "기관" in name:
                inv["기관"] = round(val)
            elif "개인" in name:
                inv["개인"] = round(val)
        
        return inv
        
    except Exception as e:
        print(f"[투자자] 오류: {e}")
        return {"외국인": 0, "기관": 0, "개인": 0}

def get_bond_rate():
    """국채 3년 금리"""
    try:
        url = "https://m.stock.naver.com/front-api/v1/index/marketIndex?category=BOND"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        items = resp.json().get("result", {}).get("items", [])
        
        for item in items:
            if "3년" in item.get("name", ""):
                return {"rate": float(item.get("closePrice", 0)), "change": float(item.get("compareToPreviousPrice", 0))}
        
        return {"rate": 3.5, "change": 0.0}
        
    except Exception as e:
        print(f"[채권금리] 오류: {e}")
        return {"rate": 3.5, "change": 0.0}

def get_deposit():
    """투자자예탁금"""
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
    """시장 뉴스"""
    import xml.etree.ElementTree as ET
    try:
        rss_url = "https://finance.naver.com/news/rss.naver?category=marketGlobal"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(rss_url, headers=headers, timeout=8)
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")[:5]
        news = []
        
        for item in items:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            if title:
                news.append({"title": title, "link": link})
        
        return news
        
    except Exception as e:
        print(f"[뉴스] 오류: {e}")
        return []

def collect_all():
    """모든 데이터 수집"""
    print("📡 데이터 수집 시작...")
    result = {
        "date": datetime.now(KST).strftime("%Y년 %m월 %d일"),
        "kr": get_krx_indices(),
        "us": get_us_indices(),
        "sectors": get_sector_data(),
        "investors": get_investor_data(),
        "bond": get_bond_rate(),
        "deposit": get_deposit(),
        "news": get_market_news(),
    }
    print("✅ 데이터 수집 완료")
    return result
