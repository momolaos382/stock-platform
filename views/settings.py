# =====================================================
# settings.py — หน้าต่าง "ตั้งค่า" (เปิดจากปุ่มฟันเฟืองในเมนูด้านข้าง)
#   เมนูซ้าย 3 หมวด:
#     บัญชี         รูปโปรไฟล์, ชื่อที่แสดง, เปลี่ยนรหัสผ่าน, ออกจากระบบ
#     การแสดงผล     ธีม (มืด/สว่าง), ภาษา, รูปแบบเมนูด้านข้าง (เต็ม/ย่อ)
#     การแจ้งเตือน   เปิด-ปิดการแจ้งเตือนในเว็บ (ดู core/notify.py)
# ค่าทั้งหมดบันทึกลงฐานข้อมูลต่อผู้ใช้ (core/auth.py: user_settings) → ล็อกอินครั้งหน้ายังอยู่
# =====================================================
import streamlit as st

from core import auth
from core.i18n import t
from core.ui import esc, keep, md

SECTIONS = ["account", "appearance", "notifications"]
ICONS = {"account": ":material/person:", "appearance": ":material/palette:",
         "notifications": ":material/notifications:"}
THRESHOLDS = [2, 3, 5, 10]


# ---------- ตัวช่วย ----------
def avatar_html(profile: dict, username: str, size: int = 40) -> str:
    """รูปโปรไฟล์วงกลม (ไม่มีรูป → ตัวอักษรแรกของชื่อ)"""
    style = f"width:{size}px;height:{size}px;font-size:{size * .42:.0f}px"
    if profile.get("avatar_uri"):
        return f'<img class="avatar" style="{style}" src="{profile["avatar_uri"]}" alt="">'
    letter = (profile.get("display_name") or username or "?").strip()[:1].upper()
    return f'<span class="avatar" style="{style}">{esc(letter)}</span>'


def _reload(uid):
    st.session_state.profile = auth.get_profile(uid)


def persist():
    """บันทึกค่าที่เลือกอยู่ตอนนี้ (ภาษา ธีม เมนู การแจ้งเตือน) ลงฐานข้อมูล"""
    user = st.session_state.get("user")
    if not user:
        return
    prefs = st.session_state.profile["prefs"]
    prefs.update(lang=st.session_state.lang_pref, dark=st.session_state.dark_pref,
                 mini=st.session_state.side_mini)
    auth.save_prefs(user["id"], prefs)


def open_settings():
    """callback ของปุ่มฟันเฟือง: เปิดหน้าต่าง + ล้างค่าตัวเลือกเก่า ให้แสดงตรงกับค่าปัจจุบัน"""
    for k in [k for k in st.session_state if k.startswith("set_") and k != "set_section"]:
        del st.session_state[k]
    st.session_state.settings_open = True


def _closed():
    st.session_state.settings_open = False


def _choice(label, key, options, current, fmt, hide_label=False):
    """ปุ่มเลือกแบบเม็ดยา (แตะง่ายบนจอสัมผัส)  คืนค่าใหม่ถ้าผู้ใช้เปลี่ยน / None ถ้าเหมือนเดิม"""
    if key not in st.session_state:
        st.session_state[key] = current
    v = st.segmented_control(label, options, key=key, format_func=fmt,
                             label_visibility="collapsed" if hide_label else "visible")
    return v if v is not None and v != current else None


# ---------- หมวด: บัญชี ----------
def _account(uid, prof):
    user = st.session_state.user
    md(f'<div class="set-title">{t("set_account")}</div>')
    c1, c2 = st.columns([1, 3])
    c1.markdown(avatar_html(prof, user["username"], 96), unsafe_allow_html=True)
    with c2:
        n = st.session_state.get("set_up_n", 0)          # เปลี่ยน key หลังอัปโหลดเสร็จ → ช่องอัปโหลดกลับมาว่าง
        up = st.file_uploader(t("set_avatar"), type=["png", "jpg", "jpeg", "webp"], key=f"set_up_{n}")
        if up is not None:
            if up.size > 5 * 1024 * 1024 or not auth.save_avatar(uid, up.getvalue()):
                st.error(t("set_img_bad"))
            else:
                _reload(uid)
                st.session_state.set_up_n = n + 1
                st.rerun()
        if prof["avatar_uri"] and st.button(t("set_avatar_remove"), key="set_rm_avatar"):
            auth.save_avatar(uid, None)
            _reload(uid)
            st.rerun()

    if "set_name" not in st.session_state:
        st.session_state.set_name = prof["display_name"]
    a, b = st.columns(2)
    name = a.text_input(t("set_display_name"), key="set_name", max_chars=40, placeholder=user["username"])
    b.text_input(t("username"), value=user["username"], disabled=True, key="set_username_ro")
    if st.button(t("set_save"), type="primary", key="set_save_name"):
        auth.save_display_name(uid, name)
        _reload(uid)
        st.toast(t("set_saved"), icon=":material/check_circle:")
        st.rerun()

    with st.expander(t("set_pw_title")):
        with st.form("set_pw_form", border=False, clear_on_submit=True):
            old = st.text_input(t("set_pw_old"), type="password")
            new = st.text_input(t("set_pw_new"), type="password")
            new2 = st.text_input(t("password2"), type="password")
            go = st.form_submit_button(t("set_pw_change"))
        if go:
            if len(new) < 6:
                st.warning(t("pw_short"))
            elif new != new2:
                st.warning(t("pw_mismatch"))
            elif auth.change_password(uid, old, new):
                st.success(t("set_pw_ok"))
            else:
                st.error(t("set_pw_bad"))

    st.divider()
    if st.button(t("logout"), key="set_logout", icon=":material/logout:"):
        st.session_state.user = None
        st.session_state.settings_open = False
        st.rerun()


# ---------- หมวด: การแสดงผล ----------
def _appearance(uid, prof):
    md(f'<div class="set-title">{t("set_appearance")}</div>')
    now = "dark" if st.session_state.dark_pref else "light"
    v = _choice(t("theme"), "set_theme", ["dark", "light"], now,
                lambda x: (":material/dark_mode: " + t("theme_dark")) if x == "dark"
                else (":material/light_mode: " + t("theme_light")))
    if v:
        st.session_state.dark_pref = v == "dark"
        persist()
        st.rerun()                       # ธีมเป็น CSS ของทั้งหน้า → ต้องวาดใหม่ทั้งแอป

    v = _choice(t("language"), "set_lang", ["ລາວ", "English"], st.session_state.lang_pref, lambda x: x)
    if v:
        st.session_state.lang_pref = v
        persist()
        st.rerun()

    now = "mini" if st.session_state.side_mini else "full"
    v = _choice(t("set_menu_style"), "set_menu", ["full", "mini"], now, lambda x: t("set_menu_" + x))
    if v:
        st.session_state.side_mini = v == "mini"
        persist()
        st.rerun()
    md(f'<p class="muted" style="margin-top:.8rem">{t("set_appearance_note")}</p>')


# ---------- หมวด: การแจ้งเตือน ----------
def _notifications(uid, prof):
    prefs = prof["prefs"]
    md(f'<div class="set-title">{t("set_notifications")}</div><p class="muted">{t("nt_note")}</p>')

    def row(key):
        c1, c2 = st.columns([3, 1.3], vertical_alignment="center")
        c1.markdown(f'<div class="set-row"><b>{t("nt_" + key)}</b><div class="muted">{t("nt_" + key + "_d")}</div></div>',
                    unsafe_allow_html=True)
        with c2:
            v = _choice(t("nt_" + key), "set_nt_" + key, ["on", "off"], "on" if prefs["notify_" + key] else "off",
                        lambda x: t("set_" + x), hide_label=True)
        if v:
            prefs["notify_" + key] = v == "on"
            auth.save_prefs(uid, prefs)

    row("moves")
    if prefs["notify_moves"]:
        v = _choice(t("nt_threshold"), "set_nt_thr", THRESHOLDS, prefs.get("move_threshold", 3), lambda x: f"±{x}%")
        if v:
            prefs["move_threshold"] = v
            auth.save_prefs(uid, prefs)
            st.session_state.pop("_nt_moves", None)       # ให้แจ้งใหม่ด้วยเกณฑ์ใหม่
    st.divider()
    row("lao")
    st.divider()
    row("quiz")


# ---------- หน้าต่างหลัก ----------
def _body():
    uid = st.session_state.user["id"]
    prof = st.session_state.profile
    nav, main = st.columns([1, 2.7])
    with nav, st.container(key="set_nav"):
        keep("set_section", "account")
        sec = st.radio("section", SECTIONS, key="set_section", label_visibility="collapsed",
                       format_func=lambda s: f"{ICONS[s]} {t('set_' + s)}")
    with main, st.container(key="set_main"):
        {"account": _account, "appearance": _appearance, "notifications": _notifications}[sec](uid, prof)


def show():
    """เรียกทุกรอบที่ settings_open เป็นจริง (ชื่อหน้าต่างแปลตามภาษา จึงสร้าง dialog ตอนเรียก)"""
    st.dialog(t("settings"), width="large", on_dismiss=_closed)(_body)()
