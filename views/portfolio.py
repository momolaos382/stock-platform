# =====================================================
# portfolio.py — หน้า "จัดสรรพอร์ต"
# ผู้ใช้เลือก: ตลาด, หุ้น 2–10 ตัว, จำนวนเงิน, วิธีจัดน้ำหนัก, ระดับความเสี่ยง
# หน้าจอแสดง:
#   1) แบ่งเงินตามประเภทสินทรัพย์ ตามระดับความเสี่ยง (จากแบบประเมิน)
#   2) แบ่งส่วน "หุ้น" ให้หุ้นแต่ละตัว ตามวิธีที่เลือก
#   3) แผนที่ความเสี่ยง–ผลตอบแทน + เทียบ 3 วิธี
#   4) บันทึก / เปิด / ลบ พอร์ตที่เคยจัดไว้
# สูตรอยู่ใน core/portfolio.py  ระดับความเสี่ยงและสัดส่วนอยู่ใน core/quiz.py
# =====================================================
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from core import data, portfolio as pf, quiz, theme
from core.i18n import t
from core.ui import esc, goto, keep, md, money, num, pct, tile
from views.stock import PLOT_CFG

MARKETS = {"US": "USD", "TH": "THB", "LA": "LAK"}
DEFAULTS = {"US": ["AAPL", "MSFT", "KO", "JNJ", "JPM"],
            "TH": ["PTT.BK", "CPALL.BK", "KBANK.BK", "ADVANC.BK", "AOT.BK"]}


def _lang():
    return st.session_state.get("lang", "lo")


def _options(market):
    return [s for s in data.universe() if data.market_of(s) == market]


def _default_symbols(market):
    """หุ้นเริ่มต้นของตลาด (หุ้นลาวใช้ตัวที่มีข้อมูลในเครื่อง 5 ตัวแรก)"""
    return DEFAULTS[market] if market in DEFAULTS else _options(market)[:5]


# ---------- callback ----------
def _market_changed():
    """เปลี่ยนตลาด → เปลี่ยนรายการหุ้นเริ่มต้นให้ตรงตลาด"""
    st.session_state.pf_symbols = list(_default_symbols(st.session_state.pf_market or "US"))


def _load_saved(d):
    """เปิดพอร์ตที่บันทึกไว้ → ใส่ค่ากลับเข้าตัวเลือกทั้งหมด"""
    st.session_state.pf_market = d["market"]
    st.session_state.pf_symbols = [s for s in d["symbols"] if s in data.universe()]
    st.session_state.pf_amount = float(d["amount"])
    st.session_state.pf_method = d["method"]
    st.session_state.pf_level = int(d["level"])


def _delete_saved(pid):
    pf.delete(st.session_state.user["id"], pid)


# ---------- ส่วนตั้งค่า ----------
def _controls(profile):
    left, right = st.columns([3, 2])
    with left, st.container(key="card_pfset"):
        md(f'<div class="card-title">{t("pf_setup")}</div>')
        c1, c2 = st.columns([1, 1])
        c1.segmented_control(t("pf_market"), list(MARKETS), key="pf_market", on_change=_market_changed,
                             format_func=lambda m: t("pf_market_" + m))
        market = st.session_state.pf_market or "US"
        c2.number_input(f'{t("rk_calc_amount")} ({MARKETS[market]})', min_value=0.0, step=1000.0,
                        format="%.0f", key="pf_amount")
        st.multiselect(t("pf_stocks").format(n=pf.MAX_STOCKS), _options(market), key="pf_symbols",
                       max_selections=pf.MAX_STOCKS,
                       format_func=lambda s: f"{s} · {data.universe()[s][0]}")
        if market == "LA" and not _options("LA"):
            st.info(t("la_empty"))
        st.segmented_control(t("pf_method"), pf.METHODS, key="pf_method",
                             format_func=lambda m: t("pf_m_" + m))
    with right, st.container(key="cardlav_pflevel"):
        level = st.session_state.pf_level or 3
        info = quiz.LEVELS[level - 1]
        source = (t("pf_from_quiz").format(i=profile["level"]) if profile else t("pf_no_quiz"))
        md(f'<div class="tile"><div class="label">{t("pf_level")}</div>'
           f'<div class="value" style="font-size:1.35rem">{esc(info["name"][_lang()])}</div>'
           f'<div class="sub" style="opacity:.85">{esc(info["desc"][_lang()])}</div></div>')
        st.segmented_control(t("pf_level_pick"), [1, 2, 3, 4, 5], key="pf_level")
        md(f'<div class="muted">{source}</div>')
        if not profile:
            st.button(t("pf_do_quiz"), on_click=goto, args=("page_quiz",))
    return market, st.session_state.pf_level or 3


# ---------- 1) แบ่งตามประเภทสินทรัพย์ ----------
def _asset_mix(info, amount, cur):
    c = theme.tokens()
    colors = [c["accent"], c["series2"], c["series3"], c["series4"]]
    bar = rows = ""
    for (_, name), share, color in zip(quiz.ASSETS, info["mix"], colors):
        label = esc(name[_lang()])
        if share > 0:
            bar += f'<i style="width:{share}%;background:{color}" title="{label}: {share}%"></i>'
        rows += (f'<div class="alloc-row"><span class="sw" style="background:{color}"></span><span>{label}</span>'
                 f'<span class="amt">{money(amount * share / 100, cur, 0)}</span><b>{share}%</b></div>')
    md(f'<div class="card-title">{t("pf_mix_title")}</div><div class="muted">{t("qz_alloc_sub")}</div>'
       f'<div class="alloc-bar">{bar}</div>{rows}')


# ---------- 2) แบ่งส่วนหุ้นให้แต่ละตัว ----------
def _weights_table(symbols, w, last, stock_amount, stock_share, cur):
    md(f'<div class="card-title">{t("pf_w_title")}</div><div class="muted">{t("pf_w_sub").format(m=money(stock_amount, cur, 0))}</div>')
    body = ""
    for i in np.argsort(-w):
        sym, wi = symbols[i], float(w[i])
        amt = stock_amount * wi
        shares = int(amt // last[sym]) if last[sym] > 0 else 0
        body += (f'<tr><td><span class="sym">{esc(sym)}</span> <span class="co">{esc(data.universe().get(sym, (sym,))[0])}</span>'
                 f'<div class="factor" style="margin:.25rem 0 0"><div class="bar" style="height:5px">'
                 f'<i style="width:{wi * 100:.0f}%"></i></div></div></td>'
                 f'<td>{pct(wi)}</td><td>{pct(wi * stock_share / 100)}</td>'
                 f'<td>{money(amt, cur, 0)}</td><td>{shares:,}</td></tr>')
    md(f'<div class="tbl-wrap"><table class="tbl"><thead><tr><th>{t("col_name")}</th><th>{t("pf_c_w")}</th>'
       f'<th>{t("pf_c_total")}</th><th>{t("pf_c_amt")}</th><th>{t("pf_c_shares")}</th></tr></thead>'
       f'<tbody>{body}</tbody></table></div>')


# ---------- 3) แผนที่ความเสี่ยง–ผลตอบแทน ----------
def _risk_map(symbols, mu, cov, results, method):
    c = theme.tokens()
    md(f'<div class="card-title">{t("pf_map_title")}</div><div class="muted">{t("pf_map_sub")}</div>')
    vols, rets = pf.cloud(mu, cov)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=vols * 100, y=rets * 100, mode="markers", name=t("pf_map_random"),
                             marker=dict(size=4, color=c["muted"], opacity=0.28), hoverinfo="skip"))
    # หุ้นแต่ละตัว (ถือตัวเดียว 100%)
    sd = np.sqrt(np.diag(cov))
    fig.add_trace(go.Scatter(x=sd * 100, y=mu * 100, mode="markers+text", name=t("pf_map_single"),
                             text=symbols, textposition="top center", textfont=dict(color=c["muted"], size=11),
                             marker=dict(size=8, color=c["ink"], symbol="circle-open", line=dict(width=2)),
                             hovertemplate="%{text}<br>" + t("rk_vol") + " %{x:.1f}%<br>" + t("pf_ret") + " %{y:.1f}%<extra></extra>"))
    shapes = {"equal": "circle", "minvol": "diamond", "sharpe": "square"}
    colors = {"equal": c["accent"], "minvol": c["series2"], "sharpe": c["series3"]}
    for m in pf.METHODS:
        s = results[m]["stats"]
        fig.add_trace(go.Scatter(x=[s["vol"] * 100], y=[s["ret"] * 100], mode="markers", name=t("pf_m_" + m),
                                 marker=dict(size=18 if m == method else 12, color=colors[m], symbol=shapes[m],
                                             line=dict(width=2, color=c["surface2"])),
                                 hovertemplate=t("pf_m_" + m) + "<br>" + t("rk_vol") + " %{x:.1f}%<br>" + t("pf_ret") + " %{y:.1f}%<extra></extra>"))
    theme.plot_layout(fig, height=380)
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(ticksuffix="%", title=dict(text=t("pf_axis_x"), font=dict(color=c["muted"], size=12)), showgrid=True, gridcolor=c["border"])
    fig.update_yaxes(ticksuffix="%", title=dict(text=t("pf_axis_y"), font=dict(color=c["muted"], size=12)))
    fig.update_layout(margin=dict(l=66, b=48))
    st.plotly_chart(fig, theme=None, config=PLOT_CFG, width="stretch")


def _compare(results, method):
    md(f'<div class="card-title">{t("pf_cmp_title")}</div>')
    body = "".join(
        f'<tr class="{"me" if m == method else ""}"><td>{t("pf_m_" + m)}</td><td>{pct(results[m]["stats"]["ret"])}</td>'
        f'<td>{pct(results[m]["stats"]["vol"])}</td><td>{num(results[m]["stats"]["sharpe"])}</td></tr>'
        for m in pf.METHODS)
    md(f'<div class="tbl-wrap"><table class="tbl"><thead><tr><th>{t("pf_method")}</th><th>{t("pf_ret")}</th>'
       f'<th>{t("rk_vol")}</th><th>Sharpe</th></tr></thead><tbody>{body}</tbody></table></div>'
       f'<p class="muted" style="margin-top:.7rem">{t("pf_cmp_note")}</p>')


# ---------- 4) บันทึก / เปิด / ลบ ----------
def _saved(user_id, current):
    with st.container(key="card_pfsave"):
        md(f'<div class="card-title">{t("pf_save_title")}</div>')
        with st.form("pf_save", border=False, clear_on_submit=True):
            c1, c2 = st.columns([4, 1])
            name = c1.text_input(t("pf_save_name"), placeholder=t("pf_save_name"), label_visibility="collapsed", max_chars=60)
            if c2.form_submit_button(t("pf_save_btn"), type="primary", width="stretch"):
                if name.strip():
                    pf.save(user_id, name, current)
                    st.toast(t("pf_saved_ok"))
                else:
                    st.warning(t("pf_save_need_name"))
        saved = pf.list_saved(user_id)
        if not saved:
            md(f'<p class="muted">{t("pf_saved_none")}</p>')
        for row in saved:
            d = row["data"]
            c1, c2, c3 = st.columns([6, 1, 1])
            c1.markdown(
                f'<div class="sign"><div class="v">{esc(row["name"])}</div><div class="k">{row["created_at"][:10]} · '
                f'{t("pf_level")} {d.get("level")} · {t("pf_m_" + d.get("method", "equal"))} · '
                f'{esc(", ".join(d.get("symbols", [])))}</div></div>', unsafe_allow_html=True)
            c2.button(t("pf_open"), key=f"pf_open_{row['id']}", on_click=_load_saved, args=(d,), width="stretch")
            c3.button(t("pf_delete"), key=f"pf_del_{row['id']}", on_click=_delete_saved, args=(row["id"],), width="stretch")


# ---------- หน้าหลักของไฟล์นี้ ----------
def render():
    user_id = st.session_state.user["id"]
    profile = quiz.load(user_id)
    # ค่าเริ่มต้นของตัวเลือก (ตั้งครั้งแรกครั้งเดียว)
    # keep() = ตั้งค่าเริ่มต้นครั้งแรก และจำค่าที่เลือกไว้เมื่อสลับภาษา/สลับหน้า
    keep("pf_market", "US")
    keep("pf_symbols", list(DEFAULTS["US"]))
    keep("pf_amount", 10000.0)
    keep("pf_method", "sharpe")
    keep("pf_level", profile["level"] if profile else 3)

    st.title(t("page_portfolio"))
    market, level = _controls(profile)
    cur = MARKETS[market]
    amount = float(st.session_state.pf_amount or 0)
    method = st.session_state.pf_method or "sharpe"
    picked = list(st.session_state.pf_symbols)
    info = quiz.LEVELS[level - 1]
    stock_share = info["mix"][2]                    # % ของพอร์ตที่เป็นหุ้น
    stock_amount = amount * stock_share / 100

    if len(picked) < 2:
        st.info(t("pf_need_two"))
        return
    with st.spinner(t("loading")):
        prices = data.load_prices(tuple(sorted(picked)))
    symbols = list(prices.columns)
    if len(symbols) < 2:
        st.error(t("no_data"))
        return
    missing = [s for s in picked if s not in symbols]
    if missing:
        st.warning(t("pf_missing").format(s=", ".join(missing)))

    mu, cov = pf.prepare(prices)
    results = {}
    for m in pf.METHODS:
        w = pf.optimize(mu, cov, m)
        results[m] = {"w": w, "stats": pf.stats(w, mu, cov)}
    w, s = results[method]["w"], results[method]["stats"]
    last = prices.iloc[-1]

    st.write("")
    c1, c2, c3, c4 = st.columns(4)
    with c1, st.container(key="cardblue_pfamt"):
        tile(t("pf_t_stock"), money(stock_amount, cur, 0), t("pf_t_stock_sub").format(p=stock_share, a=money(amount, cur, 0)),
             meter=stock_share / 100)
    with c2, st.container(key="cardmint_pfret"):
        tile(t("pf_t_ret"), pct(s["ret"]), t("pf_t_ret_sub"))
    with c3, st.container(key="cardcream_pfvol"):
        tile(t("pf_t_vol"), pct(s["vol"]), t("pf_t_vol_sub"))
    with c4, st.container(key="cardlav_pfsharpe"):
        tile("Sharpe", num(s["sharpe"]), t("pf_t_sharpe_sub"))
    st.write("")

    left, right = st.columns([2, 3])
    with left, st.container(key="card_pfmix"):
        _asset_mix(info, amount, cur)
    with right, st.container(key="card_pfweights"):
        _weights_table(symbols, w, last, stock_amount, stock_share, cur)

    left, right = st.columns([3, 2])
    with left, st.container(key="card_pfmap"):
        _risk_map(symbols, mu, cov, results, method)
    with right, st.container(key="card_pfcmp"):
        _compare(results, method)

    _saved(user_id, {"market": market, "symbols": symbols, "amount": amount, "method": method, "level": level,
                     "weights": {sym: round(float(x), 4) for sym, x in zip(symbols, w)}})

    with st.expander(t("method")):
        st.markdown(t("pf_method_body").format(days=len(prices), cap=int(pf.MAX_WEIGHT * 100)))
    md(f'<p class="muted" style="margin-top:1rem">⚠️ {t("disclaimer")} · Yahoo Finance</p>')
