# =====================================================
# login.py — หน้าเข้าสู่ระบบ และ สมัครสมาชิก
# =====================================================
import streamlit as st
from core import auth
from core.i18n import t
from core.ui import md


def render():
    # จัดฟอร์มไว้กลางหน้า (คอลัมน์ซ้าย-ขวาเป็นช่องว่าง)
    _, mid, _ = st.columns([1, 1.6, 1])
    with mid:
        md(f'<div class="eyebrow">Stock Platform</div>')
        st.title(t("app_title"))
        md(f'<p class="muted" style="margin-top:-.3rem">{t("login_sub")}</p>')

        # แบ่งเป็น 2 แท็บ: เข้าสู่ระบบ / สมัครสมาชิก
        tab_login, tab_register = st.tabs([t("login"), t("register")])

        # ---------- แท็บเข้าสู่ระบบ ----------
        with tab_login:
            with st.form("login_form", border=False):
                username = st.text_input(t("username"))
                password = st.text_input(t("password"), type="password")
                submitted = st.form_submit_button(t("login"), type="primary", width="stretch")
            if submitted:
                user = auth.login(username, password)
                if user:
                    st.session_state.user = user   # จำผู้ใช้ไว้ในเซสชัน
                    st.rerun()                     # โหลดหน้าใหม่ → เข้าหน้าหลัก
                else:
                    st.error(t("login_fail"))

        # ---------- แท็บสมัครสมาชิก ----------
        with tab_register:
            with st.form("register_form", border=False):
                new_user = st.text_input(t("username"), key="reg_user")
                new_pw = st.text_input(t("password"), type="password", key="reg_pw")
                new_pw2 = st.text_input(t("password2"), type="password", key="reg_pw2")
                submitted = st.form_submit_button(t("register"), type="primary", width="stretch")
            if submitted:
                # ตรวจข้อมูลก่อนบันทึก
                if not new_user or not new_pw:
                    st.warning(t("fill_all"))
                elif len(new_pw) < 6:
                    st.warning(t("pw_short"))
                elif new_pw != new_pw2:
                    st.warning(t("pw_mismatch"))
                elif auth.register(new_user, new_pw):
                    st.success(t("register_ok"))
                else:
                    st.error(t("user_exists"))

        md(f'<p class="muted" style="margin-top:1rem">⚠️ {t("disclaimer")}</p>')
