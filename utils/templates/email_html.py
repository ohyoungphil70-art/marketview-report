
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

BUFFETT_QUOTES = [
    ("남들이 탐욕스러울 때 두려워하고, 남들이 두려워할 때 탐욕스러워져라.", "Be fearful when others are greedy, and greedy when others are fearful."),
    ("가격은 당신이 지불하는 것이고, 가치는 당신이 얻는 것이다.", "Price is what you pay. Value is what you get."),
]

def _color(pct):
    return C_UP if pct >= 0 else C_DN

def _arrow(pct):
    return "▲" if pct >= 0 else "▼"

def _fmt(val, decimals=2):
    return f"{val:,.{decimals}f}"

def _sign(val):
    return "+" if val >= 0 else ""

def build_email_html(data: dict, analysis: dict) -> str:
    date_str = data.get("date", datetime.now(KST).strftime("%Y년 %m월 %d일"))
    kr = data.get("kr", {})
    us = data.get("us", {})
    sec = data.get("sectors", [])
    inv = data.get("investors", {})
    bond = data.get("bond", {})
    dep = data.get("deposit", {})
    summary = analysis.get("summary", "")
    issues = analysis.get("issues", [])

    quote_kr, quote_en = random.choice(BUFFETT_QUOTES)

    now = datetime.now(KST)
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    weekday = weekdays[now.weekday()]

    def index_card(name, close, chg, pct):
        col = _color(pct)
        arr = _arrow(pct)
        tag = "강세" if pct >= 0 else "약세"
        tag_bg = "rgba(229,62,62,.15)" if pct >= 0 else "rgba(49,130,206,.15)"
        font_size = "26px" if close >= 10000 else "32px"
        return f'<td style="width:33.33%;padding:0 10px;"><div style="background:#1a2235;border:2px solid {col};border-radius:12px;padding:22px;text-align:center;"><div style="font-size:10pt;color:{C_MUTE};font-weight:700;margin-bottom:16px;text-transform:uppercase;letter-spacing:2px;">{name}</div><div style="font-family:\'Courier New\',monospace;font-size:{font_size};font-weight:900;color:{C_TEXT};line-height:1;margin-bottom:14px;letter-spacing:-1px;">{_fmt(close)}</div><div style="border-top:2px solid rgba(255,255,255,.1);padding-top:14px;"><div style="font-family:\'Courier New\',monospace;font-size:18pt;color:{col};font-weight:700;margin-bottom:4px;">{arr} {_fmt(abs(chg))}</div><div style="font-family:\'Courier New\',monospace;font-size:18pt;color:{col};font-weight:700;margin-bottom:12px;">({_sign(pct)}{_fmt(pct)}%)</div><span style="background:{tag_bg};color:{col};font-size:11px;padding:6px 14px;border-radius:6px;font-weight:700;display:inline-block;border:1px solid {col};">{tag}</span></div></div></td>'

    kospi = kr.get("KOSPI", {"close": 0, "change": 0, "pct": 0})
    kosdaq = kr.get("KOSDAQ", {"close": 0, "change": 0, "pct": 0})
    krx300 = kr.get("KRX300", {"close": 0, "change": 0, "pct": 0})
    kr_cards = (
        index_card("KOSPI", kospi["close"], kospi["change"], kospi["pct"]) +
        index_card("KOSDAQ", kosdaq["close"], kosdaq["change"], kosdaq["pct"]) +
        index_card("KRX300", krx300["close"], krx300["change"], krx300["pct"])
    )

    dow = us.get("DOW", {"close": 0, "change": 0, "pct": 0})
    nasdaq = us.get("NASDAQ", {"close": 0, "change": 0, "pct": 0})
    sp500 = us.get("SP500", {"close": 0, "change": 0, "pct": 0})
    us_cards = (
        index_card("DOW JONES", dow["close"], dow["change"], dow["pct"]) +
        index_card("NASDAQ", nasdaq["close"], nasdaq["change"], nasdaq["pct"]) +
        index_card("S&P 500", sp500["close"], sp500["change"], sp500["pct"])
    )

    sector_rows = ""
    for s in sec[:8]:
        pct = s["pct"]
        col = _color(pct)
        bar_w = min(abs(pct) / 6 * 100, 100)
        sector_rows += f'<tr><td style="padding:12px 0;font-size:11pt;color:{C_MUTE};font-weight:600;width:80px;">{s["name"]}</td><td style="padding:12px 12px;"><div style="background:rgba(30,45,69,.6);border-radius:4px;height:8px;"><div style="background:{col};height:8px;border-radius:4px;width:{bar_w:.0f}%;"></div></div></td><td style="padding:12px 0;font-family:\'Courier New\',monospace;font-size:13pt;color:{col};text-align:right;font-weight:700;width:60px;">{_sign(pct)}{_fmt(pct)}%</td></tr>'

    inv_f = inv.get("외국인", 0)
    inv_i = inv.get("기관", 0)
    inv_p = inv.get("개인", 0)
    bond_rate = bond.get("rate", 0)
    dep_amt = dep.get("amount", 0)

    market_rows = f'<tr style="border-bottom:1px solid rgba(255,255,255,.08);"><td style="padding:14px 0;font-size:11pt;color:{C_MUTE};font-weight:600;">외국인 순매수</td><td style="padding:14px 0;font-family:\'Courier New\',monospace;font-size:13pt;color:{C_UP if inv_f >= 0 else C_DN};text-align:right;font-weight:700;">{_sign(inv_f)}{inv_f:,}억</td></tr>'
    market_rows += f'<tr style="border-bottom:1px solid rgba(255,255,255,.08);"><td style="padding:14px 0;font-size:11pt;color:{C_MUTE};font-weight:600;">기관 순매수</td><td style="padding:14px 0;font-family:\'Courier New\',monospace;font-size:13pt;color:{C_UP if inv_i >= 0 else C_DN};text-align:right;font-weight:700;">{_sign(inv_i)}{inv_i:,}억</td></tr>'
    market_rows += f'<tr style="border-bottom:1px solid rgba(255,255,255,.08);"><td style="padding:14px 0;font-size:11pt;color:{C_MUTE};font-weight:600;">개인 순매수</td><td style="padding:14px 0;font-family:\'Courier New\',monospace;font-size:13pt;color:{C_UP if inv_p >= 0 else C_DN};text-align:right;font-weight:700;">{_sign(inv_p)}{inv_p:,}억</td></tr>'
    market_rows += f'<tr style="border-bottom:1px solid rgba(255,255,255,.08);"><td style="padding:14px 0;font-size:11pt;color:{C_MUTE};font-weight:600;">국채 3년 금리</td><td style="padding:14px 0;font-family:\'Courier New\',monospace;font-size:13pt;color:{C_ACC};text-align:right;font-weight:700;">{bond_rate:.2f}%</td></tr>'
    market_rows += f'<tr style="border-bottom:1px solid rgba(255,255,255,.08);"><td style="padding:14px 0;font-size:11pt;color:{C_MUTE};font-weight:600;">투자자예탁금</td><td style="padding:14px 0;font-family:\'Courier New\',monospace;font-size:13pt;color:{C_ACC};text-align:right;font-weight:700;">{dep_amt:.1f}조</td></tr>'
    market_rows += f'<tr><td style="padding:14px 0;font-size:11pt;color:{C_MUTE};font-weight:600;">KOSPI 전일대비</td><td style="padding:14px 0;font-family:\'Courier New\',monospace;font-size:13pt;color:{_color(kospi["pct"])};text-align:right;font-weight:700;">{_sign(kospi["change"])}{_fmt(kospi["change"])} ({_sign(kospi["pct"])}{_fmt(kospi["pct"])}%)</td></tr>'

    issue_blocks = ""
    for iss in issues:
        badge_colors = {"red": (C_UP, "rgba(229,62,62,.15)"), "blue": (C_DN, "rgba(49,130,206,.15)"), "gold": (C_ACC, "rgba(245,158,11,.15)")}
        col, bg = badge_colors.get(iss.get("color", "gold"), (C_ACC, "rgba(245,158,11,.15)"))
        badge_emoji = {"충격": "🔴", "주의": "🔴", "변수": "🔵", "주목": "🟡", "참고": "🟡"}.get(iss.get("badge", "참고"), "🟡")
        issue_blocks += f'<div style="background:rgba(255,255,255,.02);border-left:4px solid {col};border-radius:8px;padding:16px;margin-bottom:12px;"><span style="background:{bg};color:{col};font-size:11px;padding:6px 12px;border-radius:6px;font-weight:700;display:inline-block;border:1px solid {col};margin-bottom:8px;margin-right:8px;">{badge_emoji} {iss.get("badge", "참고")}</span><div style="color:{C_TEXT};font-size:11pt;font-weight:700;margin-bottom:6px;">{iss.get("title", "")}</div><div style="color:{C_MUTE};font-size:10pt;line-height:1.6;">{iss.get("text", "")}</div></div>'

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0f1724;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0f1724;padding:20px 0;">
<tr><td align="center">
<table width="720" cellpadding="0" cellspacing="0" style="background:{C_BG};border-radius:14px;overflow:hidden;border:1px solid #1e2d45;max-width:720px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.5);">
<tr><td style="background:linear-gradient(135deg,#111827 0%,#1a2235 100%);padding:32px 40px;border-bottom:3px solid {C_ACC};"><table width="100%"><tr><td><div style="font-size:32px;font-weight:900;color:{C_TEXT};letter-spacing:-1px;">MARKET<span style="color:{C_ACC};">VIEW</span></div><div style="font-size:11pt;color:{C_MUTE};margin-top:6px;letter-spacing:1px;">DAILY MARKET REPORT</div></td><td align="right"><div style="font-size:13pt;color:{C_ACC};font-weight:700;text-align:right;">📅 {date_str}<br><span style="font-size:10pt;color:{C_MUTE};">{weekday}</span></div></td></tr></table></td></tr>
<tr><td style="padding:24px 40px 0;"><div style="background:linear-gradient(135deg,rgba(245,158,11,.15) 0%,rgba(245,158,11,.05) 100%);border-left:4px solid {C_ACC};border-radius:8px;padding:20px 24px;"><div style="font-size:12pt;color:{C_ACC};font-weight:700;margin-bottom:12px;">💡 TODAY'S INSIGHT</div><div style="font-size:11pt;color:{C_TEXT};font-style:italic;line-height:1.8;">"{quote_kr}"</div></div></td></tr>
<tr><td style="padding:24px 40px 0;"><div style="margin-bottom:8px;"><div style="font-size:14pt;font-weight:900;color:{C_TEXT};letter-spacing:1px;margin-bottom:16px;">🇰🇷 국내 주요 지수</div><table width="100%"><tr>{kr_cards}</tr></table></div></td></tr>
<tr><td style="padding:24px 40px 0;"><div style="margin-bottom:8px;"><div style="font-size:14pt;font-weight:900;color:{C_TEXT};letter-spacing:1px;margin-bottom:16px;">🇺🇸 미국 3대 지수</div><table width="100%"><tr>{us_cards}</tr></table></div></td></tr>
<tr><td style="padding:24px 40px 0;"><table width="100%"><tr><td width="48%" style="padding-right:20px;vertical-align:top;"><div style="background:linear-gradient(135deg,#1a2235 0%,#111827 100%);border:1px solid #1e2d45;border-radius:12px;padding:20px;"><div style="font-size:12pt;font-weight:900;color:{C_TEXT};margin-bottom:16px;letter-spacing:1px;">📊 업종별 등락률</div><table width="100%">{sector_rows}</table></div></td><td width="52%" style="padding-left:20px;vertical-align:top;"><div style="background:linear-gradient(135deg,#1a2235 0%,#111827 100%);border:1px solid #1e2d45;border-radius:12px;padding:20px;"><div style="font-size:12pt;font-weight:900;color:{C_TEXT};margin-bottom:16px;letter-spacing:1px;">📈 시장 요약</div><table width="100%">{market_rows}</table></div></td></tr></table></td></tr>
<tr><td style="padding:24px 40px 0;"><div style="background:linear-gradient(135deg,rgba(242,113,28,.15) 0%,rgba(242,113,28,.05) 100%);border:1px solid {C_ACC};border-radius:12px;padding:24px;"><div style="font-size:11pt;color:{C_ACC};font-weight:700;margin-bottom:12px;letter-spacing:1px;">💬 시황 분석</div><div style="font-size:11pt;color:{C_TEXT};line-height:1.9;">{summary}</div></div></td></tr>
<tr><td style="padding:24px 40px 0;"><div style="font-size:12pt;font-weight:900;color:{C_TEXT};margin-bottom:16px;letter-spacing:1px;">🔍 핵심 이슈</div>{issue_blocks}</td></tr>
<tr><td style="padding:28px 40px;border-top:2px solid #1e2d45;background:rgba(0,0,0,.2);"><div style="font-size:12pt;color:{C_TEXT};font-weight:700;margin-bottom:12px;">본 리포트는 투자 참고용이며 투자 결과에 대한 책임은 투자자 본인에게 있습니다.</div><div style="font-size:9pt;color:{C_MUTE};text-align:center;line-height:1.8;">MARKETVIEW Daily Report &nbsp;|&nbsp; 매일 오전 6:50 KST 자동 발송</div></td></tr>
</table></td></tr></table></body></html>'''
    
    return html
