# =====================================================
# ui.py — ชิ้นส่วนหน้าจอที่ใช้ซ้ำ + ตัวช่วยจัดรูปแบบตัวเลข + การสลับหน้า
# (หน้าตาของชิ้นส่วนเหล่านี้กำหนดด้วย CSS ใน theme.py)
# =====================================================
import html

import numpy as np
import streamlit as st

# ลำดับหน้าในเมนู (ต้องตรงกับ PAGES ใน app.py)
PAGE_ORDER = ["page_home", "page_valuation", "page_risk", "page_quiz", "page_portfolio", "page_lao", "page_learn"]

CURRENCY = {"USD": "$", "THB": "฿", "EUR": "€", "GBP": "£", "JPY": "¥", "CNY": "¥", "HKD": "HK$", "LAK": "₭"}


def goto(page_key: str, symbol: str = None):
    """สลับไปหน้าอื่น / ถ้าส่ง symbol จะเปิดหุ้นตัวนั้น
    (ฝากคำสั่งไว้ที่ "_goto" แล้ว app.py จะตั้งค่าเมนูให้ในรอบวาดหน้าถัดไป)"""
    st.session_state["_goto"] = PAGE_ORDER.index(page_key)
    if symbol:
        st.session_state["symbol"] = symbol


def keep(key: str, default=None):
    """เรียกก่อนสร้างตัวเลือก (widget) ที่มี key นี้ เพื่อให้ค่าที่ผู้ใช้เลือกไว้ไม่หาย
    เวลาตัวเลือกถูกสร้างใหม่ เช่น ตอนสลับภาษา (ข้อความบนตัวเลือกเปลี่ยน → Streamlit มองเป็นตัวใหม่)
    ครั้งแรกจะตั้งเป็นค่า default"""
    st.session_state[key] = st.session_state.get(key, default)


def ok(v) -> bool:
    return v is not None and isinstance(v, (int, float, np.floating)) and np.isfinite(v)


def money(v, cur="USD", digits=2) -> str:
    """ราคา เช่น $356.27"""
    return f"{CURRENCY.get(cur, (cur or '') + ' ')}{v:,.{digits}f}" if ok(v) else "–"


def big(v, cur="USD") -> str:
    """ตัวเลขใหญ่แบบย่อ เช่น $5.18T, ฿1.09T, $399.8M"""
    if not ok(v):
        return "–"
    sign, a = ("-" if v < 0 else ""), abs(v)
    for unit, size in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if a >= size:
            return f"{sign}{CURRENCY.get(cur, (cur or '') + ' ')}{a / size:,.2f}{unit}"
    return f"{sign}{CURRENCY.get(cur, (cur or '') + ' ')}{a:,.0f}"


def pct(v, signed=False, digits=1) -> str:
    """เปอร์เซ็นต์ เช่น 12.3% / +12.3% (ค่าที่เกิน 1,000% แสดงเป็น >1,000%)"""
    if not ok(v):
        return "–"
    if abs(v) > 10:
        return (">" if v > 0 else "<-") + "1,000%"
    return f"{v * 100:{'+' if signed else ''},.{digits}f}%"


def num(v, digits=2) -> str:
    return f"{v:,.{digits}f}" if ok(v) else "–"


def esc(text) -> str:
    return html.escape(str(text or ""))


def md(html_text: str):
    """แสดง HTML ดิบ"""
    st.markdown(html_text, unsafe_allow_html=True)


def tile(label, value, sub="", meter=None, tone=""):
    """การ์ดตัวเลขเด่น: ป้ายชื่อ + ตัวเลขใหญ่ + คำอธิบาย (+ แถบวัด 0–1)"""
    bar = f'<div class="meter"><i style="width:{max(0, min(1, meter)) * 100:.0f}%"></i></div>' if meter is not None else ""
    md(f'<div class="tile"><div class="label">{label}</div>'
       f'<div class="value {tone}">{value}</div><div class="sub">{sub}</div>{bar}</div>')


def sparkline(values, color, w=160, h=44, fill=True) -> str:
    """เส้นกราฟจิ๋ว (SVG) ไว้ประกอบการ์ด — ไม่มีแกน แค่ให้เห็นทิศทาง"""
    if not values or len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    pts = [(i / (len(values) - 1) * w, h - 3 - (v - lo) / span * (h - 6)) for i, v in enumerate(values)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f'<polygon points="0,{h} {line} {w},{h}" fill="{color}" opacity=".14"/>' if fill else ""
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" height="{h}" preserveAspectRatio="none" aria-hidden="true">'
            f'{area}<polyline points="{line}" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/></svg>')


def change_html(chg) -> str:
    """% เปลี่ยนแปลง พร้อมลูกศรและสี (ไม่ใช้สีอย่างเดียว — มีลูกศรและเครื่องหมายกำกับ)"""
    if not ok(chg):
        return '<span class="tone-neutral">–</span>'
    tone, arrow = ("tone-good", "▲") if chg >= 0 else ("tone-bad", "▼")
    return f'<span class="{tone}">{arrow} {pct(chg, signed=True, digits=2)}</span>'
