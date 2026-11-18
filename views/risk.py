# =====================================================
# risk.py — หน้า "วัดความเสี่ยง"
# ผู้ใช้เลือกหุ้น + ช่วงเวลา → แสดง:
#   การ์ดตัวเลขเด่น: ความผันผวน, Beta, VaR 95%, ขาดทุนสูงสุด (Max Drawdown)
#   กราฟ: เงิน 100 โตเป็นเท่าไรเทียบตลาด, ระยะห่างจากจุดสูงสุด, การกระจายของผลตอบแทนรายวัน
#   เครื่องคิดเลข: ถ้าลงทุนเท่านี้ วันที่แย่อาจขาดทุนเท่าไร
# สูตรคำนวณอยู่ใน core/risk.py
# =====================================================
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from core import data, risk, theme
from core.i18n import t
from core.ui import md, money, num, ok, pct, tile
from views.stock import PLOT_CFG, header, search_bar

RANGES = {"1Y": 1, "3Y": 3, "5Y": 5}


# ---------- การ์ดตัวเลขเด่น ----------
def _tiles(a, bench_name):
    tone = {"low": "tone-good", "mid": "tone-neutral", "high": "tone-bad"}[a["level"]]
    icon = {"low": "▼", "mid": "●", "high": "▲"}[a["level"]]
    c1, c2, c3, c4 = st.columns(4)
    with c1, st.container(key="cardblue_vol"):
        tile(t("rk_vol"), pct(a["vol"], digits=0) + f' <small>{t("rk_per_year")}</small>',
             f'<b class="{tone}">{icon} {t("rk_level_" + a["level"])}</b>', meter=min(a["vol"] / 0.6, 1))
    with c2, st.container(key="cardlav_beta"):
        if ok(a["beta"]):
            tile("Beta", num(a["beta"]), t("rk_beta_sub").format(b=bench_name))
        else:
            tile("Beta", t("na"), t("rk_no_bench"))
    with c3, st.container(key="cardmint_var"):
        tile(t("rk_var"), pct(a["var"]), t("rk_var_sub"))
    with c4, st.container(key="cardcream_mdd"):
        tile(t("rk_mdd"), pct(abs(a["mdd"]), digits=0),
             f'{a["mdd_peak"]:%b %Y} → {a["mdd_trough"]:%b %Y}')


# ---------- กราฟ ----------
def _growth_chart(a, sym, bench_name):
    c = theme.tokens()
    md(f'<div class="card-title">{t("rk_growth_title")}</div><div class="muted">{t("rk_growth_sub")}</div>')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=a["growth"].index, y=a["growth"].values, name=sym, mode="lines",
                             line=dict(color=c["accent"], width=2), hovertemplate="%{y:,.1f}"))
    if len(a["growth_bench"]):
        fig.add_trace(go.Scatter(x=a["growth_bench"].index, y=a["growth_bench"].values, name=bench_name,
                                 mode="lines", line=dict(color=c["series2"], width=2), hovertemplate="%{y:,.1f}"))
    fig.add_hline(y=100, line=dict(color=c["muted"], width=1, dash="dot"))
    theme.plot_layout(fig, height=320)
    st.plotly_chart(fig, theme=None, config=PLOT_CFG, width="stretch")


def _drawdown_chart(a):
    c = theme.tokens()
    md(f'<div class="card-title">{t("rk_dd_title")}</div><div class="muted">{t("rk_dd_sub")}</div>')
    dd = a["drawdown"] * 100
    fig = go.Figure(go.Scatter(x=dd.index, y=dd.values, mode="lines", fill="tozeroy",
                               line=dict(color=c["accent"], width=2), fillcolor=_alpha(c["accent"], 0.18),
                               hovertemplate="%{y:.1f}%<extra></extra>"))
    # ชี้จุดที่ตกลึกที่สุด
    fig.add_trace(go.Scatter(x=[a["mdd_trough"]], y=[a["mdd"] * 100], mode="markers+text",
                             marker=dict(size=9, color=c["ink"], line=dict(width=2, color=c["surface2"])),
                             text=[pct(a["mdd"], digits=0)], textposition="bottom center",
                             textfont=dict(color=c["ink"], size=12), hoverinfo="skip"))
    theme.plot_layout(fig, height=280, legend=False)
    fig.update_yaxes(ticksuffix="%", range=[min(dd.min() * 1.25, -5), 2])
    st.plotly_chart(fig, theme=None, config=PLOT_CFG, width="stretch")


def _hist_chart(a):
    c = theme.tokens()
    md(f'<div class="card-title">{t("rk_hist_title")}</div><div class="muted">{t("rk_hist_sub")}</div>')
    r = a["returns"] * 100
    lim = max(abs(np.percentile(r, 0.5)), abs(np.percentile(r, 99.5)))   # ตัดหางสุดขั้วออกจากแกน
    fig = go.Figure(go.Histogram(x=r.values, xbins=dict(start=-lim, end=lim, size=lim / 20),
                                 marker=dict(color=c["accent"], line=dict(width=1, color=c["surface2"])),
                                 hovertemplate="%{x}%: %{y}<extra></extra>"))
    fig.add_vline(x=-a["var"] * 100, line=dict(color=c["ink"], width=2, dash="dash"),
                  annotation_text=f'VaR 95%  −{a["var"] * 100:.1f}%', annotation_position="top left",
                  annotation_font=dict(color=c["ink"], size=12))
    theme.plot_layout(fig, height=280, legend=False)
    fig.update_layout(hovermode="closest", bargap=0.06)
    fig.update_xaxes(ticksuffix="%", range=[-lim, lim])
    st.plotly_chart(fig, theme=None, config=PLOT_CFG, width="stretch")


def _alpha(hex_color, a):
    """แปลงสี #RRGGBB เป็น rgba() แบบโปร่งแสง"""
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


# ---------- เครื่องคิดเลขการขาดทุน ----------
def _calculator(a, cur):
    md(f'<div class="card-title">{t("rk_calc_title")}</div>')
    amount = st.number_input(f'{t("rk_calc_amount")} ({cur})', min_value=0.0, value=10000.0, step=1000.0, format="%.0f")
    day = amount * a["var"]
    month = amount * a["var"] * np.sqrt(21)       # ขยายจาก 1 วันเป็น 1 เดือน (≈21 วันทำการ) ด้วยกฎ √เวลา
    worst = amount * abs(a["mdd"])
    rows = [("rk_calc_day", day), ("rk_calc_month", month), ("rk_calc_worst", worst)]
    md('<div class="stats" style="grid-template-columns:1fr;margin-top:.4rem">' + "".join(
        f'<div class="stat"><div class="k">{t(k)}</div><div class="v">−{money(v, cur, 0)}</div></div>'
        for k, v in rows) + "</div>")


# ---------- ตัวเลขเพิ่มเติม ----------
def _stats(a, bench_name):
    md(f'<div class="card-title">{t("rk_stats_title")}</div>')
    items = [
        ("rk_s_return", pct(a["ann_return"], signed=True)),
        ("rk_s_bench", f'{pct(a["bench_return"], signed=True)} <span class="muted">{bench_name}</span>'),
        ("rk_s_sharpe", num(a["sharpe"])),
        ("rk_s_corr", num(a["corr"])),
        ("rk_s_cvar", pct(a["cvar"])),
        ("rk_s_downside", pct(a["downside"], digits=0)),
        ("rk_s_best", pct(a["best"], signed=True)),
        ("rk_s_worst", pct(a["worst"], signed=True)),
        ("rk_s_up", pct(a["up_days"], digits=0)),
    ]
    md('<div class="stats" style="margin-top:.6rem">' + "".join(
        f'<div class="stat"><div class="k">{t(k)}</div><div class="v">{v}</div></div>' for k, v in items) + "</div>")


# ---------- หน้าหลักของไฟล์นี้ ----------
def render():
    st.session_state.setdefault("symbol", "AAPL")
    st.title(t("page_risk"))
    search_bar("risk_search")
    sym = st.session_state.symbol

    try:
        with st.spinner(t("loading")):
            daily = data.load_daily(sym)
    except Exception:
        st.error(f"{sym} — {t('not_found')}")
        return
    try:
        info = data.load_stock(sym)["info"]       # ชื่อบริษัท + สกุลเงิน (ใช้ cache ร่วมกับหน้าวิเคราะห์)
    except Exception:
        info = {}
    cur = info.get("currency") or {"TH": "THB", "LA": "LAK"}.get(data.market_of(sym), "USD")
    bench_name = data.benchmark_of(sym)[1]

    st.write("")
    header(sym, info, float(daily["stock"].iloc[-1]), cur)
    st.write("")
    rng = st.segmented_control(t("rk_period"), list(RANGES), default="3Y", key="risk_rng")
    a = risk.analyze(daily, RANGES.get(rng or "3Y", 3))
    if not a:
        st.info(t("rk_short"))
        return

    _tiles(a, bench_name)
    st.write("")

    left, right = st.columns([2, 1])
    with left, st.container(key="card_growth"):
        _growth_chart(a, sym, bench_name)
    with right, st.container(key="card_calc"):
        _calculator(a, cur)

    left, right = st.columns(2)
    with left, st.container(key="card_dd"):
        _drawdown_chart(a)
    with right, st.container(key="card_hist"):
        _hist_chart(a)

    with st.container(key="card_riskstats"):
        _stats(a, bench_name)

    with st.expander(t("method")):
        st.markdown(t("rk_method").format(days=a["days"], b=bench_name, rf=num(risk.RISK_FREE * 100, 0)))
    md(f'<p class="muted" style="margin-top:1rem">⚠️ {t("disclaimer")} · Yahoo Finance</p>')
