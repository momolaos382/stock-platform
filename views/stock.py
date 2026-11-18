# =====================================================
# stock.py — หน้า "วิเคราะห์หุ้น"
# ผู้ใช้พิมพ์ชื่อย่อหุ้น → แสดง:
#   แท็บภาพรวม:   คะแนนคุณภาพ, มูลค่าที่เหมาะสม, กราฟราคาเทียบมูลค่า, 5 ปัจจัย,
#                 สัญญาณธุรกิจ, คะแนนย้อนหลัง, เทียบคู่แข่ง, ตัวเลขสำคัญ
#   แท็บงบการเงิน: กราฟรายได้/กำไร + ตารางตัวเลขรายปี
# สูตรคำนวณอยู่ใน core/valuation.py  ข้อมูลมาจาก core/data.py
# =====================================================
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import data, theme, valuation
from core.i18n import t
from core.ui import big, change_html, esc, md, money, num, ok, pct, tile
from views import company

QUICK = ["AAPL", "MSFT", "NVDA", "KO", "JPM", "PTT.BK", "CPALL.BK"]
RANGES = {"1Y": 1, "3Y": 3, "5Y": 5, "10Y": 10}
PLOT_CFG = {"displayModeBar": False}


# ---------- การเลือกหุ้น ----------
def _pick_quick():
    if st.session_state.get("quick_pick"):
        st.session_state.symbol = st.session_state.quick_pick
        st.session_state.quick_pick = None


def _pick_peer():
    if st.session_state.get("peer_pick"):
        st.session_state.symbol = st.session_state.peer_pick
        st.session_state.peer_pick = None


def search_bar(form_key="stock_search"):
    """ช่องค้นหาหุ้น + ปุ่มลัดหุ้นยอดนิยม (ใช้ร่วมกับหน้าวัดความเสี่ยง)"""
    with st.form(form_key, border=False, clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        q = c1.text_input(t("search_ph"), placeholder=t("search_ph"), label_visibility="collapsed")
        submitted = c2.form_submit_button(t("analyze"), type="primary", width="stretch")
    if submitted and q:
        sym = data.clean_symbol(q)
        if sym:
            st.session_state.symbol = sym
        else:
            st.warning(t("bad_symbol"))
    lao_quick = [s for s in data.universe() if data.market_of(s) == "LA"][:3]
    st.pills(t("popular"), QUICK + lao_quick, key="quick_pick", on_change=_pick_quick, label_visibility="collapsed")


# ---------- ส่วนหัว + การ์ดตัวเลขเด่น ----------
def header(sym, info, price, cur):
    """ส่วนหัว: ชื่อบริษัท ป้ายกลุ่มอุตสาหกรรม ราคาล่าสุด และ % เปลี่ยนแปลงวันนี้"""
    name = info.get("longName") or info.get("shortName") or sym
    prev = info.get("previousClose")
    chg = price / prev - 1 if ok(prev) and prev else None
    chips = "".join(f'<span class="chip">{esc(x)}</span>'
                    for x in (info.get("fullExchangeName"), info.get("sector"), info.get("industry")) if x)
    md(f'<div class="stock-head"><div><div class="eyebrow">{esc(sym)}</div>'
       f'<div class="name">{esc(name)}</div><div style="margin-top:.45rem">{chips}</div></div>'
       f'<div><div class="px">{money(price, cur)}</div>'
       f'<div style="text-align:right;font-weight:700;font-size:.9rem">{change_html(chg)} '
       f'<span class="muted">{t("today")}</span></div></div></div>')


def _tiles(a, cur):
    c1, c2, c3, c4 = st.columns(4)
    with c1, st.container(key="cardblue_score"):
        s = a["score"]
        tile(t("quality_score"), f'{num(s)} <small>/ 10</small>' if ok(s) else t("na"),
             t("of_10"), meter=s / 10 if ok(s) else 0)
    # ไม่มีคะแนน = ไม่มีงบการเงินเลย (เช่น หุ้นลาวที่ยังไม่กรอกงบ) / มีคะแนนแต่ไม่มีมูลค่า = กำไรติดลบ
    why = t("no_fair") if ok(a["score"]) else t("no_fin")
    with c2, st.container(key="cardlav_fair"):
        fv = a["fair"]["now"]
        tile(t("fair_value"), money(fv, cur) if ok(fv) else t("na"),
             t("per_share") if ok(fv) else why)
    with c3, st.container(key="cardmint_gap"):
        g = a["gap"]
        if ok(g):
            tile(t("price_vs_fair"), pct(abs(g), digits=0),
                 f'<b class="{"tone-bad" if g > 0 else "tone-good"}">{t("over_fair") if g > 0 else t("under_fair")}</b>')
        else:
            tile(t("price_vs_fair"), t("na"), why)
    with c4, st.container(key="cardcream_loss"):
        tile(t("loss_chance"), pct(a["loss"], digits=0) if ok(a["loss"]) else t("na"), t("loss_sub"))


# ---------- กราฟ ----------
def _price_chart(stock, a, cur):
    c = theme.tokens()
    head, pick = st.columns([3, 2])
    head.markdown(f'<div class="card-title">{t("chart_title")}</div>', unsafe_allow_html=True)
    with pick:
        rng = st.segmented_control("range", list(RANGES), default="5Y", key="rng", label_visibility="collapsed")
    years = RANGES.get(rng or "5Y", 5)
    price = stock["price"]
    start = price.index[-1] - pd.DateOffset(years=years)
    price = price[price.index >= start]

    # เส้นมูลค่าที่เหมาะสม: ค่ารายปี + จุดปัจจุบัน
    line = a["fair"]["line"]
    if ok(a["fair"]["now"]):
        line = pd.concat([line, pd.Series([a["fair"]["now"]], index=[stock["price"].index[-1]])])
    if line.empty:          # ไม่มีงบการเงิน (เช่น หุ้นลาวที่ยังไม่ได้กรอกงบ) → ไม่มีเส้นมูลค่า
        line = pd.Series(dtype=float, index=pd.DatetimeIndex([]))
    line = line[line.index >= start]
    line = line[~line.index.duplicated(keep="last")].sort_index()

    sym = "%{y:,.2f}"
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=price.index, y=price.values, name=t("price"), mode="lines",
                             line=dict(color=c["accent"], width=2), hovertemplate=sym))
    if len(line):
        fig.add_trace(go.Scatter(x=line.index, y=line.values, name=t("fair_value"), mode="lines+markers",
                                 line=dict(color=c["ink"], width=2, dash="dash"),
                                 marker=dict(size=8, color=c["ink"], line=dict(width=2, color=c["surface2"])),
                                 hovertemplate=sym))
    theme.plot_layout(fig, height=340)
    fig.update_yaxes(tickprefix=money(0, cur, 0)[:-1])
    st.plotly_chart(fig, theme=None, config=PLOT_CFG, width="stretch")


def _factors(a):
    md(f'<div class="card-title">{t("factors_title")}</div><div class="muted">{t("factors_sub")}</div>')
    rows = ""
    for k in valuation.FACTORS:
        v = a["factors"].get(k)
        val, w = (f"{v:.0f}", v) if ok(v) else (t("na"), 0)
        rows += (f'<div class="factor"><div class="row"><span>{t("f_" + k)}</span><b>{val}</b></div>'
                 f'<div class="bar"><i style="width:{w:.0f}%"></i></div></div>')
    md(rows)


def _signs(table):
    md(f'<div class="card-title">{t("signs_title")}</div>')
    icon = {"good": "✓", "neutral": "•", "bad": "✕"}
    cells = "".join(
        f'<div class="sign"><div class="k">{t(topic)}</div>'
        f'<div class="v"><span class="tone-{tone}">{icon[tone]}</span> {t(verdict)}</div></div>'
        for topic, verdict, tone in valuation.signs(table))
    md(f'<div class="signs">{cells}</div>' if cells else f'<p class="muted">{t("na")}</p>')


def _history(table):
    c = theme.tokens()
    md(f'<div class="card-title">{t("history_title")}</div>')
    hist = valuation.score_history(table)
    if not hist:
        md(f'<p class="muted">{t("na")}</p>')
        return
    years = [str(y) for y, _ in hist]
    vals = [s for _, s in hist]
    fig = go.Figure(go.Bar(x=years, y=vals, marker_color=c["accent"], width=0.45,
                           text=[f"{v:.2f}" for v in vals], textposition="outside",
                           textfont=dict(color=c["ink"], size=12), cliponaxis=False,
                           hovertemplate="%{x}: %{y:.2f} / 10<extra></extra>"))
    fig.update_traces(marker_cornerradius=4)
    theme.plot_layout(fig, height=250, legend=False)
    fig.update_layout(hovermode="closest")
    fig.update_yaxes(range=[0, 10.9], dtick=2.5)
    fig.update_xaxes(type="category")
    st.plotly_chart(fig, theme=None, config=PLOT_CFG, width="stretch")


# ---------- เทียบคู่แข่ง ----------
def _peers(sym, info, a, cur):
    md(f'<div class="card-title">{t("peers_title")}</div>')
    sector = info.get("sector")
    peers = data.peers_of(sym, sector) if sector else []
    if not peers:
        md(f'<p class="muted">{t("peers_none")}</p>')
        return
    with st.spinner(t("loading")):
        raw = data.load_many(tuple(peers))
    rows = [{"sym": sym, "name": info.get("shortName") or sym, "score": a["score"],
             "price": a["price"], "gap": a["gap"], "cur": cur, "me": True}]
    for p, d in raw.items():
        pa = valuation.analyze(d)
        rows.append({"sym": p, "name": data.universe()[p][0], "score": pa["score"], "price": pa["price"],
                     "gap": pa["gap"], "cur": d["info"].get("currency") or cur, "me": False})
    rows.sort(key=lambda r: r["score"] if ok(r["score"]) else -1, reverse=True)
    rank = next(i for i, r in enumerate(rows, 1) if r["me"])
    md(f'<p class="muted">{t("peers_rank").format(r=rank, n=len(rows), s=esc(sector))}</p>')

    body = ""
    for i, r in enumerate(rows, 1):
        gap = "–"
        if ok(r["gap"]):
            tone, arrow = ("tone-bad", "▲") if r["gap"] > 0 else ("tone-good", "▼")
            gap = f'<span class="{tone}">{arrow} {pct(abs(r["gap"]), digits=0)}</span>'
        body += (f'<tr class="{"me" if r["me"] else ""}"><td>{i}. <span class="sym">{esc(r["sym"])}</span> '
                 f'<span class="co">{esc(r["name"])}</span></td><td>{num(r["score"])}</td>'
                 f'<td>{money(r["price"], r["cur"])}</td><td>{gap}</td></tr>')
    md(f'<div class="tbl-wrap"><table class="tbl"><thead><tr><th>{t("col_name")}</th><th>{t("col_score")}</th>'
       f'<th>{t("col_price")}</th><th>{t("col_gap")}</th></tr></thead><tbody>{body}</tbody></table></div>')
    st.pills(t("peers_open"), [r["sym"] for r in rows if not r["me"]], key="peer_pick", on_change=_pick_peer)


# ---------- ตัวเลขสำคัญ ----------
def _stats(info, a, cur):
    md(f'<div class="card-title">{t("stats_title")}</div>')
    tb = a["table"]
    last = tb.iloc[-1] if len(tb) else {}
    bv, div = info.get("bookValue"), info.get("dividendRate")
    items = [
        ("st_mcap", big(info.get("marketCap"), cur)),
        ("st_pe", num(info.get("trailingPE"), 1)),
        ("st_pb", num(a["price"] / bv, 1) if ok(bv) and bv > 0 else "–"),
        ("st_eps", money(info.get("trailingEps"), cur)),
        ("st_roe", pct(last.get("roe"))),
        ("st_margin", pct(last.get("op_margin"))),
        ("st_de", num(last.get("de"))),
        ("st_div", pct(div / a["price"], digits=2) if ok(div) and a["price"] else "–"),
        ("st_beta", num(info.get("beta"))),
    ]
    md('<div class="stats" style="margin-top:.6rem">' + "".join(
        f'<div class="stat"><div class="k">{t(k)}</div><div class="v">{v}</div></div>' for k, v in items) + "</div>")


# ---------- แท็บงบการเงิน ----------
def _financials(a, info):
    tb = a["table"]
    if tb.empty:
        st.info(t("fin_none"))
        return
    c = theme.tokens()
    fcur = info.get("financialCurrency") or info.get("currency") or "USD"
    years = [str(d.year) for d in tb.index]

    with st.container(key="card_finchart"):
        md(f'<div class="card-title">{t("fin_chart")}</div>')
        # เลือกหน่วยแกนตั้งตามขนาดตัวเลข (T = ล้านล้าน, B = พันล้าน, M = ล้าน)
        peak = tb[["revenue", "net_income"]].abs().max().max()
        unit, size = next(((u, s) for u, s in (("T", 1e12), ("B", 1e9), ("M", 1e6)) if peak >= s), ("", 1))
        fig = go.Figure()
        for col, key, color in (("revenue", "r_revenue", c["accent"]), ("net_income", "r_net_income", c["series2"])):
            fig.add_trace(go.Bar(x=years, y=tb[col].values / size, name=t(key), marker_color=color,
                                 customdata=[big(v, fcur) for v in tb[col].values],
                                 hovertemplate="%{customdata}"))
        fig.update_traces(marker_cornerradius=4, marker_line=dict(width=2, color=c["surface2"]))
        theme.plot_layout(fig, height=320)
        fig.update_layout(barmode="group", bargap=0.35, bargroupgap=0.05)
        fig.update_xaxes(type="category")
        fig.update_yaxes(ticksuffix=unit)
        st.plotly_chart(fig, theme=None, config=PLOT_CFG, width="stretch")

    with st.container(key="card_fintable"):
        md(f'<div class="card-title">{t("fin_table")} <span class="muted">({esc(fcur)})</span></div>')
        fair = a["fair"]["line"].reindex(tb.index)
        spec = [
            ("r_revenue", tb["revenue"], lambda v: big(v, fcur)),
            ("r_net_income", tb["net_income"], lambda v: big(v, fcur)),
            ("r_eps", tb["eps"], lambda v: num(v)),
            ("r_op_margin", tb["op_margin"], pct),
            ("r_roe", tb["roe"], pct),
            ("r_de", tb["de"], lambda v: num(v)),
            ("r_fcf", tb["fcf"], lambda v: big(v, fcur)),
            ("r_fair", fair, lambda v: num(v)),
        ]
        head = "".join(f"<th>{y}</th>" for y in years)
        body = "".join(f'<tr><td>{t(k)}</td>' + "".join(f"<td>{fmt(v)}</td>" for v in s.values) + "</tr>"
                       for k, s, fmt in spec)
        md(f'<div class="tbl-wrap"><table class="tbl"><thead><tr><th></th>{head}</tr></thead>'
           f'<tbody>{body}</tbody></table></div>')


# ---------- หน้าหลักของไฟล์นี้ ----------
def render():
    st.session_state.setdefault("symbol", "AAPL")
    st.title(t("page_valuation"))
    search_bar()
    sym = st.session_state.symbol

    try:
        with st.spinner(t("loading")):
            stock = data.load_stock(sym)
    except Exception:
        st.error(f"{esc(sym)} — {t('not_found')}")
        return

    info = stock["info"]
    cur = info.get("currency") or "USD"
    a = valuation.analyze(stock)

    st.write("")
    header(sym, info, a["price"], cur)
    st.write("")
    _tiles(a, cur)

    tab_sum, tab_fin, tab_co, tab_news = st.tabs([t("tab_summary"), t("tab_financials"),
                                                  t("tab_company"), t("tab_news")])
    with tab_sum:
        left, right = st.columns([2, 1])
        with left, st.container(key="card_chart"):
            _price_chart(stock, a, cur)
        with right, st.container(key="card_factors"):
            _factors(a)

        left, right = st.columns([3, 2])
        with left, st.container(key="card_signs"):
            _signs(a["table"])
        with right, st.container(key="card_history"):
            _history(a["table"])

        left, right = st.columns([3, 2])
        with left, st.container(key="card_peers"):
            _peers(sym, info, a, cur)
        with right, st.container(key="card_stats"):
            _stats(info, a, cur)

        with st.expander(t("method")):
            fv = a["fair"]
            st.markdown(t("method_body").format(
                eps=num(fv["eps"]), g=num((fv["g"] or 0) * 100, 1),
                y=num(fv.get("y") or valuation.AAA_YIELD, 1), m=num(fv["multiple"], 1)))
    with tab_fin:
        seg = company.revenue_structure(sym)
        company.income_flow(stock, seg)
        _financials(a, info)
    with tab_co:
        company.company_tab(sym, info)
    with tab_news:
        company.news_tab(sym)

    source = "Lao Securities Exchange (lsx.com.la)" if data.market_of(sym) == "LA" else "Yahoo Finance"
    md(f'<p class="muted" style="margin-top:1rem">⚠️ {t("disclaimer")} · {source}</p>')
