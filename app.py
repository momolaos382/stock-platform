# =====================================================
# app.py — ไฟล์หลักของแพลตฟอร์ม (เริ่มทำงานที่ไฟล์นี้)
# วิธีรัน:  streamlit run app.py   หรือดับเบิลคลิก run.bat
#
# โครงสร้างโปรเจกต์:
#   app.py          ← ไฟล์นี้: ตั้งค่า, แถบเมนู, สลับหน้า
#   core/           ← ระบบเบื้องหลัง
#       i18n.py       ข้อความ 2 ภาษา        theme.py      สี + CSS (ระบบดีไซน์)
#       auth.py       ระบบสมาชิก            ui.py         ชิ้นส่วนหน้าจอที่ใช้ซ้ำ
#       data.py       ดึงข้อมูลหุ้น          valuation.py  สูตรคำนวณ
#   views/          ← แต่ละหน้าของเว็บ (1 ไฟล์ = 1 หน้า)
#   data/app.db     ← ฐานข้อมูล (สร้างอัตโนมัติ)
# =====================================================
import streamlit as st

from core import auth, data, notify, quiz as quiz_core, theme
from core.i18n import t
from core.ui import PAGE_ORDER, esc, keep, md
from views import home, lao, learn, login, portfolio, quiz, risk, settings, stock

# ---------- 1) ตั้งค่าหน้าเว็บ (ต้องเป็นคำสั่ง Streamlit แรกสุด) ----------
st.set_page_config(page_title="Stock Platform", page_icon="📈", layout="wide")

# ---------- 2) เตรียมฐานข้อมูล + ค่าเริ่มต้น ----------
auth.init_db()
st.session_state.setdefault("user", None)         # ยังไม่ได้เข้าสู่ระบบ
# ค่าที่ผู้ใช้เลือก เก็บแยกจากตัวเลือก (widget) — เพราะโหมดเมนูย่อจะไม่วาดตัวเลือกพวกนี้
# และ Streamlit จะลบค่าของตัวเลือกที่ไม่ได้วาดทิ้ง
st.session_state.setdefault("lang_pref", "ລາວ")    # ภาษาเริ่มต้น = ลาว
st.session_state.setdefault("dark_pref", True)     # ธีมเริ่มต้น = มืด
st.session_state.setdefault("side_mini", False)    # เมนูด้านซ้าย: False = เต็ม, True = ย่อเหลือไอคอน
# เพิ่งเข้าสู่ระบบ → โหลดโปรไฟล์ + ค่าที่ผู้ใช้เคยตั้งไว้ (ภาษา ธีม รูปแบบเมนู การแจ้งเตือน) จากฐานข้อมูล
_user = st.session_state.user
if _user and st.session_state.get("_profile_uid") != _user["id"]:
    st.session_state.profile = auth.get_profile(_user["id"])
    _p = st.session_state.profile["prefs"]
    if "lang" in _p:
        st.session_state.lang_pref = _p["lang"]
    if "dark" in _p:
        st.session_state.dark_pref = bool(_p["dark"])
    if "mini" in _p:
        st.session_state.side_mini = bool(_p["mini"])
    st.session_state._profile_uid = _user["id"]
    for _k in ("_nt_moves", "_nt_quiz", "_nt_lao"):          # เริ่มนับการแจ้งเตือนใหม่ทุกครั้งที่เข้าสู่ระบบ
        st.session_state.pop(_k, None)
st.session_state.lang = "lo" if st.session_state.lang_pref == "ລາວ" else "en"
st.session_state.theme = "dark" if st.session_state.dark_pref else "light"
theme.apply(st.session_state.theme, mini=st.session_state.side_mini,
            login=st.session_state.user is None)          # หน้า login: ไม่มีเมนูด้านข้าง

# ---------- 3) รายการหน้า: (คีย์ชื่อหน้า, ไอคอน, ฟังก์ชันแสดงหน้า) ----------
# เพิ่มหน้าใหม่: สร้างไฟล์ใน views/ แล้วเพิ่มบรรทัดที่นี่ + ชื่อหน้าใน core/ui.py (PAGE_ORDER)
# (views/placeholder.py คือหน้า "กำลังพัฒนา" ไว้ใช้ชั่วคราวระหว่างทำหน้าใหม่)
RENDER = {
    "page_home": (":material/dashboard:", home.render),
    "page_valuation": (":material/monitoring:", stock.render),
    "page_risk": (":material/shield:", risk.render),
    "page_quiz": (":material/checklist:", quiz.render),
    "page_portfolio": (":material/pie_chart:", portfolio.render),
    "page_lao": (":material/database:", lao.render),
    "page_learn": (":material/school:", learn.render),
}


# ---------- callback ของเมนูด้านซ้าย / หน้า login ----------
def _toggle_side():
    st.session_state.side_mini = not st.session_state.side_mini
    settings.persist()


def _flip_lang():
    st.session_state.lang_pref = "English" if st.session_state.lang_pref == "ລາວ" else "ລາວ"


def _flip_dark():
    st.session_state.dark_pref = not st.session_state.dark_pref


# ---------- 4) แถบเมนูด้านข้าง ----------
mini = st.session_state.side_mini
# ---------- 4a) หน้า login: ไม่มีเมนูด้านข้าง มีแค่ปุ่มกลม 2 ปุ่มมุมขวาบน (ภาษา / ธีม) ----------
if st.session_state.user is None:
    with st.container(key="login_tools", horizontal=True):
        st.button("EN" if st.session_state.lang == "lo" else "ລາວ", key="login_lang", on_click=_flip_lang,
                  help=t("language"))
        st.button(":material/light_mode:" if st.session_state.dark_pref else ":material/dark_mode:",
                  key="login_dark", on_click=_flip_dark, help=t("dark_mode"))
    login.render()
    st.stop()

# ---------- 4b) เข้าสู่ระบบแล้ว: เมนูด้านข้าง ----------
with st.sidebar:
    md(f'<div class="brand"><div class="mark">SP</div><div class="brand-text"><div class="name">Stock Platform</div>'
       f'<div class="tag">{t("brand_tag")}</div></div></div>')
    # ถ้ามีปุ่มในหน้าไหนสั่งให้สลับหน้า (ui.goto) → ตั้งค่าเมนูก่อนวาด
    if "_goto" in st.session_state:
        st.session_state["nav"] = st.session_state.pop("_goto")
    keep("nav", 0)   # จำหน้าที่เปิดอยู่ไว้ แม้สลับภาษา
    choice = st.radio(
        t("menu"), range(len(PAGE_ORDER)), key="nav",
        format_func=lambda i: f"{RENDER[PAGE_ORDER[i]][0]} {t(PAGE_ORDER[i])}",
        label_visibility="collapsed",
    )
    # ส่วนล่างของเมนู (CSS ดันไปชิดล่างสุด): ผู้ใช้ + ปุ่มฟันเฟือง "ตั้งค่า" + ปุ่มย่อ/ขยายเมนู
    # ภาษา / ธีม / บัญชี / การแจ้งเตือน / ออกจากระบบ อยู่ในหน้าต่างตั้งค่า (views/settings.py)
    with st.container(key="side_toggle_wrap"):
        prof, uname = st.session_state.profile, st.session_state.user["username"]
        if mini:
            st.button(":material/settings:", key="side_gear", on_click=settings.open_settings, help=t("settings"))
            st.button(":material/keyboard_double_arrow_right:", key="side_toggle", on_click=_toggle_side,
                      help=t("side_expand"))
        else:
            with st.container(key="side_user", horizontal=True, vertical_alignment="center"):
                md(f'<div class="user-chip">{settings.avatar_html(prof, uname, 38)}<div class="who">'
                   f'<div class="nm">{esc(prof["display_name"] or uname)}</div><div class="un">@{esc(uname)}</div></div></div>')
                st.button(":material/settings:", key="side_gear", on_click=settings.open_settings, help=t("settings"))
            st.button(f':material/keyboard_double_arrow_left: {t("side_collapse")}', key="side_toggle",
                      on_click=_toggle_side, width="stretch")

# หน้าต่างตั้งค่า (เปิดค้างไว้จนกว่าผู้ใช้จะปิด — เปลี่ยนธีม/ภาษาแล้วหน้าเว็บวาดใหม่ หน้าต่างยังอยู่)
if st.session_state.get("settings_open"):
    settings.show()

# ---------- 5) อัปเดตราคาหุ้นลาวจากเว็บ LSX เบื้องหลัง (ทุก 6 ชั่วโมง) แล้วแสดงหน้าที่เลือก ----------
data.refresh_lao()
RENDER[PAGE_ORDER[choice]][1]()

# ---------- 6) การแจ้งเตือนในเว็บ (เปิด-ปิดได้ในตั้งค่า) ----------
notify.lao_updated(data.lao_sync_at())
notify.quiz_reminder(quiz_core.load(st.session_state.user["id"]) is not None)
