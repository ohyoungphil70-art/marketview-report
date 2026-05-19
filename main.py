"""
marketview/main.py
시황 리포트 생성 및 발송 메인 스크립트
"""
import os
import json
from datetime import datetime
import pytz
from data.collector import collect_all
from utils.claude_analyst import analyze_market
from utils.mailer import send_report_email
from utils.templates.email_html import build_email_html

KST = pytz.timezone("Asia/Seoul")

def ensure_directories():
    """필요한 디렉토리 생성"""
    dirs = ["data/archive", "data/analysis", "data/html", "reports"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def save_json(filename, data):
    """JSON 파일 저장"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 저장 완료: {filename}")
        return True
    except Exception as e:
        print(f"❌ 저장 실패: {filename} - {e}")
        return False

def save_html(filename, html_content):
    """HTML 파일 저장"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ HTML 저장: {filename}")
        return True
    except Exception as e:
        print(f"❌ HTML 저장 실패: {filename} - {e}")
        return False

def git_auto_commit(commit_msg):
    """Git 자동 커밋"""
    try:
        os.system(f'git add -A')
        os.system(f'git commit -m "{commit_msg}"')
        os.system(f'git push')
        print(f"✅ Git 커밋 완료: {commit_msg}")
        return True
    except Exception as e:
        print(f"❌ Git 커밋 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("=" * 50)
    print("📊 MarketView 시황 리포트 생성 시작")
    print("=" * 50)
    
    # 1단계: 디렉토리 생성
    ensure_directories()
    
    # 2단계: 데이터 수집
    print("\n📡 Step 1: 시장 데이터 수집")
    data = collect_all()
    
    # 3단계: AI 분석
    print("\n🤖 Step 2: Claude AI 분석")
    analysis = analyze_market(data)
    
    # 4단계: 이메일 발송
    print("\n📧 Step 3: 이메일 발송")
    try:
        send_report_email(data, analysis)
        print("✅ 이메일 발송 완료")
    except Exception as e:
        print(f"❌ 이메일 발송 실패: {e}")
    
    # 5단계: 데이터 저장
    print("\n💾 Step 4: 데이터 저장")
    today = datetime.now(KST).strftime("%Y-%m-%d")
    
    archive_file = f"data/archive/{today}.json"
    save_json(archive_file, data)
    
    analysis_file = f"data/analysis/{today}.json"
    save_json(analysis_file, analysis)
    
    # HTML 저장
    html_content = build_email_html(data, analysis)
    html_file = f"data/html/{today}.html"
    save_html(html_file, html_content)
    
    # 6단계: Git 커밋
    print("\n🔄 Step 5: Git 자동 커밋")
    commit_msg = f"Daily report {today} - {datetime.now(KST).strftime('%H:%M:%S')}"
    git_auto_commit(commit_msg)
    
    print("\n" + "=" * 50)
    print("✅ 시황 리포트 생성 완료!")
    print("=" * 50)

if __name__ == "__main__":
    main()
