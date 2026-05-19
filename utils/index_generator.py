"""
marketview/utils/index_generator.py
보고서 INDEX.md 및 월간 요약 생성기
"""
import os
import json
from datetime import datetime
import pytz

KST = pytz.timezone("Asia/Seoul")


def generate_index():
    """data/archive/*.json 기반으로 INDEX.md 생성"""
    archive_dir = "data/archive"
    html_dir    = "data/html"

    if not os.path.exists(archive_dir):
        print("[인덱스] data/archive 디렉토리 없음")
        return

    files = sorted(
        [f for f in os.listdir(archive_dir) if f.endswith(".json")],
        reverse=True
    )

    now_str = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    lines = [
        "# MarketView Daily Reports\n\n",
        f"_최종 업데이트: {now_str}_\n\n",
        "| 날짜 | HTML | JSON |\n",
        "|------|:----:|:----:|\n",
    ]

    for f in files[:60]:
        date = f.replace(".json", "")
        html_path = f"{html_dir}/{date}.html"
        json_path = f"{archive_dir}/{date}.json"
        html_cell = f"[📄 HTML]({html_path})" if os.path.exists(html_path) else "—"
        lines.append(f"| {date} | {html_cell} | [📊 JSON]({json_path}) |\n")

    with open("INDEX.md", "w", encoding="utf-8") as fh:
        fh.writelines(lines)

    print(f"✅ INDEX.md 생성 완료 ({len(files)}건)")


def generate_summary_for_month(year: int, month: int):
    """월별 요약 — data/archive에서 해당 월 데이터를 읽어 요약 출력"""
    archive_dir = "data/archive"
    if not os.path.exists(archive_dir):
        return

    month_prefix = f"{year}-{month:02d}"
    files = sorted(
        [f for f in os.listdir(archive_dir)
         if f.startswith(month_prefix) and f.endswith(".json")]
    )

    if not files:
        print(f"[{month_prefix}] 데이터 없음")
        return

    kospi_closes = []
    for f in files:
        try:
            with open(os.path.join(archive_dir, f), encoding="utf-8") as fh:
                d = json.load(fh)
            close = d.get("kr", {}).get("KOSPI", {}).get("close", 0)
            if close:
                kospi_closes.append(close)
        except Exception:
            continue

    summary_path = f"reports/{month_prefix}-summary.md"
    os.makedirs("reports", exist_ok=True)

    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write(f"# {year}년 {month}월 시황 요약\n\n")
        fh.write(f"- 거래일 수: {len(files)}일\n")
        if kospi_closes and kospi_closes[0] != 0:
            fh.write(f"- KOSPI 월초: {kospi_closes[0]:,.2f}\n")
            fh.write(f"- KOSPI 월말: {kospi_closes[-1]:,.2f}\n")
            monthly_ret = (kospi_closes[-1] / kospi_closes[0] - 1) * 100
            fh.write(f"- 월간 수익률: {monthly_ret:+.2f}%\n")

    print(f"✅ {month_prefix} 월간 요약 생성: {summary_path}")


if __name__ == "__main__":
    generate_index()
