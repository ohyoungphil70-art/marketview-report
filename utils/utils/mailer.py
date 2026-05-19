"""
marketview/utils/mailer.py
이메일 발송 모듈
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.utils.templates.email_html import build_email_html

def send_report_email(data: dict, analysis: dict) -> bool:
    """
    시황 리포트 이메일 발송
    """
    try:
        # 환경변수에서 Gmail 정보 가져오기
        gmail_user = os.getenv("GMAIL_USER", "")
        gmail_pass = os.getenv("GMAIL_APP_PASS", "")
        report_to = os.getenv("REPORT_TO", "")
        
        if not gmail_user or not gmail_pass:
            print("❌ Gmail 인증정보가 없습니다")
            return False
        
        # 수신자 리스트
        recipients = [
            report_to,
            "ops114@nhqv.com",
            "devil17c@naver.com",
            "21283@naver.com",
        ]
        recipients = [r for r in recipients if r]  # 빈 값 제거
        
        if not recipients:
            print("❌ 수신자가 없습니다")
            return False
        
        # HTML 이메일 생성
        html_content = build_email_html(data, analysis)
        
        # 이메일 구성
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📊 MarketView Daily Report - {data.get('date', '')}"
        msg["From"] = gmail_user
        msg["To"] = ", ".join(recipients)
        
        # HTML 부분 추가
        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)
        
        # Gmail SMTP 서버로 발송
        print(f"📧 이메일 발송 중... ({', '.join(recipients)})")
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, recipients, msg.as_string())
        
        print(f"✅ 이메일 발송 완료 ({len(recipients)}명)")
        return True
        
    except Exception as e:
        print(f"❌ 이메일 발송 실패: {e}")
        return False
