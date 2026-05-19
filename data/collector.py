"""
marketview/data/collector.py
시황 데이터 수집 모듈 (더미 데이터)
"""
import requests
import json
from datetime import datetime, timedelta
import pytz
import random

KST = pytz.timezone("Asia/Seoul")

def get_krx_indices():
    """국내 지수 (더미 데이터)"""
    return {
        "KOSPI": {
            "name": "KOSPI",
            "close": round(2875.50 + random.uniform(-50, 50), 2),
            "change": round(random.uniform(-30, 30), 2),
            "pct": round(random.uniform(-1.5, 1.5), 2),
        },
        "KOSDAQ": {
            "name": "KOSDAQ",
            "close": round(937.35 + random.uniform(-30, 30), 2),
            "change": round(random.uniform(-20, 20), 2),
            "pct": round(random.uniform(-2.0, 2.0), 2),
        },
        "KRX300": {
            "name": "KRX300",
            "close": round(450.25 + random.uniform(-20, 20), 2),
            "change": round(random.uniform(-10, 10), 2),
            "pct": round(random.uniform(-1.5, 1.5), 2),
        },
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
    """업종별 등락률 (더미 데이터)"""
    sectors = [
        {"name": "반도체", "pct": round(random.uniform(-2, 3), 2)},
        {"name": "자동차", "pct": round(random.uniform(-1, 2), 2)},
        {"name": "바이오", "pct": round(random.uniform(-2, 4), 2)},
        {"name": "2차전지", "pct": round(random.uniform(-3, 5), 2)},
        {"name": "금융", "pct": round(random.uniform(-1.5, 1.5), 2)},
        {"name": "화학", "pct": round(random.uniform(-1, 2), 2)},
    ]
    return sorted(sectors, key=lambda x: x["pct"], reverse=True)

def get_investor_data():
    """투자자 수급 (더미 데이터)"""
    return {
        "외국인": random.randint(-3000, 3000),
        "기관": random.randint(-2000, 2000),
        "개인": random.randint(-1000, 1000),
    }

def get_bond_rate():
    """국채 3년 금리 (고정값)"""
    return {
        "rate": 3.50,
        "change": 0.0
    }

def get_deposit():
    """투자자예탁금 (고정값)"""
    return {
        "amount": 450.5
    }

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
