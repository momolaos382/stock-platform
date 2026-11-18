# =====================================================
# home.py — หน้าหลัก (Dashboard) หลังเข้าสู่ระบบ
#   แถวบน:   คำทักทายตัวใหญ่ + การ์ดดัชนี 3 ตลาด (สหรัฐฯ / ไทย / ลาว)
#   แถวกลาง: ตัวกรองตลาด + ช่องค้นหา
#   แถวล่าง: การ์ดหุ้นเด่น 3 ตัว + ตารางหุ้นยอดนิยมของตลาดที่เลือก + การ์ดชวนเรียนรู้
# =====================================================
import streamlit as st

from core import data, lao, notify, theme
from core.i18n import t
from core.ui import change_html, esc, goto, keep, md, money, num, sparkline

INDEX_US, INDEX_TH = "^GSPC", "TDEX.BK"            # S&P 500 / กองทุนตามดัชนี SET50
BASE = {"US": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "JPM", "KO"],
        "TH": ["PTT.BK", "CPALL.BK", "KBANK.BK", "ADVANC.BK", "AOT.BK", "SCB.BK"]}
CARDS = ["cardlav", "cardmint", "cardcream"]
CURRENCY_OF = {"US": "USD", "TH": "THB", "LA": "LAK"}


def _lao_symbols():
    return [s for s in data.universe() if data.market_of(s) == "LA"]


def _symbols(market):
    """หุ้นที่จะแสดงตามตัวกรองตลาด"""
    la = _lao_symbols()
    if market == "US":
        return BASE["US"]
    if market == "TH":
        return BASE["TH"]
    if market == "LA":
        return la
    return BASE["US"][:4] + BASE["TH"][:3] + la[:3]          # ทั้งหมด = ผสม 3 ตลาด


def _search():
    with st.form("home_search", border=False):
        c1, c2 = st.columns([5, 1])
        q = c1.text_input(t("search_ph"), placeholder=t("search_ph"), label_visibility="collapsed")
        submitted = c2.form_submit_button(t("analyze"), type="primary", width="stretch")
    if submitted and q:
        sym = data.clean_symbol(q)
        if sym:
            goto("page_valuation", sym)
            st.rerun()
        else:
            st.warning(t("bad_symbol"))


def _lao_index_quote():
    s = lao.index_daily()
    if s is None or len(s) < 2:
        return None
    c = s.tail(22)
    return {"price": float(c.iloc[-1]), "chg": float(c.iloc[-1] / c.iloc[-2] - 1), "spark": [float(x) for x in c]}


def _index_card(key, label, q, spark_color, target="page_valuation", symbol=None):
    """การ์ดดัชนี: ชื่อตลาด + ตัวเลขใหญ่ + % วันนี้ + เส้นกราฟจิ๋ว"""
    with st.container(key=key):
        if q:
            md(f'<div class="tile"><div class="label">{label}</div>'
               f'<div class="value">{num(q["price"])}</div>'
               f'<div class="sub" style="font-weight:700;opacity:1">{change_html(q["chg"])} '
               f'<span class="muted">{t("today")}</span></div>'
               f'<div style="margin-top:.5rem">{sparkline(q["spark"], spark_color, h=40)}</div></div>')
        else:
            md(f'<div class="tile"><div class="label">{label}</div><div class="value">–</div></div>')


def _row_html(sym, q):
    name = data.universe().get(sym, (sym,))[0]
    cur = CURRENCY_OF[data.market_of(sym)]
    digits = 0 if cur == "LAK" else 2
    return (f'<tr><td><span class="sym">{esc(sym)}</span> <span class="co">{esc(name)}</span></td>'
            f'<td>{money(q["price"], cur, digits) if q else "–"}</td>'
            f'<td>{change_html(q["chg"] if q else None)}</td></tr>')


def render():
    c = theme.tokens()
    user = st.session_state.user
    keep("home_mkt", "ALL")

    lao_syms = _lao_symbols()
    market = st.session_state.get("home_mkt") or "ALL"
    shown = _symbols(market)
    quotes = data.load_quotes(tuple([INDEX_US, INDEX_TH] + list(dict.fromkeys(
        BASE["US"] + BASE["TH"] + lao_syms))))
    if not quotes:
        st.info(t("no_data"))
    notify.price_moves(quotes, BASE["US"] + BASE["TH"] + lao_syms)   # แจ้งเตือนหุ้นขึ้น/ลงแรง (ถ้าเปิดไว้)

    # ---------- แถวบน: คำทักทาย + การ์ดดัชนี ----------
    left, right = st.columns([2, 3])
    with left:
        md(f'<div class="hero"><div class="eyebrow">{t("welcome")}</div>'
           f'<div class="hero-name">{esc(user["username"])}</div>'
           f'<p class="muted">{t("home_sub")}</p></div>')
    with right:
        k1, k2, k3 = st.columns(3)
        with k1:
            _index_card("card_idx_us", "S&amp;P 500 · " + t("pf_market_US"), quotes.get(INDEX_US), c["accent"])
        with k2:
            _index_card("card_idx_th", "SET50 · " + t("pf_market_TH"), quotes.get(INDEX_TH), c["series2"])
        with k3:
            lq = _lao_index_quote()
            if lq:
                _index_card("cardblue_idx_la", "LSX · " + t("pf_market_LA"), lq, c["lime_ink"])
            else:
                with st.container(key="cardblue_idx_la"):
                    md(f'<div class="tile"><div class="label">LSX · {t("pf_market_LA")}</div>'
                       f'<div class="value">{len(lao_syms)}</div>'
                       f'<div class="sub">{t("la_home")}</div></div>')
                    st.button(t("page_lao"), key="home_to_lao", on_click=goto, args=("page_lao",), width="stretch")

    st.write("")

    # ---------- แถวกลาง: ตัวกรองตลาด + ค้นหา ----------
    f1, f2 = st.columns([2, 3])
    f1.segmented_control(t("pf_market"), ["ALL", "US", "TH", "LA"], key="home_mkt", label_visibility="collapsed",
                         format_func=lambda m: t("mkt_all") if m == "ALL" else t("pf_market_" + m))
    with f2:
        _search()

    # ---------- แถวล่าง ----------
    featured = shown[:3]
    col_tbl, col_side = st.columns([3, 2])
    with col_tbl:
        md(f'<h3>{t("popular")}</h3>')
        if market == "LA" and not lao_syms:
            st.info(t("la_empty"))
        body = "".join(_row_html(s, quotes.get(s)) for s in shown)
        with st.container(key="card_popular"):
            md(f'<div class="tbl-wrap"><table class="tbl"><thead><tr><th>{t("col_name")}</th><th>{t("col_price")}</th>'
               f'<th>{t("col_change")}</th></tr></thead><tbody>{body}</tbody></table></div>')
            if shown:
                st.pills(t("open_stock"), shown, key="home_pick", on_change=_pick_popular)
    with col_side:
        md(f'<h3>{t("featured")}</h3>')
        for sym, card in zip(featured, CARDS):
            q = quotes.get(sym)
            cur = CURRENCY_OF[data.market_of(sym)]
            with st.container(key=f"{card}_{sym}"):
                md(f'<div class="tile"><div class="label">{esc(data.universe().get(sym, (sym,))[0])} · {esc(sym)}</div>'
                   f'<div class="value" style="font-size:1.4rem">{money(q["price"], cur, 0 if cur == "LAK" else 2) if q else "–"}</div>'
                   f'<div class="sub" style="font-weight:700;opacity:1">{change_html(q["chg"] if q else None)}</div>'
                   f'<div style="margin:.35rem 0 .45rem">{sparkline(q["spark"], c["ink"], h=30, fill=False) if q else ""}</div></div>')
                st.button(t("view"), key=f"feat_{sym}", on_click=goto, args=("page_valuation", sym), width="stretch")
        with st.container(key="cardcta_learn"):
            md(f'<h3 style="margin:0 0 .3rem">{t("cta_title")}</h3><p class="muted">{t("cta_body")}</p>')
            st.button(t("cta_btn"), key="cta_learn", on_click=goto, args=("page_learn",))

    md(f'<p class="muted" style="margin-top:1.2rem">⚠️ {t("disclaimer")}</p>')


def _pick_popular():
    """กดเม็ดยาชื่อหุ้นใต้ตาราง → เปิดหน้าวิเคราะห์ของหุ้นนั้น"""
    if st.session_state.get("home_pick"):
        goto("page_valuation", st.session_state.home_pick)
        st.session_state.home_pick = None
