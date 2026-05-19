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
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일"]
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
              padding:14px 16px;border-top:3px solid {col};">
    <div style="font-size:9pt;color:{C_MUTE};letter-spacing:1px;margin-bottom:5px;">{name}</div>
    <div style="font-family:'Courier New',monospace;font-size:22px;font-weight:700;
                color:{C_TEXT};margin-bottom:5px;">{_fmt(close)}</div>
    <div style="font-family:'Courier New',monospace;font-size:8pt;color:{col};">
      {arr} {_fmt(abs(chg))} &nbsp;
      <span>({_sign(pct)}{_fmt(pct)}%)</span>
      &nbsp;<span style="background:{tag_bg};color:{col};font-size:11px;
                         padding:2px 6px;border-radius:4px;font-weight:700;">{tag}</span>
    </div>
  </div>
</td>"""

    kospi  = kr.get("KOSPI",  {"close":0,"change":0,"pct":0})
    kosdaq = kr.get("KOSDAQ", {"close":0,"change":0,"pct":0})
    krx300 = kr.get("KRX300", {"close":0,"change":0,"pct":0})
    kr_cards = (
        index_card("KOSPI",  kospi["close"],  kospi["change"],  kospi["pct"]) +
        index_card("KOSDAQ", kosdaq["close"], kosdaq["change"], kosdaq["pct"]) +
        index_card("KRX300", krx300["close"], krx300["change"], krx300["pct"])
    )

    dow    = us.get("DOW",    {"close":0,"change":0,"pct":0})
    nasdaq = us.get("NASDAQ", {"close":0,"change":0,"pct":0})
    sp500  = us.get("SP500",  {"close":0,"change":0,"pct":0})
    us_cards = (
        index_card("DOW JONES", dow["close"],    dow["change"],    dow["pct"]) +
        index_card("NASDAQ",    nasdaq["close"], nasdaq["change"], nasdaq["pct"]) +
        index_card("S&P 500",   sp500["close"],  sp500["change"],  sp500["pct"])
    )

    sector_rows = ""
    for s in sec[:8]:
        pct = s["pct"]
        col = _color(pct)
        bar_w = min(abs(pct) / 6 * 100, 100)
        sector_rows += f"""
<tr>
  <td style="padding:5px 0;font-size:8pt;color:{C_MUTE};width:70px;">{s['name']}</td>
  <td style="padding:5px 8px;">
    <div style="background:#1e2d45;border-radius:2px;height:4px;width:100%;">
      <div style="background:{col};height:4px;border-radius:2px;width:{bar_w:.0f}%;"></div>
    </div>
  </td>
  <td style="padding:5px 0;font-family:'Courier New',monospace;font-size:8pt;
             color:{col};text-align:right;">{_sign(pct)}{_fmt(pct)}%</td>
</tr>"""

    def summary_row(label, value, color=C_TEXT):
        return f"""
<tr style="border-bottom:1px solid #1e2d45;">
  <td style="padding:6px 0;font-size:8pt;color:{C_MUTE};">{label}</td>
  <td style="padding:6px 0;font-family:'Courier New',monospace;font-size:8pt;
             color:{color};text-align:right;">{value}</td>
</tr>"""

    inv_f = inv.get("외국인", 0)
    inv_i = inv.get("기관", 0)
    inv_p = inv.get("개인", 0)
    bond_rate = bond.get("rate", 0)
    dep_amt   = dep.get("amount", 0)

    market_rows = (
        summary_row("외국인 순매수", f"{_sign(inv_f)}{inv_f:,}억", _inv_color(inv_f)) +
        summary_row("기관 순매수",   f"{_sign(inv_i)}{inv_i:,}억", _inv_color(inv_i)) +
        summary_row("개인 순매수",   f"{_sign(inv_p)}{inv_p:,}억", _inv_color(inv_p)) +
        summary_row("국채 3년 금리", f"{bond_rate:.2f}%", C_ACC) +
        summary_row("투자자예탁금",  f"{dep_amt:.1f}조", C_UP if dep_amt > 0 else C_TEXT)
        ))
    )

    badge_colors = {
        "red":  (C_UP,  "rgba(229,62,62,.18)"),
        "blue": (C_DN,  "rgba(49,130,206,.18)"),
        "gold": (C_ACC, "rgba(245,158,11,.18)"),
    }
    issue_blocks = ""
    for iss in issues:
        col, bg = badge_colors.get(iss.get("color","gold"), (C_ACC, "rgba(245,158,11,.18)"))
        badge_emoji = {"충격":"🔴","주의":"🔴","변수":"🔵","주목":"🟡","참고":"🟡"}.get(iss.get("badge","참고"),"🟡")
        issue_blocks += f"""
<div style="background:rgba(255,255,255,.03);border-left:3px solid {col};
            border-radius:0 6px 6px 0;padding:10px 14px;margin-bottom:10px;">
  <span style="background:{bg};color:{col};font-size:9px;font-weight:700;
               padding:2px 6px;border-radius:4px;margin-right:8px;">
    {badge_emoji} {iss.get('badge','참고')}
  </span>
  <strong style="color:{C_TEXT};font-size:10pt;">{iss.get('title','')}</strong>
  <div style="font-size:10pt;color:{C_MUTE};margin-top:5px;line-height:1.7;">
    {iss.get('text','')}
  </div>
</div>"""

    news_links = ""
    for n in news[:4]:
        news_links += f"""
<div style="padding:5px 0;border-bottom:1px solid #1e2d45;font-size:10pt;">
  <a href="{n.get('link','#')}" style="color:{C_DN};text-decoration:none;">
    📰 {n.get('title','')}
  </a>
</div>"""

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0f1724;font-family:'Apple SD Gothic Neo','Noto Sans KR',sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0f1724;padding:20px 0;">
<tr><td align="center">
<table width="680" cellpadding="0" cellspacing="0"
       style="background:{C_BG};border-radius:12px;overflow:hidden;border:1px solid #1e2d45;max-width:680px;width:100%;">

  <!-- 헤더 -->
  <tr>
    <td style="background:linear-gradient(135deg,#111827 0%,#1a2235 100%);
               padding:24px 28px;border-bottom:2px solid {C_ACC};">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td>
            <div style="font-size:28px;font-weight:700;color:{C_TEXT};">
              MARKET<span style="color:{C_ACC};">VIEW</span>
            </div>
            <div style="font-size:10pt;color:{C_MUTE};margin-top:3px;">
              Daily Market Report &nbsp;|&nbsp; {date_str}
            </div>
          </td>
          <td align="right">
            <div style="background:rgba(245,158,11,.15);border:1px solid rgba(245,158,11,.3);
                        border-radius:6px;padding:6px 12px;font-size:10pt;color:{C_ACC};">
              📈 시황 리포트
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- 아침인사 + 버핏 명언 -->
  {greeting_section}

  <!-- 국내 지수 -->
  <tr>
    <td style="padding:20px 28px 0;">
      <div style="font-size:12pt;font-weight:700;color:{C_TEXT};margin-bottom:10px;">🇰🇷 국내 주요 지수</div>
      <table width="100%" cellpadding="0" cellspacing="0"><tr>{kr_cards}</tr></table>
    </td>
  </tr>

  <!-- 미국 지수 -->
  <tr>
    <td style="padding:16px 28px 0;">
      <div style="font-size:12pt;font-weight:700;color:{C_TEXT};margin-bottom:10px;">🇺🇸 미국 3대 지수</div>
      <table width="100%" cellpadding="0" cellspacing="0"><tr>{us_cards}</tr></table>
    </td>
  </tr>

  <!-- 업종 + 시장요약 -->
  <tr>
    <td style="padding:16px 28px 0;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td width="50%" style="padding-right:10px;vertical-align:top;">
            <div style="background:#111827;border:1px solid #1e2d45;border-radius:10px;padding:14px;">
              <div style="font-size:10pt;font-weight:700;color:{C_TEXT};margin-bottom:10px;">📊 업종별 등락률</div>
              <table width="100%" cellpadding="0" cellspacing="0">{sector_rows}</table>
            </div>
          </td>
          <td width="50%" style="padding-left:10px;vertical-align:top;">
            <div style="background:#111827;border:1px solid #1e2d45;border-radius:10px;padding:14px;">
              <div style="font-size:10pt;font-weight:700;color:{C_TEXT};margin-bottom:10px;">📈 시장 요약</div>
              <table width="100%" cellpadding="0" cellspacing="0">{market_rows}</table>
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- 시황 코멘트 -->
  <tr>
    <td style="padding:16px 28px 0;">
      <div style="background:#1a2235;border:1px solid {C_ACC};border-radius:10px;padding:16px 20px;">
        <div style="font-size:10px;color:{C_ACC};font-weight:700;letter-spacing:2px;margin-bottom:8px;">
          💬 TODAY'S COMMENT
        </div>
        <div style="font-size:10pt;color:{C_TEXT};line-height:1.9;">{summary}</div>
      </div>
    </td>
  </tr>

  <!-- 핵심 이슈 -->
  <tr>
    <td style="padding:16px 28px 0;">
      <div style="font-size:10pt;font-weight:700;color:{C_TEXT};margin-bottom:10px;">🔍 핵심 이슈</div>
      {issue_blocks}
    </td>
  </tr>

  <!-- 푸터 -->
  <tr>
    <td style="padding:20px 28px;border-top:1px solid #1e2d45;margin-top:16px;">
      <div style="font-size:12pt;color:{C_TEXT};font-weight:bold;margin-bottom:8px;">본 리포트는 투자 참고용이며 투자 결과에 대한 책임은 투자자 본인에게 있습니다.</div>
      <div style="font-size:9pt;color:{C_MUTE};text-align:center;line-height:1.8;">
        MARKETVIEW Daily Report &nbsp;|&nbsp; 매일 오전 6:50 KST 자동 발송<br>
        데이터 출처: 한국거래소(KRX) · 네이버금융 · Yahoo Finance
      </div>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    return html
