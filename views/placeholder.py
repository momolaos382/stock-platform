# =====================================================
# placeholder.py — หน้าชั่วคราว สำหรับหน้าที่ยังไม่ได้ทำ
# เมื่อทำหน้าจริงเสร็จ จะเปลี่ยนใน app.py ให้เรียกไฟล์หน้านั้นแทน
# =====================================================
import streamlit as st
from core.i18n import t


def render(title_key: str):
    st.title(t(title_key))
    st.info(t("coming_soon"))
