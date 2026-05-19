"""
marketview/utils/claude_analyst.py
Claude API를 사용한 시황 분석 모듈
"""
import json
import os
from dotenv import load_dotenv

load_dotenv()


def _build_prompt(data: dict) -> str:
    kr  = data.get("kr", {})
    us  = data.get("us", {})
    inv = data.get("investors", {})
    bond = data.get("bond", {})
    dep  = data.get("deposit", {})

    # 업종 전체
    sectors_lines = "\n".join(
        f"  - {s['name']}: {s['pct']:+.2f}%"
        for s in data.get("sectors", [])
    ) or "  (데이터 없음)"

    # 뉴스 상위 5건
    news_lines = "\n".join(
        f"  {i+1}. {n['title']}"
        for i, n in enumerate(data.get("news", [])[:5])
    ) or "  (뉴스 없음)"

    bond_rate   = bond.get("rate") or 0
    bond_change = bond.get("change") or 0
    dep_note    = f"{dep['amount']:.1f}조" if dep.get("amount") else "미제공"

    return f"""당신은 18년 경력의 국내 증권사 수석 시황 분석가입니다.
아래 시장 데이터를 바탕으로 전문적이고 심층적인 시황 분석을 작성하세요.

━━ 시장 데이터 ({data.get('date', '')}) ━━

[국내 지수]
  - KOSPI  : {kr.get('KOSPI',  {}).get('close', 0):,.2f}  ({kr.get('KOSPI',  {}).get('pct', 0):+.2f}%,  전일比 {kr.get('KOSPI',  {}).get('change', 0):+.2f}pt)
  - KOSDAQ : {kr.get('KOSDAQ', {}).get('close', 0):,.2f}  ({kr.get('KOSDAQ', {}).get('pct', 0):+.2f}%,  전일比 {kr.get('KOSDAQ', {}).get('change', 0):+.2f}pt)
  - KRX300 : {kr.get('KRX300', {}).get('close', 0):,.2f}  ({kr.get('KRX300', {}).get('pct', 0):+.2f}%)

[미국 3대 지수 (전일 종가)]
  - 다우존스 : {us.get('DOW',    {}).get('close', 0):>10,.2f}  ({us.get('DOW',    {}).get('pct', 0):+.2f}%)
  - 나스닥   : {us.get('NASDAQ', {}).get('close', 0):>10,.2f}  ({us.get('NASDAQ', {}).get('pct', 0):+.2f}%)
  - S&P 500  : {us.get('SP500',  {}).get('close', 0):>10,.2f}  ({us.get('SP500',  {}).get('pct', 0):+.2f}%)

[투자자 순매수 — KOSPI 기준, 억원]
  - 외국인 : {inv.get('외국인', 0):+,}억
  - 기관   : {inv.get('기관',   0):+,}억
  - 개인   : {inv.get('개인',   0):+,}억

[시장 지표]
  - 국채 3년 금리 : {bond_rate:.2f}%  (전일比 {bond_change:+.3f}%p)
  - 투자자예탁금  : {dep_note}

[KOSPI 업종별 등락률]
{sectors_lines}

[오늘의 주요 뉴스]
{news_lines}

━━ 분석 지침 ━━
- 수치 간 상관관계를 파악해 종합적으로 해석하세요
  (예: 외국인 순매도 + 원화 약세 + 미 국채 금리 상승의 연관성)
- 단순 수치 나열이 아닌 배경과 의미를 설명하세요
- 투자자 관점에서 실질적 인사이트를 포함하세요
- 뉴스 헤드라인이 시장에 미친 영향을 언급하세요

━━ 출력 형식 (순수 JSON만, 코드 블록 없이) ━━
{{
  "summary": "오늘 시장 전반 요약 — 핵심 흐름·원인 분석 포함, 4~5문장",
  "issues": [
    {{
      "badge": "충격|주의|주목|변수",
      "color": "red|blue|gold",
      "title": "이슈 제목 (15자 이내)",
      "text":  "상세 설명 — 구체적 수치 포함, 2~3문장"
    }}
  ]
}}

badge 기준: 충격(±2% 이상 급변동), 주의(리스크 요인), 주목(핵심 트렌드), 변수(불확실성)
color 기준: red(부정/하락 우려), blue(중립/관망), gold(주목/기회)
issues 개수: 시장 상황에 따라 3~5개로 가변 구성
"""


def _parse_json(text: str) -> dict:
    text = text.strip()
    # ```json ... ``` 블록 제거
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:]
        )
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
        raise


def analyze_market(data: dict) -> dict:
    """시장 데이터를 분석하고 투자 인사이트 생성"""
    print("🤖 Claude AI 분석 시작...")

    try:
        from anthropic import Anthropic
        client = Anthropic()   # 함수 내부에서 초기화 → import 시 크래시 방지

        message = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=2500,
            messages=[{"role": "user", "content": _build_prompt(data)}],
        )

        result = _parse_json(message.content[0].text)
        print("✅ Claude 분석 완료")
        return result

    except Exception as e:
        print(f"❌ 분석 실패: {e}")
        return {
            "summary": f"시장 분석 중 오류가 발생했습니다. ({type(e).__name__})",
            "issues": [
                {
                    "badge": "참고",
                    "color": "gold",
                    "title": "시스템 알림",
                    "text":  f"분석 오류: {str(e)[:120]}",
                }
            ],
        }
