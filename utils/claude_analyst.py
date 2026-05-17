"""
marketview/utils/claude_analyst.py
Claude API로 시황 코멘트 및 뉴스 분석 생성
"""
import os
import json
import requests


def generate_comment(data: dict) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback_comment()

    kr  = data.get("kr", {})
    us  = data.get("us", {})
    inv = data.get("investors", {})
    bond= data.get("bond", {})
    dep = data.get("deposit", {})
    news= data.get("news", [])
    sec = data.get("sectors", [])

    news_titles = "\n".join([f"- {n['title']}" for n in news[:5]]) or "없음"
    sector_str  = "\n".join([f"- {s['name']}: {s['pct']:+.2f}%" for s in sec[:8]]) or "없음"

    prompt = f"""
오늘 날짜: {data.get('date', '')}

[국내 지수]
- KOSPI:  {kr.get('KOSPI',{}).get('close',0):,.2f}  ({kr.get('KOSPI',{}).get('pct',0):+.2f}%)
- KOSDAQ: {kr.get('KOSDAQ',{}).get('close',0):,.2f} ({kr.get('KOSDAQ',{}).get('pct',0):+.2f}%)
- KRX300: {kr.get('KRX300',{}).get('close',0):,.2f} ({kr.get('KRX300',{}).get('pct',0):+.2f}%)

[미국 지수]
- DOW:    {us.get('DOW',{}).get('close',0):,.2f}  ({us.get('DOW',{}).get('pct',0):+.2f}%)
- NASDAQ: {us.get('NASDAQ',{}).get('close',0):,.2f} ({us.get('NASDAQ',{}).get('pct',0):+.2f}%)
- S&P500: {us.get('SP500',{}).get('close',0):,.2f}  ({us.get('SP500',{}).get('pct',0):+.2f}%)

[투자자 순매수 (억원)]
- 외국인: {inv.get('외국인',0):+,}억
- 기관:   {inv.get('기관',0):+,}억
- 개인:   {inv.get('개인',0):+,}억

[국채 3년 금리]
- {bond.get('rate',0):.2f}%

[업종별 등락]
{sector_str}

[오늘의 뉴스]
{news_titles}

위 데이터를 바탕으로 18년 경력 증권사 부장 관점에서 아래 JSON 형식으로 분석해주세요.
반드시 JSON만 출력하고 다른 말은 하지 마세요.

{{
  "summary": "200자 이내 핵심 시황 총평",
  "issues": [
    {{
      "badge": "충격|주의|변수|주목|참고 중 하나",
      "color": "red|blue|gold 중 하나",
      "title": "뉴스 제목 30자 이내",
      "text": "분석 내용 100자 이내"
    }}
  ]
}}

issues는 3~4개 작성.
"""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        text = resp.json()["content"][0]["text"].strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as e:
        print(f"[Claude API] 오류: {e}")
        return _fallback_comment()


def _fallback_comment():
    return {
        "summary": "시황 데이터를 불러오는 중 오류가 발생했습니다.",
        "issues": [
            {
                "badge": "참고",
                "color": "gold",
                "title": "데이터 수집 오류",
                "text": "API 연결 실패. 잠시 후 재시도하세요."
            }
        ]
    }
