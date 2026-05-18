"""
marketview/main.py
메인 실행 파일 — 데이터 수집 → 분석 → HTML 생성 → 이메일 발송
"""
import sys
import os
import traceback
from datetime import datetime
import pytz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.collector       import collect_all
from utils.claude_analyst import generate_comment
from utils.templates.email_html import build_email_html
from utils.mailer         import send_email

KST = pytz.timezone("Asia/Seoul")


def run():
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    print(f"\n{'='*50}")
    print(f"  MarketView Daily Report 시작: {now}")
    print(f"{'='*50}\n")

    try:
        print("▶ Step 1: 시장 데이터 수집")
        data = collect_all()

        print("▶ Step 2: Claude AI 시황 분석")
        analysis = generate_comment(data)

        print("▶ Step 3: HTML 이메일 생성")
        html = build_email_html(data, analysis)

        print("▶ Step 4: 이메일 발송")
        success = send_email(html)

        if success:
            print(f"\n✅ 완료! {datetime.now(KST).strftime('%H:%M:%S KST')}")
        else:
            print("\n⚠️ 이메일 발송 실패")
            sys.exit(1)

    except Exception:
        print("\n❌ 오류 발생:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run()
