"""
marketview/utils/mailer.py
Gmail SMTP로 HTML 이메일 발송
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import pytz

KST = pytz.timezone("Asia/Seoul")


def send_email(html_content: str, subject: str = None) -> bool:
    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASS", "")
    report_to  = os.environ.get("REPORT_TO", gmail_user)

    if not gmail_user or not gmail_pass:
        print("❌ Gmail 환경변수 미설정 (GMAIL_USER, GMAIL_APP_PASS)")
        return False

    today = datetime.now(KST).strftime("%Y.%m.%d")
    if subject is None:
        subject = f"📈 MarketView 시황 리포트 — {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"MarketView <{gmail_user}>"
    msg["To"]      = report_to

    part = MIMEText(html_content, "html", "utf-8")
    msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, report_to, msg.as_string())
        print(f"✅ 이메일 발송 완료 → {report_to}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("❌ Gmail 인증 실패 — 앱 비밀번호를 확인하세요")
        return False
    except Exception as e:
        print(f"❌ 이메일 발송 오류: {e}")
        return False
