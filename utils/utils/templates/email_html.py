"""
marketview/templates/email_html.py
수집 데이터 → 이메일용 HTML 생성
"""
from datetime import datetime
import pytz
import random

KST = pytz.timezone("Asia/Seoul")

C_UP   = "#e53e3e"
C_DN   = "#3182ce"
C_ACC  = "#f59e0b"
C_BG   = "#0a0e1a"
C_SURF = "#111827"
C_TEXT = "#e2e8f0"
C_MUTE = "#94a3b8"

# 워렌 버핏 투자 명언
BUFFETT_QUOTES = [
    ("남들이 탐욕스러울 때 두려워하고, 남들이 두려워할 때 탐욕스러워져라.",
     "Be fearful when others are greedy, and greedy when others are fearful."),
    ("가격은 당신이 지불하는 것이고, 가치는 당신이 얻는 것이다.",
     "Price is what you pay. Value is what you get."),
    ("10년간 보유할 생각이 없다면, 10분도 보유하지 마라.",
     "If you aren't willing to own a stock for 10 years, don't even think about owning it for 10 minutes."),
    ("리스크는 자신이 무엇을 하는지 모를 때 발생한다.",
     "Risk comes from not knowing what you're doing."),
    ("첫 번째 규칙: 절대 돈을 잃지 마라. 두 번째 규칙: 첫 번째 규칙을 절대 잊지 마라.",
     "Rule No.1: Never lose money. Rule No.2: Never forget rule No.1."),
    ("뛰어난 기업을 적정한 가격에 사는 것이 적정한 기업을 뛰어난 가격에 사는 것보다 훨씬 낫다.",
     "It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price."),
    ("주식시장은 인내심 없는 사람의 돈을 인내심 있는 사람에게 이전하는 장치다.",
     "The stock market is a device for transferring money from the impatient to the patient."),
    ("오늘 누군가 나무 그늘에 앉아 있는 것은 오래전 누군가가 나무를 심었기 때문이다.",
     "Someone is sitting in the shade today because someone planted a tree a long time ago."),
    ("분산투자는 무지에 대한 보호책이다. 자신이 무엇을 하는지 아는 사람에게는 거의 의미가 없다.",
     "Diversification is protection against ignorance. It makes little sense if you know what you are doing."),
    ("좋은 기업을 찾아내는 것보다 좋은 기업을 계속 보유하는 것이 더 어렵다.",
     "The most important thing to do if you find yourself in a hole is to stop digging."),
]


def _color(pct):
    return C_UP if pct >= 0 else C_DN

def _arrow(pct):
    return "▲" if pct >= 0 else "▼"

def _fmt(val, decimals=2):
    return f"{val:,.{decimals}f}"

def _sign(val):
    return "+" if val >= 0 else ""

def _inv_color(val):
    return C_UP if val >= 0 else C_DN


def build_email_html(data: dict, analysis: dict) -> str:
    date_str = data.get("date", datetime.now(KST).strftime("%Y년 %m월 %d일"))
    kr       = data.get("kr", {})
    us       = data.get("us", {})
    sec      = data.get("sectors", [])
    inv      = data.get("investors", {})
    bond     = data.get("bond", {})
    dep      = data.get("deposit", {})
    news     = data.get("news", [])
    summary  = analysis.get("summary", "")
    issues   = analysis.get("issues", [])

    # 오늘의 버핏 명언 랜덤 선택
    quote_kr, quote_en = random.choice(BUFFETT_QUOTES)

    # 요일
    now = datetime.now(KST)
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    weekday = weekdays[now.weekday()]

    # 아침 인사 + 명언 섹션
    greeting_section = f"""
<tr>
  <td style="padding:20px 28px 0;">
    <div style="background:linear-gradient(135deg,#1a2235 0%,#111827 100%);
                border:1px solid rgba(245,158,11,.3);border-radius:10px;padding:18px 20px;">
      <div style="font-size:10pt;color:{C_MUTE};margin-bottom:8px;">
        📅 {date_str} {weekday}
      </div>
      <div style="font-size:11pt;font-weight:700;color:{C_TEXT};margin-bottom:12px;line-height:1.8;">
        안녕하세요! 오늘도 성공적인 하루 되시길 바랍니다.<br>
        오늘의 워렌 버핏 명언을 전해드립니다. 🌅
      </div>
      <div style="border-left:3px solid {C_ACC};padding-left:14px;">
        <div style="font-size:11pt;color:{C_ACC};font-weight:700;line-height:1.9;">
          "{quote_kr}"
        </div>
        <div style="font-size:9pt;color:{C_MUTE};margin-top:4px;font-style:italic;">
          "{quote_en}"
        </div>
        <div style="font-size:9pt;color:{C_MUTE};margin-top:6px;text-align:right;">
          — Warren Buffett
        </div>
      </div>
    </div>
  </td>
</tr>"""

    def index_card(name, close, chg, pct):
        col = _color(pct)
        arr = _arrow(pct)
        tag = "강세" if pct >= 0 else "약세"
        tag_bg = "rgba(229,62,62,.18)" if pct >= 0 else "rgba(49,130,206,.18)"
        return f"""
<td style="width:33%;padding:0 6px;">
  <div style="background:#1a2235;border:1px solid {col};border-radius:10px;
