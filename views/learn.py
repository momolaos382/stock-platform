# =====================================================
# learn.py — หน้า "ความรู้การลงทุน"
# แท็บ 5 หมวด + อภิธานศัพท์  แต่ละหมวดมีบทเรียนสั้น 3 บท
# เครื่องมือประกอบ:
#   หมวดพื้นฐาน         → เครื่องคิดเลขดอกเบี้ยทบต้น
#   หมวดระวังการหลอกลวง → แบบตรวจสอบสัญญาณเตือน
#   หมวดอื่น            → ปุ่มไปลองใช้หน้าจริง
# เนื้อหาทั้งหมดอยู่ใน core/learn.py
# =====================================================
import plotly.graph_objects as go
import streamlit as st

from core import learn, theme
from core.i18n import t
from core.ui import esc, goto, md, tile
from views.stock import PLOT_CFG


def _lang():
    return st.session_state.get("lang", "lo")


def _n(v) -> str:
    return f"{v:,.0f}"


# ---------- บทเรียน ----------
def _lessons(topic):
    lang = _lang()
    for i, lesson in enumerate(topic["lessons"]):
        with st.expander(f'{i + 1}. {lesson["title"][lang]}', expanded=(i == 0)):
            st.markdown(lesson["body"][lang])
            md(f'<div class="tip"><b>{t("ln_tip")}</b> {esc(lesson["tip"][lang])}</div>')


# ---------- เครื่องคิดเลขดอกเบี้ยทบต้น ----------
def _compound():
    c = theme.tokens()
    with st.container(key="card_compound"):
        md(f'<div class="card-title">{t("ln_calc_title")}</div><div class="muted">{t("ln_calc_sub")}</div>')
        c1, c2, c3, c4 = st.columns(4)
        initial = c1.number_input(t("ln_calc_initial"), min_value=0.0, value=1000.0, step=500.0, format="%.0f")
        monthly = c2.number_input(t("ln_calc_monthly"), min_value=0.0, value=100.0, step=50.0, format="%.0f")
        years = c3.slider(t("ln_calc_years"), 1, 40, 20)
        rate = c4.slider(t("ln_calc_rate"), 0.0, 15.0, 7.0, 0.5, format="%.1f%%")
        rows = learn.compound(initial, monthly, years, rate / 100)
        paid, total = rows[-1][1], rows[-1][2]

        k1, k2, k3 = st.columns(3)
        with k1, st.container(key="cardblue_cmp_total"):
            tile(t("ln_calc_final").format(y=years), _n(total), t("ln_calc_final_sub"))
        with k2, st.container(key="cardlav_cmp_paid"):
            tile(t("ln_calc_paid"), _n(paid), t("ln_calc_paid_sub"))
        with k3, st.container(key="cardmint_cmp_gain"):
            tile(t("ln_calc_gain"), _n(total - paid),
                 t("ln_calc_gain_sub").format(p=f"{(total - paid) / total * 100:.0f}" if total > 0 else "0"))

        xs = [str(r[0]) for r in rows]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=xs, y=[r[1] for r in rows], name=t("ln_calc_paid"), marker_color=c["accent"],
                             hovertemplate="%{y:,.0f}"))
        fig.add_trace(go.Bar(x=xs, y=[r[2] - r[1] for r in rows], name=t("ln_calc_gain"), marker_color=c["series2"],
                             hovertemplate="%{y:,.0f}"))
        fig.update_traces(marker_line=dict(width=1, color=c["surface2"]))
        theme.plot_layout(fig, height=320)
        fig.update_layout(barmode="stack", bargap=0.25, legend_traceorder="normal")
        fig.update_xaxes(type="category", title=dict(text=t("ln_calc_axis"), font=dict(color=c["muted"], size=12)))
        fig.update_yaxes(tickformat="~s")
        fig.update_layout(margin=dict(b=48))
        st.plotly_chart(fig, theme=None, config=PLOT_CFG, width="stretch")


# ---------- แบบตรวจสอบการหลอกลวง ----------
def _scam_check():
    lang = _lang()
    with st.container(key="card_scamcheck"):
        md(f'<div class="card-title">{t("ln_scam_title")}</div><div class="muted">{t("ln_scam_sub")}</div>')
        left, right = st.columns([3, 2])
        with left:
            hits = sum(st.checkbox(flag[lang], key=f"flag_{i}") for i, flag in enumerate(learn.RED_FLAGS))
        level = "none" if hits == 0 else "some" if hits <= 2 else "high"
        card = {"none": "cardmint", "some": "cardcream", "high": "cardcta"}[level]
        icon = {"none": "✓", "some": "!", "high": "✕"}[level]
        with right, st.container(key=f"{card}_scamresult"):
            md(f'<div class="tile"><div class="label">{t("ln_scam_count").format(n=hits, m=len(learn.RED_FLAGS))}</div>'
               f'<div class="value" style="font-size:1.35rem">{icon} {t("ln_scam_" + level)}</div>'
               f'<div class="sub" style="opacity:.9">{t("ln_scam_" + level + "_body")}</div></div>')


# ---------- อภิธานศัพท์ ----------
def _glossary():
    lang = _lang()
    q = st.text_input(t("ln_gloss_search"), placeholder=t("ln_gloss_search"), label_visibility="collapsed").strip().lower()
    rows = [(term, d[lang]) for term, d in learn.GLOSSARY
            if not q or q in term.lower() or q in d[lang].lower()]
    if not rows:
        md(f'<p class="muted">{t("ln_gloss_none")}</p>')
        return
    md('<div class="tbl-wrap"><table class="tbl gloss"><tbody>' + "".join(
        f'<tr><td><span class="sym">{esc(term)}</span></td><td>{esc(text)}</td></tr>' for term, text in rows)
       + "</tbody></table></div>")


# ---------- หน้าหลักของไฟล์นี้ ----------
def render():
    lang = _lang()
    st.title(t("page_learn"))
    md(f'<p class="muted" style="margin-top:-.4rem">{t("ln_sub")}</p>')

    labels = [f'{tp["icon"]} {tp["title"][lang]}' for tp in learn.TOPICS] + [f':material/menu_book: {t("ln_glossary")}']
    tabs = st.tabs(labels)
    for tab, topic in zip(tabs, learn.TOPICS):
        with tab:
            _lessons(topic)
            if topic["key"] == "basics":
                _compound()
            elif topic["key"] == "scam":
                _scam_check()
            elif topic["link"]:
                with st.container(key=f'cardcta_try_{topic["key"]}'):
                    md(f'<h3 style="margin:0 0 .3rem">{t("ln_try_title")}</h3>'
                       f'<p class="muted">{t("ln_try_" + topic["key"])}</p>')
                    st.button(t(topic["link"]), key=f'try_{topic["key"]}', on_click=goto, args=(topic["link"],))
    with tabs[-1]:
        _glossary()

    md(f'<p class="muted" style="margin-top:1.2rem">⚠️ {t("disclaimer")}</p>')
