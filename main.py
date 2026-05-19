"""
marketview/main.py (개선 버전)
메인 실행 파일 — 데이터 수집 → 분석 → HTML 생성 → 이메일 발송 → 자동 저장
"""
import sys
import os
import json
import traceback
from datetime import datetime
import pytz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.collector                    import collect_all
from utils.claude_analyst              import generate_comment
from utils.utils.templates.email_html  import build_email_html
from utils.utils.mailer                import send_email

KST = pytz.timezone("Asia/Seoul")

def ensure_directories():
    """필요한 디렉토리 생성"""
    dirs = [
        "data/archive",
        "data/analysis",
        "data/html",
        "logs"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def save_json(data, filepath):
    """JSON 파일 저장"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 저장 완료: {filepath}")
        return True
    except Exception as e:
        print(f"❌ 저장 실패 ({filepath}): {e}")
        return False

def save_html(html_content, filepath):
    """HTML 파일 저장"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ HTML 저장: {filepath}")
        return True
    except Exception as e:
        print(f"❌ HTML 저장 실패: {e}")
        return False

def git_auto_commit(date_str):
    """GitHub에 자동 커밋 (선택사항)"""
    try:
        os.system("git add data/archive data/analysis data/html")
        os.system(f'git commit -m "Daily Update: {date_str}"')
        os.system("git push origin main")
        print("✅ GitHub 커밋 완료")
        return True
    except Exception as e:
        print(f"⚠️ Git 커밋 실패: {e}")
        return False

def run():
    now = datetime.now(KST)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%Y-%m-%d %H:%M KST")
    
    print(f"\n{'='*60}")
    print(f"  MarketView Daily Report 시작: {time_str}")
    print(f"{'='*60}\n")

    # 1. 디렉토리 생성
    ensure_directories()

    try:
        # 2. 데이터 수집
        print("▶ Step 1: 시장 데이터 수집")
        data = collect_all()

        # 2-1. 원본 데이터 저장
        print("▶ Step 1-1: 원본 데이터 저장")
        save_json(data, f"data/archive/{date_str}.json")

        # 3. AI 분석
        print("▶ Step 2: Claude AI 시황 분석")
        analysis = generate_comment(data)

        # 3-1. 분석 결과 저장
        print("▶ Step 2-1: 분석 결과 저장")
        save_json(analysis, f"data/analysis/{date_str}.json")

        # 4. HTML 생성
        print("▶ Step 3: HTML 이메일 생성")
        html = build_email_html(data, analysis)

        # 4-1. HTML 저장
        print("▶ Step 3-1: HTML 파일 저장")
        save_html(html, f"data/html/{date_str}.html")

        # 5. 이메일 발송
        print("▶ Step 4: 이메일 발송")
        success = send_email(html)

        if not success:
            print("\n⚠️ 이메일 발송 실패")
            sys.exit(1)

        # 6. GitHub에 자동 커밋 (선택사항)
        print("▶ Step 5: GitHub 자동 커밋")
        git_auto_commit(date_str)

        print(f"\n✅ 모든 작업 완료! {datetime.now(KST).strftime('%H:%M:%S KST')}")
        print(f"\n📊 저장된 파일:")
        print(f"   - 원본 데이터: data/archive/{date_str}.json")
        print(f"   - 분석 결과: data/analysis/{date_str}.json")
        print(f"   - HTML 파일: data/html/{date_str}.html")
        print(f"   - 이메일 발송: ✅")

    except Exception:
        print("\n❌ 오류 발생:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run()
