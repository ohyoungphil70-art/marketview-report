"""
marketview/main.py
시황 리포트 생성 및 발송 메인 스크립트
"""
import os
import json
import subprocess
from datetime import datetime
import pytz
from dotenv import load_dotenv

load_dotenv()

from data.collector import collect_all
from utils.claude_analyst import analyze_market
from utils.mailer import send_report_email
from utils.templates.email_html import build_email_html

KST = pytz.timezone("Asia/Seoul")


def ensure_directories():
    for d in ["data/archive", "data/analysis", "data/html", "reports", "logs"]:
        os.makedirs(d, exist_ok=True)


def save_json(filename: str, data: dict) -> bool:
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 저장 완료: {filename}")
        return True
    except Exception as e:
        print(f"❌ 저장 실패: {filename} — {e}")
        return False


def save_html(filename: str, html_content: str) -> bool:
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"✅ HTML 저장: {filename}")
        return True
    except Exception as e:
        print(f"❌ HTML 저장 실패: {filename} — {e}")
        return False


def git_auto_commit(commit_msg: str) -> bool:
    """로컬 환경 전용 git 자동 커밋 (GitHub Actions에서는 workflow가 처리)"""
    try:
        subprocess.run(["git", "add", "-A"], check=True, capture_output=True)
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            capture_output=True, text=True
        )
        if result.returncode not in (0, 1):   # 1 = nothing to commit
            raise subprocess.CalledProcessError(result.returncode, "git commit",
                                                stderr=result.stderr)
        if result.returncode == 0:
            subprocess.run(["git", "push"], check=True, capture_output=True)
            print(f"✅ Git 커밋 완료: {commit_msg}")
        else:
            print("ℹ️  커밋할 변경사항 없음")
        return True
    except subprocess.CalledProcessError as e:
        stderr = e.stderr if isinstance(e.stderr, str) else (e.stderr or b"").decode()
        print(f"❌ Git 커밋 실패: {stderr.strip() or str(e)}")
        return False


def main():
    print("=" * 50)
    print("📊 MarketView 시황 리포트 생성 시작")
    print("=" * 50)

    ensure_directories()

    print("\n📡 Step 1: 시장 데이터 수집")
    data = collect_all()

    print("\n🤖 Step 2: Claude AI 분석")
    analysis = analyze_market(data)

    print("\n📧 Step 3: 이메일 발송")
    try:
        send_report_email(data, analysis)
    except Exception as e:
        print(f"❌ 이메일 발송 실패: {e}")

    print("\n💾 Step 4: 데이터 저장")
    today = datetime.now(KST).strftime("%Y-%m-%d")

    save_json(f"data/archive/{today}.json", data)
    save_json(f"data/analysis/{today}.json", analysis)

    html_content = build_email_html(data, analysis)
    save_html(f"data/html/{today}.html", html_content)

    # GitHub Actions 환경에서는 workflow의 git 스텝이 커밋을 처리
    if not os.getenv("GITHUB_ACTIONS"):
        print("\n🔄 Step 5: Git 자동 커밋")
        commit_msg = f"Daily report {today} - {datetime.now(KST).strftime('%H:%M:%S')}"
        git_auto_commit(commit_msg)

    print("\n" + "=" * 50)
    print("✅ 시황 리포트 생성 완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()
