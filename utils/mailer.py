"""
marketview/utils/mailer.py
이메일 발송 모듈
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.templates.email_html import build_email_html

def send_report_email(data: dict, analysis: dict) -> bool:
    """시황 리포트 이메일 발송"""
    try:
        gmail_user = os.getenv("GMAIL_USER", "")
        gmail_pass = os.getenv("GMAIL_APP_PASS", "")
        report_to = os.getenv("REPORT_TO", "")
        
        if not gmail_user or not gmail_pass:
            print("❌ Gmail 인증정보가 없습니다")
            return False
        
        recipients = [report_to] if report_to else []
        
        if not recipients:
            print("❌ 수신자가 없습니다")
            return False
        
        html_content = build_email_html(data, analysis)
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📊 MarketView Daily Report - {data.get('date', '')}"
        msg["From"] = gmail_user
        msg["To"] = ", ".join(recipients)
        
        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)
        
        print(f"📧 이메일 발송 중... ({', '.join(recipients)})")
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, recipients, msg.as_string())
        
        print(f"✅ 이메일 발송 완료 ({len(recipients)}명)")
        return True
        
    except Exception as e:
        print(f"❌ 이메일 발송 실패: {e}")
        return False
