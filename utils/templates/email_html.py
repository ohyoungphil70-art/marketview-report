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
C_TEXT = "#e2e8f0"
C_MUTE = "#94a3b8"

QUOTES = [
    ("남들이 탐욕스러울 때 두려워하고, 남들이 두려워할 때 탐욕스러워져라.", "Warren Buffett"),
    ("가격은 당신이 지불하는 것이고, 가치는 당신이 얻는 것이다.", "Warren Buffett"),
    ("리스크는 자신이 무엇을 하고 있는지 모를 때 발생한다.", "Warren Buffett"),
    ("훌륭한 회사를 적당한 가격에 사는 것이 적당한 회사를 훌륭한 가격에 사는 것보다 훨씬 낫다.", "Warren Buffett"),
    ("주식시장은 인내심 없는 사람의 돈을 인내심 있는 사람에게 이전하는 장치다.", "Warren Buffett"),
    ("오늘 누군가는 그늘에 앉아 있다. 그것은 오래전에 누군가가 나무를 심었기 때문이다.", "Warren Buffett"),
    ("분산투자는 무지에 대한 보호책이다.", "Warren Buffett"),
    ("최고의 투자는 자기 자신에 대한 투자다.", "Warren Buffett"),
    ("주가는 단기적으로는 인기투표이지만, 장기적으로는 가치 측정기다.", "Benjamin Graham"),
    ("시장을 예측하려 하지 말고, 시장에 적응하라.", "Peter Lynch"),
    ("강세장은 비관론 속에서 태어나고, 회의론 속에서 성장하고, 낙관론 속에서 성숙해지고, 행복감 속에서 죽는다.", "John Templeton"),
    ("투자에서 가장 위험한 말은 '이번엔 다르다'는 것이다.", "John Templeton"),
]


def _color(pct: float) -> str:
    return C_UP if pct >= 0 else C_DN

def _arrow(pct: float) -> str:
    return "▲" if pct >= 0 else "▼"

def _fmt(val: float, decimals: int = 2) -> str:
    return f"{val:,.{decimals}f}"

def _sign(val: float) -> str:
    return "+" if val >= 0 else ""


def _index_card(name: str, close: float, chg: float, pct: float) -> str:
    col     = _color(pct)
    arr     = _arrow(pct)
    tag     = "강세" if pct >= 0 else "약세"
    tag_bg  = "rgba(229,62,62,.18)" if pct >= 0 else "rgba(49,130,206,.18)"
    val_size = "22px" if close >= 10000 else "28px"
    return (
        f'<td style="width:33.33%;padding:0 8px;">'
        f'<div style="background:#1a2235;border:2px solid {col};border-radius:12px;'
        f'padding:14px 12px;text-align:center;">'
        # 인덱스 이름
        f'<div style="font-size:13px;color:{C_MUTE};font-weight:700;margin-bottom:14px;'
        f'text-transform:uppercase;letter-spacing:2px;">{name}</div>'
        # 종가
        f'<div style="font-family:\'Courier New\',monospace;font-size:{val_size};'
        f'font-weight:900;color:{C_TEXT};line-height:1;margin-bottom:12px;'
        f'letter-spacing:-1px;">{_fmt(close)}</div>'
        # 구분선 + 변동
        f'<div style="border-top:1px solid rgba(255,255,255,.12);padding-top:12px;">'
        f'<div style="font-family:\'Courier New\',monospace;font-size:15px;'
        f'color:{col};font-weight:700;margin-bottom:2px;">'
        f'{arr} {_fmt(abs(chg))}</div>'
        f'<div style="font-family:\'Courier New\',monospace;font-size:15px;'
        f'color:{col};font-weight:700;margin-bottom:10px;">'
        f'({_sign(pct)}{_fmt(pct)}%)</div>'
        f'<span style="background:{tag_bg};color:{col};font-size:12px;'
        f'padding:5px 12px;border-radius:5px;font-weight:700;'
        f'display:inline-block;border:1px solid {col};">{tag}</span>'
        f'</div></div></td>'
    )


def _section_title(emoji: str, title: str) -> str:
    return (
        f'<div style="font-size:15px;font-weight:900;color:{C_TEXT};'
        f'letter-spacing:1px;margin-bottom:12px;">{emoji} {title}</div>'
    )


def build_email_html(data: dict, analysis: dict) -> str:
    date_str = data.get("date", datetime.now(KST).strftime("%Y년 %m월 %d일"))
    kr  = data.get("kr", {})
    us  = data.get("us", {})
    sec = data.get("sectors", [])
    inv = data.get("investors", {})
    bond = data.get("bond", {})
    dep  = data.get("deposit", {})
    summary = analysis.get("summary", "")
    issues  = analysis.get("issues", [])

    quote_text, quote_author = random.choice(QUOTES)

    now = datetime.now(KST)
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    weekday  = weekdays[now.weekday()]

    # ── 국내 지수 카드 ──
    def _kr(key):
        return kr.get(key, {"close": 0, "change": 0, "pct": 0})

    kr_cards = (
        _index_card("KOSPI",  _kr("KOSPI")["close"],  _kr("KOSPI")["change"],  _kr("KOSPI")["pct"])
        + _index_card("KOSDAQ", _kr("KOSDAQ")["close"], _kr("KOSDAQ")["change"], _kr("KOSDAQ")["pct"])
        + _index_card("SOX",    _kr("SOX")["close"],    _kr("SOX")["change"],    _kr("SOX")["pct"])
    )

    # ── 미국 지수 카드 ──
    def _us(key):
        return us.get(key, {"close": 0, "change": 0, "pct": 0})

    us_cards = (
        _index_card("DOW JONES", _us("DOW")["close"],    _us("DOW")["change"],    _us("DOW")["pct"])
        + _index_card("NASDAQ",    _us("NASDAQ")["close"], _us("NASDAQ")["change"], _us("NASDAQ")["pct"])
        + _index_card("S&P 500",   _us("SP500")["close"],  _us("SP500")["change"],  _us("SP500")["pct"])
    )

    # ── 업종 바 차트 ──
    sector_rows = ""
    for s in sec[:5]:
        pct = s["pct"]
        col = _color(pct)
        bar_w = min(abs(pct) / 5 * 100, 100)
        sector_rows += (
            f'<tr>'
            f'<td style="padding:10px 0;font-size:13px;color:{C_MUTE};'
            f'font-weight:600;width:80px;white-space:nowrap;">{s["name"]}</td>'
            f'<td style="padding:10px 10px;">'
            f'<div style="background:rgba(30,45,69,.6);border-radius:4px;height:10px;">'
            f'<div style="background:{col};height:10px;border-radius:4px;'
            f'width:{bar_w:.0f}%;"></div></div></td>'
            f'<td style="padding:10px 0;font-family:\'Courier New\',monospace;'
            f'font-size:14px;color:{col};text-align:right;font-weight:700;'
            f'width:65px;">{_sign(pct)}{_fmt(pct)}%</td>'
            f'</tr>'
        )

    # ── 시장 요약 테이블 ──
    inv_f = inv.get("외국인", 0)
    inv_i = inv.get("기관",   0)
    inv_p = inv.get("개인",   0)
    inv_f_chg = inv.get("외국인_chg")
    inv_i_chg = inv.get("기관_chg")
    inv_p_chg = inv.get("개인_chg")
    bond_rate   = bond.get("rate") or 0
    bond_change = bond.get("change") or 0
    dep_amt     = dep.get("amount")

    def _mrow(label: str, value_html: str, last: bool = False) -> str:
        border = "" if last else "border-bottom:1px solid rgba(255,255,255,.08);"
        return (
            f'<tr style="{border}">'
            f'<td style="padding:8px 0;font-size:13px;color:{C_MUTE};font-weight:600;">'
            f'{label}</td>'
            f'<td style="padding:8px 0;font-family:\'Courier New\',monospace;'
            f'font-size:13px;text-align:right;font-weight:700;">{value_html}</td>'
            f'</tr>'
        )

    def _inv_val(v, chg=None):
        c = C_UP if v >= 0 else C_DN
        html = f'<span style="color:{c};">{_sign(v)}{v:,}억</span>'
        if chg is not None:
            cc = C_UP if chg >= 0 else C_DN
            html += (f' <span style="font-size:11px;color:{cc};">'
                     f'({_sign(chg)}{chg:,}억)</span>')
        return html

    # 값이 있는 행만 동적으로 구성 (0이면 숨김)
    rows_list = []
    if inv_f != 0:
        rows_list.append(("외국인 순매수", _inv_val(inv_f, inv_f_chg)))
    if inv_i != 0:
        rows_list.append(("기관 순매수",   _inv_val(inv_i, inv_i_chg)))
    if inv_p != 0:
        rows_list.append(("개인 순매수",   _inv_val(inv_p, inv_p_chg)))
    if bond_rate:
        bond_color = C_UP if bond_change >= 0 else C_DN
        rows_list.append(("국채 3년 금리",
                           f'<span style="color:{C_ACC};">{bond_rate:.2f}%</span>'
                           f' <span style="font-size:11px;color:{bond_color};">({_sign(bond_change)}{bond_change:.3f}%p)</span>'))
    if dep_amt:
        rows_list.append(("투자자예탁금",
                           f'<span style="color:{C_ACC};">{dep_amt:.1f}조</span>'))

    market_rows = ""
    for i, (label, val_html) in enumerate(rows_list):
        market_rows += _mrow(label, val_html, last=(i == len(rows_list) - 1))

    # ── 핵심 이슈 블록 ──
    badge_style = {
        "red":  (C_UP,  "rgba(229,62,62,.18)"),
        "blue": (C_DN,  "rgba(49,130,206,.18)"),
        "gold": (C_ACC, "rgba(245,158,11,.18)"),
    }
    badge_emoji = {"충격": "🔴", "주의": "🟠", "변수": "🔵", "주목": "🟡", "참고": "⚪"}

    issue_blocks = ""
    for iss in issues:
        col, bg = badge_style.get(iss.get("color", "gold"), badge_style["gold"])
        emoji   = badge_emoji.get(iss.get("badge", "참고"), "⚪")
        issue_blocks += (
            f'<div style="background:rgba(255,255,255,.025);border-left:4px solid {col};'
            f'border-radius:8px;padding:16px 18px;margin-bottom:12px;">'
            f'<span style="background:{bg};color:{col};font-size:12px;padding:5px 12px;'
            f'border-radius:5px;font-weight:700;display:inline-block;border:1px solid {col};'
            f'margin-bottom:10px;margin-right:8px;">{emoji} {iss.get("badge", "참고")}</span>'
            f'<div style="color:{C_TEXT};font-size:14px;font-weight:700;margin-bottom:6px;">'
            f'{iss.get("title", "")}</div>'
            f'<div style="color:{C_MUTE};font-size:13px;line-height:1.7;">'
            f'{iss.get("text", "")}</div>'
            f'</div>'
        )

    # ── 최종 HTML ──
    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <style>
    @media only screen and (max-width: 600px) {{
      .container {{ width: 100% !important; }}
      .index-card {{ display: block !important; width: 100% !important;
                     padding: 0 0 12px 0 !important; }}
      .index-card > div {{ margin: 0 !important; }}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background:#0f1724;">
<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#0f1724;padding:20px 0;">
<tr><td align="center">
<table class="container" width="680" cellpadding="0" cellspacing="0"
       style="background:{C_BG};border-radius:14px;overflow:hidden;
              border:1px solid #1e2d45;max-width:680px;width:100%;
              box-shadow:0 20px 60px rgba(0,0,0,.5);">

  <!-- HEADER -->
  <tr><td style="background:linear-gradient(135deg,#111827 0%,#1a2235 100%);
                 padding:30px 36px;border-bottom:3px solid {C_ACC};">
    <table width="100%"><tr>
      <td>
        <div style="font-size:28px;font-weight:900;color:{C_TEXT};letter-spacing:-1px;">
          MARKET<span style="color:{C_ACC};">VIEW</span>
        </div>
        <div style="font-size:12px;color:{C_MUTE};margin-top:5px;letter-spacing:2px;">
          DAILY MARKET REPORT
        </div>
      </td>
      <td align="right">
        <div style="font-size:14px;color:{C_ACC};font-weight:700;text-align:right;">
          📅 {date_str}<br>
          <span style="font-size:12px;color:{C_MUTE};">{weekday}</span>
        </div>
      </td>
    </tr></table>
  </td></tr>

  <!-- QUOTE -->
  <tr><td style="padding:14px 36px 0;">
    <div style="background:linear-gradient(135deg,rgba(245,158,11,.15) 0%,
                rgba(245,158,11,.05) 100%);border-left:4px solid {C_ACC};
                border-radius:8px;padding:18px 22px;">
      <div style="font-size:12px;color:{C_ACC};font-weight:700;margin-bottom:10px;">
        💡 TODAY'S INSIGHT
      </div>
      <div style="font-size:13px;color:{C_TEXT};font-style:italic;line-height:1.8;">
        "{quote_text}"
      </div>
      <div style="font-size:11px;color:{C_MUTE};margin-top:8px;text-align:right;">
        — {quote_author}
      </div>
    </div>
  </td></tr>

  <!-- 국내 지수 -->
  <tr><td style="padding:14px 36px 0;">
    {_section_title("🇰🇷", "국내 주요 지수")}
    <table width="100%"><tr class="index-card">{kr_cards}</tr></table>
  </td></tr>

  <!-- 미국 지수 -->
  <tr><td style="padding:14px 36px 0;">
    {_section_title("🇺🇸", "미국 3대 지수")}
    <table width="100%"><tr class="index-card">{us_cards}</tr></table>
  </td></tr>

  <!-- 업종 + 시장 요약 -->
  <tr><td style="padding:14px 36px 0;">
    <table width="100%"><tr>
      <td width="48%" style="padding-right:16px;vertical-align:top;">
        <div style="background:linear-gradient(135deg,#1a2235 0%,#111827 100%);
                    border:1px solid #1e2d45;border-radius:12px;padding:18px 16px;">
          {_section_title("📊", "업종별 등락률")}
          <table width="100%">{sector_rows}</table>
        </div>
      </td>
      <td width="52%" style="padding-left:16px;vertical-align:top;">
        <div style="background:linear-gradient(135deg,#1a2235 0%,#111827 100%);
                    border:1px solid #1e2d45;border-radius:12px;padding:18px 16px;">
          {_section_title("📈", "시장 요약")}
          <table width="100%">{market_rows}</table>
        </div>
      </td>
    </tr></table>
  </td></tr>

  <!-- 시황 분석 -->
  <tr><td style="padding:14px 36px 0;">
    <div style="background:linear-gradient(135deg,rgba(245,158,11,.12) 0%,
                rgba(245,158,11,.04) 100%);border:1px solid rgba(245,158,11,.4);
                border-radius:12px;padding:22px;">
      <div style="font-size:13px;color:{C_ACC};font-weight:700;margin-bottom:12px;
                  letter-spacing:1px;">💬 AI 시황 분석</div>
      <div style="font-size:14px;color:{C_TEXT};line-height:1.5;">{summary}</div>
    </div>
  </td></tr>

  <!-- 핵심 이슈 -->
  <tr><td style="padding:14px 36px 0;">
    {_section_title("🔍", "핵심 이슈")}
    {issue_blocks}
  </td></tr>

  <!-- FOOTER -->
  <tr><td style="padding:24px 36px;border-top:2px solid #1e2d45;
                 background:rgba(0,0,0,.2);margin-top:8px;">
    <div style="font-size:12px;color:{C_MUTE};text-align:center;line-height:2;">
      본 리포트는 투자 참고용이며 투자 결과에 대한 책임은 투자자 본인에게 있습니다.<br>
      MARKETVIEW Daily Report &nbsp;|&nbsp; 매일 오전 6:50 KST 자동 발송
    </div>
  </td></tr>

</table>
</td></tr></table>
</body>
</html>'''

    return html
