# =====================================================
# notify.py — การแจ้งเตือนในเว็บ (ข้อความเด้งมุมจอ / toast)
# เปิด-ปิดได้ในหน้าต่างตั้งค่า → หมวด "การแจ้งเตือน"  (ค่าอยู่ใน profile["prefs"])
#   price_moves()   หุ้นในหน้าหลักที่ขึ้น/ลงแรงวันนี้ (เกินเกณฑ์ % ที่ตั้งไว้) — แจ้งครั้งเดียวต่อการเข้าใช้
#   lao_updated()   แจ้งเมื่อระบบดึงข้อมูลหุ้นลาวรอบใหม่เสร็จ
#   quiz_reminder() เตือนให้ทำแบบประเมินผู้ลงทุน ถ้ายังไม่เคยทำ
# หมายเหตุ: เป็นการแจ้งเตือน "ขณะเปิดเว็บอยู่" เท่านั้น — ยังไม่มีอีเมล/แจ้งเตือนมือถือ
# =====================================================
import streamlit as st

from core.i18n import t


def _prefs() -> dict:
    return (st.session_state.get("profile") or {}).get("prefs") or {}


def _once(flag: str) -> bool:
    """True ครั้งแรกเท่านั้นในการเข้าใช้ครั้งนี้"""
    if st.session_state.get(flag):
        return False
    st.session_state[flag] = True
    return True


def price_moves(quotes: dict, symbols: list):
    p = _prefs()
    if not p.get("notify_moves") or not quotes or not _once("_nt_moves"):
        return
    limit = float(p.get("move_threshold", 3)) / 100
    big = sorted(((s, quotes[s]["chg"]) for s in symbols if s in quotes and abs(quotes[s]["chg"]) >= limit),
                 key=lambda x: -abs(x[1]))
    for sym, chg in big[:3]:
        st.toast(t("nt_toast_move").format(s=sym, arrow="▲" if chg > 0 else "▼", p=f"{chg * 100:+.2f}%"),
                 icon=":material/trending_up:" if chg > 0 else ":material/trending_down:")


def lao_updated(sync_at: float):
    """sync_at = เวลาที่ดึงข้อมูลหุ้นลาวเสร็จล่าสุด (0 = ยังไม่เคยในรอบที่เปิดเซิร์ฟเวอร์นี้)"""
    seen = st.session_state.get("_nt_lao")
    st.session_state["_nt_lao"] = sync_at
    if _prefs().get("notify_lao") and seen is not None and sync_at and sync_at != seen:
        st.toast(t("nt_toast_lao"), icon=":material/sync:")


def quiz_reminder(has_profile: bool):
    if _prefs().get("notify_quiz") and not has_profile and _once("_nt_quiz"):
        st.toast(t("nt_toast_quiz"), icon=":material/checklist:")
