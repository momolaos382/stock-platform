# =====================================================
# lao.py — หน้า "ข้อมูลหุ้นลาว"
# เพิ่ม/อัปเดต/ลบหุ้นตลาดหลักทรัพย์ลาว (LSX) โดยอัปโหลดไฟล์ CSV
# (Yahoo ไม่มีข้อมูลหุ้นลาว — การอ่านไฟล์และตรวจความถูกต้องอยู่ใน core/lao.py)
# =====================================================
import streamlit as st

from core import data, lao
from core.i18n import t
from core.ui import esc, md, money

SECTORS = ["Financial Services", "Utilities", "Energy", "Industrials", "Consumer Defensive",
           "Consumer Cyclical", "Communication Services", "Real Estate", "Technology",
           "Healthcare", "Basic Materials", "Other"]


def _delete(code):
    lao.delete(code)
    st.cache_data.clear()


def _listing():
    items = lao.universe()
    with st.container(key="card_lalist"):
        md(f'<div class="card-title">{t("la_list")}</div>')
        if not items:
            md(f'<p class="muted">{t("la_none")}</p>')
            return
        body = ""
        for sym, (name, sector) in items.items():
            try:
                s = lao.daily(sym)
                last, days, when = money(float(s.iloc[-1]), "LAK", 0), len(s), s.index[-1].strftime("%Y-%m-%d")
            except Exception:
                last, days, when = "–", 0, "–"
            body += (f'<tr><td><span class="sym">{esc(sym)}</span> <span class="co">{esc(name)}</span></td>'
                     f'<td>{esc(sector)}</td><td>{last}</td><td>{days}</td><td>{when}</td></tr>')
        md(f'<div class="tbl-wrap"><table class="tbl"><thead><tr><th>{t("col_name")}</th><th>{t("la_sector")}</th>'
           f'<th>{t("col_price")}</th><th>{t("la_col_rows")}</th><th>{t("la_col_last")}</th></tr></thead>'
           f'<tbody>{body}</tbody></table></div>')
        cols = st.columns(min(len(items), 4))
        for i, sym in enumerate(items):
            cols[i % len(cols)].button(f'{t("la_delete")} {sym}', key=f"la_del_{sym}", width="stretch",
                                       on_click=_delete, args=(lao.code_of(sym),))


def _form():
    with st.container(key="card_laform"):
        md(f'<div class="card-title">{t("la_add")}</div>')
        md(f'<div class="muted" style="margin:.2rem 0 .4rem">{t("la_tpl")}</div>')
        t1, t2, t3, t4 = st.columns(4)
        t1.download_button("⬇ " + t("la_tpl_prices"), lao.template("prices"), "lsx_prices.csv", "text/csv", width="stretch")
        t2.download_button("⬇ " + t("la_tpl_fin"), lao.template("fin"), "lsx_financials.csv", "text/csv", width="stretch")
        t3.download_button("⬇ " + t("la_tpl_bs"), lao.template("bs"), "lsx_balance.csv", "text/csv", width="stretch")
        t4.download_button("⬇ " + t("la_tpl_cf"), lao.template("cf"), "lsx_cashflow.csv", "text/csv", width="stretch")

        with st.form("la_form", border=False):
            a, b, c = st.columns([1, 2, 2])
            code = a.text_input(t("la_code"), max_chars=12)
            name = b.text_input(t("la_name"))
            sector = c.selectbox(t("la_sector"), SECTORS)
            d, e, f, g = st.columns(4)
            shares = d.number_input(t("la_shares"), min_value=0.0, step=1000000.0, format="%.0f")
            eps = e.number_input(t("la_eps"), min_value=0.0, step=10.0, format="%.2f")
            bv = f.number_input(t("la_bv"), min_value=0.0, step=100.0, format="%.2f")
            div = g.number_input(t("la_div"), min_value=0.0, step=10.0, format="%.2f")
            desc = st.text_area(t("la_desc"), height=80)
            prices = st.file_uploader(t("la_prices"), type="csv")
            with st.expander(t("la_stmts")):
                u1, u2, u3 = st.columns(3)
                fin = u1.file_uploader(t("la_fin"), type="csv", key="la_up_fin")
                bs = u2.file_uploader(t("la_bs"), type="csv", key="la_up_bs")
                cf = u3.file_uploader(t("la_cf"), type="csv", key="la_up_cf")
            go = st.form_submit_button(t("la_save"), type="primary")

    if not go:
        return
    code = lao.clean_code(code)
    if not code:
        st.error(t("la_err_code"))
        return
    if not name.strip() or prices is None:
        st.error(t("la_err_need"))
        return
    try:
        df = lao.parse_prices(prices.getvalue())
    except Exception:
        st.error(t("la_err_prices"))
        return
    info = {"name": name.strip(), "sector": sector, "currency": "LAK", "description": desc.strip() or None,
            "shares": shares or None, "eps": eps or None, "book_value": bv or None, "dividend": div or None}
    lao.save(code, info, df, {"fin": fin and fin.getvalue(), "bs": bs and bs.getvalue(), "cf": cf and cf.getvalue()})
    st.cache_data.clear()
    st.toast(t("la_saved"), icon="✅")
    st.rerun()


def _index():
    with st.expander(t("la_index")):
        up = st.file_uploader(t("la_prices"), type="csv", key="la_up_index")
        if up is not None and st.button(t("la_save"), key="la_save_index"):
            try:
                lao.save_index(lao.parse_prices(up.getvalue()))
                st.cache_data.clear()
                st.success(t("la_index_ok"))
            except Exception:
                st.error(t("la_err_prices"))


def _sync_now():
    """ปุ่ม "อัปเดตตอนนี้": ดึงจาก LSX ทันที แล้วล้าง cache ให้ทุกหน้าเห็นราคาใหม่"""
    from core import lao_fundamentals
    res = lao.sync()
    try:
        fres = lao_fundamentals.sync()
        res["failed"] += [f"{c} (factsheet)" for c in fres.get("failed", [])]
    except Exception:
        res["failed"].append("Factsheet")
    st.session_state.la_sync_result = res
    st.cache_data.clear()


def render():
    st.title(t("page_lao"))
    with st.container(key="cardblue_laintro"):
        when = lao.last_sync()
        md(f'<div class="card-title" style="font-size:1.2rem">{t("la_intro_title")}</div>'
           f'<p style="margin:.4rem 0 .6rem">{t("la_intro_body")}</p>'
           f'<span class="chip">{t("la_source")}: lsx.com.la</span>'
           f'<span class="chip">{t("la_last_sync")}: {when.strftime("%Y-%m-%d %H:%M") if when else "–"}</span>')
        st.write("")
        if st.button(t("la_sync"), type="primary"):
            with st.spinner(t("la_syncing")):
                _sync_now()
    res = st.session_state.pop("la_sync_result", None)
    if res:
        if res["ok"]:
            st.success(t("la_sync_ok").format(n=len(res["ok"])))
        if res["failed"]:
            st.warning(t("la_sync_fail").format(names=", ".join(res["failed"])))
    st.write("")
    _listing()
    st.write("")
    _form()
    _index()
    md(f'<p class="muted" style="margin-top:1.2rem">{t("la_note")}</p>')
