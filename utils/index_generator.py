"""
utils/index_generator.py
data/archive/ 폴더의 모든 JSON 파일을 인덱싱해서 INDEX.md 자동 생성
"""
import os
import json
from pathlib import Path
from datetime import datetime
import pytz

KST = pytz.timezone("Asia/Seoul")


def generate_index_markdown():
    """
    data/archive/의 모든 JSON을 읽어서
    INDEX.md로 자동 생성
    """
    archive_dir = Path("data/archive")
    analysis_dir = Path("data/analysis")
    html_dir = Path("data/html")
    
    # 파일 목록 조회 (최신순)
    json_files = sorted(archive_dir.glob("*.json"), reverse=True)
    
    if not json_files:
        print("❌ 아카이브 파일이 없습니다.")
        return False
    
    # Markdown 생성
    md = """# 📅 MarketView Daily Report Archive

> 매일 오전 6시에 자동으로 생성되는 시황 분석 리포트의 아카이브입니다.

---

## 📊 최신 30일 리포트

| 날짜 | 요일 | 리포트 | 분석 | 데이터 |
|------|------|--------|------|--------|
"""
    
    for json_file in json_files[:30]:  # 최근 30일
        date_str = json_file.stem  # "2026-05-20"
        
        # 날짜에서 요일 계산
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            weekdays = ["월", "화", "수", "목", "금", "토", "일"]
            day_name = weekdays[dt.weekday()]
        except:
            day_name = "?"
        
        # 파일 크기로 존재 여부 확인
        has_html = (html_dir / f"{date_str}.html").exists()
        has_analysis = (analysis_dir / f"{date_str}.json").exists()
        has_data = json_file.exists()
        
        # 링크 생성
        html_link = f"[📄 보기](data/html/{date_str}.html)" if has_html else "❌"
        analysis_link = f"[📈 분석](data/analysis/{date_str}.json)" if has_analysis else "❌"
        data_link = f"[📊 데이터](data/archive/{date_str}.json)" if has_data else "❌"
        
        # 마크다운에 추가
        md += f"| {date_str} | {day_name} | {html_link} | {analysis_link} | {data_link} |\n"
    
    # 추가 정보
    md += f"""
---

## 📈 통계

- **총 리포트 수**: {len(json_files)}개
- **최신 업데이트**: {json_files[0].stem}
- **저장 위치**: 
  - 원본 데이터: `data/archive/`
  - 분석 결과: `data/analysis/`
  - HTML 이메일: `data/html/`

---

## 🔍 특정 날짜의 리포트 찾기

### 최근 주간 (지난 7일)
"""
    
    for json_file in json_files[:7]:
        date_str = json_file.stem
        md += f"- [{date_str}](data/archive/{date_str}.json)\n"
    
    md += f"""

### 이전 주간 (8-14일 전)
"""
    
    for json_file in json_files[7:14]:
        date_str = json_file.stem
        md += f"- [{date_str}](data/archive/{date_str}.json)\n"
    
    md += """

---

## 📚 이용 안내

### 리포트 보기
1. 위 표에서 원하는 날짜의 **[📄 보기]** 링크 클릭
2. HTML 이메일 형식으로 브라우저에서 확인

### 데이터 다운로드
1. **[📊 데이터]** 링크를 클릭하면 JSON 파일 확인
2. Python/JavaScript에서 파싱해서 활용 가능

### 분석 결과 확인
1. **[📈 분석]** 링크를 클릭하면 Claude AI의 분석 결과 (JSON)
2. 시황 요약 + 핵심 이슈 4개 포함

---

## 💾 데이터 구조

### archive/ - 원본 데이터
```json
{
  "date": "2026년 05월 20일",
  "kr": {
    "KOSPI": {"close": 2875.95, "change": 25.50, "pct": 0.90},
    "KOSDAQ": {...},
    "KRX300": {...}
  },
  "us": {
    "DOW": {...},
    "NASDAQ": {...},
    "SP500": {...}
  },
  "sectors": [...],
  "investors": {...},
  "bond": {...},
  "deposit": {...},
  "news": [...]
}
```

### analysis/ - AI 분석 결과
```json
{
  "summary": "200자 핵심 시황 총평",
  "issues": [
    {
      "badge": "충격|주의|변수|주목|참고",
      "color": "red|blue|gold",
      "title": "뉴스 제목",
      "text": "분석 내용"
    },
    ...
  ]
}
```

---

## 🔗 빠른 링크

- [최신 리포트](data/html/) - 오늘의 이메일 리포트
- [데이터 아카이브](data/archive/) - 모든 원본 데이터
- [분석 결과](data/analysis/) - AI 분석 기록
- [GitHub Repository](https://github.com/ohyoungphil70-art/marketview-report) - 코드 저장소

---

## 📞 기술 정보

- **자동 생성**: GitHub Actions (매일 6시)
- **데이터 출처**: KRX, Yahoo Finance, Naver Finance
- **AI 분석**: Claude API (Anthropic)
- **업데이트 주기**: 매일 1회 (평일/주말 구분)

마지막 인덱스 갱신: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')}
"""
    
    # INDEX.md 저장
    try:
        with open("INDEX.md", "w", encoding="utf-8") as f:
            f.write(md)
        print(f"✅ INDEX.md 생성 완료 ({len(json_files)}개 파일)")
        return True
    except Exception as e:
        print(f"❌ INDEX.md 생성 실패: {e}")
        return False


def generate_summary_for_month(year: int, month: int):
    """
    특정 월의 모든 리포트를 정리해서
    reports/{year}-{month:02d}.md 생성
    """
    archive_dir = Path("data/archive")
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # 해당 월의 파일 조회
    target_files = sorted([
        f for f in archive_dir.glob(f"{year}-{month:02d}-*.json")
    ])
    
    if not target_files:
        print(f"❌ {year}년 {month}월 리포트가 없습니다.")
        return False
    
    md = f"""# {year}년 {month}월 MarketView 시황 분석

> 당신의 18년 경력으로 본 {month}월 시장 분석

---

## 📊 {month}월 요약

**분석 기간**: {target_files[0].stem} ~ {target_files[-1].stem}  
**분석 건수**: {len(target_files)}개 (거래일 기준)

---

## 📅 일별 시황

"""
    
    for json_file in sorted(target_files):
        date_str = json_file.stem
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            kr = data.get("kr", {})
            kospi = kr.get("KOSPI", {})
            
            md += f"""
### {date_str}

**지수**
- KOSPI: {kospi.get('close', 0):,.2f} ({kospi.get('pct', 0):+.2f}%)
- KOSDAQ: {kr.get('KOSDAQ', {}).get('close', 0):,.2f} ({kr.get('KOSDAQ', {}).get('pct', 0):+.2f}%)

**투자자 수급**
- 외국인: {data.get('investors', {}).get('외국인', 0):+,}억
- 기관: {data.get('investors', {}).get('기관', 0):+,}억
- 개인: {data.get('investors', {}).get('개인', 0):+,}억

**링크**: [상세 리포트](../data/html/{date_str}.html) | [데이터](../data/archive/{date_str}.json) | [분석](../data/analysis/{date_str}.json)

---
"""
        except Exception as e:
            print(f"⚠️ {date_str} 처리 실패: {e}")
            continue
    
    # reports 파일 저장
    try:
        report_file = reports_dir / f"{year}-{month:02d}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"✅ {year}년 {month}월 요약 생성: {report_file}")
        return True
    except Exception as e:
        print(f"❌ 월간 요약 생성 실패: {e}")
        return False


if __name__ == "__main__":
    # INDEX.md 생성
    generate_index_markdown()
    
    # 현재 월의 요약 생성
    now = datetime.now(KST)
    generate_summary_for_month(now.year, now.month)
    
    # 이전 월 요약도 생성 (월 초일 때)
    if now.day == 1:
        prev_month = now.month - 1
        prev_year = now.year if prev_month > 0 else now.year - 1
        if prev_month < 1:
            prev_month = 12
        generate_summary_for_month(prev_year, prev_month)
