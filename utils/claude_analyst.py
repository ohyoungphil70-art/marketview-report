
"""
marketview/utils/claude_analyst.py
Claude API를 사용한 시황 분석 모듈
"""
import os
import json
from anthropic import Anthropic

client = Anthropic()

def analyze_market(data: dict) -> dict:
    """시장 데이터를 분석하고 투자 인사이트 생성"""
    print("🤖 Claude AI 분석 시작...")
    
    try:
        market_summary = f"""
=== 시장 데이터 요약 ===
날짜: {data.get('date', '')}

[국내 지수]
- KOSPI: {data['kr']['KOSPI']['close']:.2f} ({data['kr']['KOSPI']['pct']:+.2f}%)
- KOSDAQ: {data['kr']['KOSDAQ']['close']:.2f} ({data['kr']['KOSDAQ']['pct']:+.2f}%)
- KRX300: {data['kr']['KRX300']['close']:.2f} ({data['kr']['KRX300']['pct']:+.2f}%)

[미국 지수]
- DOW JONES: {data['us']['DOW']['close']:.2f} ({data['us']['DOW']['pct']:+.2f}%)
- NASDAQ: {data['us']['NASDAQ']['close']:.2f} ({data['us']['NASDAQ']['pct']:+.2f}%)
- S&P 500: {data['us']['SP500']['close']:.2f} ({data['us']['SP500']['pct']:+.2f}%)

[업종별 등락률 (상위 3)]
"""
        for i, sector in enumerate(data.get('sectors', [])[:3]):
            market_summary += f"- {sector['name']}: {sector['pct']:+.2f}%\n"
        
        market_summary += f"""
[투자자 수급]
- 외국인: {data['investors'].get('외국인', 0):+,}억
- 기관: {data['investors'].get('기관', 0):+,}억
- 개인: {data['investors'].get('개인', 0):+,}억

[시장 지표]
- 국채 3년 금리: {data['bond'].get('rate', 0):.2f}%
- 투자자예탁금: {data['deposit'].get('amount', 0):.1f}조
"""
        
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"""당신은 18년 경력의 증권사 시황 분석가입니다.

다음 시장 데이터를 분석하고 전문적인 인사이트를 제공해주세요.

{market_summary}

다음 형식으로 답변해주세요:

1. 오늘의 시장 요약 (2-3문장)
2. 주목할 점 3가지 (각 1-2문장)

JSON 형식으로 답변해주세요:
{{
    "summary": "시장 요약 텍스트",
    "issues": [
        {{"badge": "주목", "color": "gold", "title": "이슈 제목", "text": "설명"}},
        {{"badge": "주목", "color": "gold", "title": "이슈 제목", "text": "설명"}},
        {{"badge": "주목", "color": "gold", "title": "이슈 제목", "text": "설명"}}
    ]
}}
"""
                }
            ]
        )
        
        response_text = message.content[0].text
        
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
            else:
                result = {
                    "summary": response_text[:200],
                    "issues": [
                        {"badge": "참고", "color": "gold", "title": "시장 분석", "text": response_text[:100]}
                    ]
                }
        except json.JSONDecodeError:
            result = {
                "summary": response_text[:200],
                "issues": [
                    {"badge": "참고", "color": "gold", "title": "시장 분석", "text": response_text[:100]}
                ]
            }
        
        print("✅ Claude 분석 완료")
        return result
        
    except Exception as e:
        print(f"❌ 분석 실패: {e}")
        return {
            "summary": "시장 분석 데이터를 수집 중입니다.",
            "issues": [
                {"badge": "참고", "color": "gold", "title": "시장 모니터링", "text": "실시간 데이터를 분석 중입니다."}
            ]
        }
