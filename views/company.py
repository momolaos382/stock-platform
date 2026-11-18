# =====================================================
# company.py — ส่วนข้อมูลเชิงลึกของบริษัท (ใช้ในหน้า "วิเคราะห์หุ้น")
#   company_tab()  ข้อมูลบริษัท: เว็บไซต์, พนักงาน, ที่อยู่, ผู้บริหาร, ผู้ถือหุ้นรายใหญ่,
#                  ผู้บริหารที่ถือหุ้น, การซื้อขายหุ้นของผู้บริหาร
#   news_tab()     ข่าวล่าสุดที่พูดถึงหุ้นตัวนี้ (กดเปิดอ่านต้นฉบับ)
#   income_flow()  แผนภาพการไหลของงบกำไรขาดทุน (Sankey): รายได้ → ต้นทุน/ค่าใช้จ่าย → กำไรสุทธิ
# ข้อมูลมาจาก core/data.py (load_stock + load_profile) — หุ้นสหรัฐฯ ครบที่สุด
# =====================================================
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import data, theme
from core.i18n import t
from core.ui import big, esc, md, num, ok, pct

PLOT_CFG = {"displayModeBar": False}


def _url(u) -> str:
    """รับเฉพาะลิงก์ http(s) (กันลิงก์แปลกๆ จากข้อมูลภายนอก)"""
    u = str(u or "").strip()
    if u.startswith("www."):
        u = "https://" + u
    return u if u.startswith(("http://", "https://")) else ""


def _table(head: list, rows: list, align_left=1) -> str:
    """ตาราง HTML ตามสไตล์ .tbl  (คอลัมน์แรกๆ ชิดซ้ายตาม align_left)"""
    th = "".join(f'<th style="{"text-align:left" if i < align_left else ""}">{h}</th>' for i, h in enumerate(head))
    body = "".join("<tr>" + "".join(f'<td style="{"text-align:left" if i < align_left else ""}">{c}</td>'
                                    for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def _change(v) -> str:
    if not ok(v):
        return "–"
    tone, arrow = ("tone-good", "▲") if v > 0 else ("tone-bad", "▼") if v < 0 else ("tone-neutral", "")
    return f'<span class="{tone}">{arrow} {pct(abs(v), digits=2)}</span>'


# ---------- แท็บ "บริษัท" ----------
def _profile_card(sym, info):
    site, ir = _url(info.get("website")), _url(info.get("irWebsite"))
    addr = ", ".join(x for x in (info.get("address1"), info.get("city"), info.get("state"), info.get("country")) if x)
    emp = info.get("fullTimeEmployees")
    items = [
        (t("co_employees"), f"{int(emp):,}" if ok(emp) else "–"),
        (t("co_sector"), esc(info.get("sector") or "–")),
        (t("co_industry"), esc(info.get("industry") or "–")),
        (t("co_exchange"), esc(info.get("fullExchangeName") or "–")),
        (t("co_phone"), esc(info.get("phone") or "–")),
        (t("co_address"), esc(addr or "–")),
    ]
    with st.container(key="cardblue_coprofile"):
        md(f'<div class="card-title" style="font-size:1.15rem">{esc(info.get("longName") or sym)}</div>'
           + '<div class="co-grid">' + "".join(f'<div><div class="k">{k}</div><div class="v">{v}</div></div>'
                                              for k, v in items) + "</div>")
        b1, b2, _ = st.columns([1, 1, 2])
        if site:
            b1.link_button(t("co_website"), site, icon=":material/language:", width="stretch")
        if ir:
            b2.link_button(t("co_ir"), ir, icon=":material/query_stats:", width="stretch")


def _officers(info, cur):
    people = info.get("companyOfficers") or []
    with st.container(key="card_cofficers"):
        md(f'<div class="card-title">{t("co_officers")}</div>')
        if not people:
            md(f'<p class="muted">{t("co_none")}</p>')
            return
        rows = []
        for p in people[:12]:
            rows.append([f'<b>{esc(p.get("name"))}</b>', esc(p.get("title") or "–"),
                         str(p.get("age") or "–"), big(p.get("totalPay"), "USD") if ok(p.get("totalPay")) else "–"])
        md(_table([t("co_name"), t("co_title"), t("co_age"), t("co_pay")], rows, align_left=2))
        md(f'<p class="muted" style="margin-top:.4rem">{t("co_pay_note")}</p>')


def _ownership(prof):
    m = prof.get("major") or {}
    ins, inst, cnt = m.get("insidersPercentHeld"), m.get("institutionsPercentHeld"), m.get("institutionsCount")
    other = 1 - (ins or 0) - (inst or 0) if ok(ins) or ok(inst) else None
    c = theme.tokens()
    with st.container(key="card_coown"):
        md(f'<div class="card-title">{t("co_own")}</div>')
        if not m:
            md(f'<p class="muted">{t("co_none")}</p>')
            return
        parts = [(t("co_own_inst"), inst, c["accent"]), (t("co_own_ins"), ins, c["series2"]),
                 (t("co_own_other"), other, c["series3"])]
        bar = "".join(f'<i style="width:{max(v, 0) * 100:.1f}%;background:{col}" title="{lab}"></i>'
                      for lab, v, col in parts if ok(v) and v > 0)
        rows = "".join(f'<div class="alloc-row"><span class="sw" style="background:{col}"></span><span>{lab}</span>'
                       f'<b>{pct(v)}</b></div>' for lab, v, col in parts if ok(v))
        md(f'<div class="alloc-bar">{bar}</div>{rows}'
           + (f'<p class="muted" style="margin-top:.5rem">{t("co_inst_count").format(n=f"{int(cnt):,}")}</p>' if ok(cnt) else ""))


def _holders(title_key, records, cur, key):
    with st.container(key=key):
        md(f'<div class="card-title">{t(title_key)}</div>')
        if not records:
            md(f'<p class="muted">{t("co_none")}</p>')
            return
        rows = [[f'{i}. <b>{esc(r.get("Holder"))}</b>', pct(r.get("pctHeld"), digits=2),
                 big(r.get("Shares"), "").lstrip(), big(r.get("Value"), cur), _change(r.get("pctChange"))]
                for i, r in enumerate(records, 1)]
        md(_table([t("co_holder"), t("co_pct"), t("co_shares"), t("co_value"), t("co_chg")], rows))
        date = records[0].get("Date Reported")
        if date:
            md(f'<p class="muted" style="margin-top:.4rem">{t("co_reported").format(d=esc(date))}</p>')


def _insiders(prof, cur):
    roster, tx = prof.get("insiders") or [], prof.get("insider_tx") or []
    left, right = st.columns([1, 1])
    with left, st.container(key="card_coinsiders"):
        md(f'<div class="card-title">{t("co_insiders")}</div>')
        if roster:
            rows = [[f'<b>{esc(r.get("Name"))}</b><div class="co">{esc(r.get("Position") or "")}</div>',
                     big(r.get("Shares Owned Directly"), "").lstrip(), esc(r.get("Latest Transaction Date") or "–")]
                    for r in roster]
            md(_table([t("co_name"), t("co_shares"), t("co_last_tx")], rows))
        else:
            md(f'<p class="muted">{t("co_none")}</p>')
    with right, st.container(key="card_cotx"):
        md(f'<div class="card-title">{t("co_tx")}</div>')
        if tx:
            rows = []
            for r in tx[:12]:
                text = str(r.get("Text") or "")
                tone = "tone-bad" if text.lower().startswith("sale") else "tone-good" if text.lower().startswith(("purchase", "buy")) else ""
                rows.append([esc(r.get("Start Date") or r.get("Transaction Start Date") or "–"),
                             f'<b>{esc(r.get("Insider"))}</b><div class="co {tone}">{esc(text) or esc(r.get("Transaction") or "")}</div>',
                             big(r.get("Shares"), "").lstrip(), big(r.get("Value"), cur) if ok(r.get("Value")) else "–"])
            md(_table([t("co_date"), t("co_name"), t("co_shares"), t("co_value")], rows, align_left=2))
        else:
            md(f'<p class="muted">{t("co_none")}</p>')


def _lao_company(sym, info):
    """แท็บ "บริษัท" ของหุ้นลาว: โปรไฟล์จาก Factsheet ของ LSX (ที่อยู่ เว็บไซต์ กรรมการ จำนวนผู้ถือหุ้น ฯลฯ)"""
    from core import lao, lao_profile
    p = lao_profile.profile(lao.code_of(sym))
    if not p:
        st.info(t("co_la_none"))
        return
    items = [(t("co_est"), p.get("established")), (t("co_listed"), p.get("listed")), (t("co_ipo"), p.get("ipo_price")),
             (t("co_advisor"), p.get("advisor")), (t("co_phone"), p.get("phone")), (t("co_address"), p.get("address")),
             (t("co_sector"), info.get("sector"))]
    with st.container(key="cardblue_coprofile"):
        md(f'<div class="card-title" style="font-size:1.15rem">{esc(info.get("longName") or sym)}</div>'
           + '<div class="co-grid">' + "".join(f'<div><div class="k">{k}</div><div class="v">{esc(v)}</div></div>'
                                              for k, v in items if v) + "</div>")
        site = _url(p.get("website"))
        if site:
            st.link_button(t("co_website"), site, icon=":material/language:")

    def n(v, suffix=""):
        return f"{v:,.0f}{suffix}" if isinstance(v, (int, float)) else "–"

    stats = [(t("co_holders_total"), n(p.get("shareholders"))), (t("co_float"), n(p.get("free_float"), "%")),
             (t("co_foreign_limit"), n(p.get("foreign"), "%")), (t("co_listed_shares"), n(p.get("listed_shares")))]
    left, right = st.columns([3, 2])
    with left, st.container(key="card_cofficers"):
        md(f'<div class="card-title">{t("co_board")}</div>')
        board = p.get("board") or []
        if board:
            md(_table([t("co_name"), t("co_title")], [[f"<b>{esc(b['name'])}</b>", esc(b["position"])] for b in board]))
        else:
            md(f'<p class="muted">{t("co_none")}</p>')
    with right, st.container(key="card_coown"):
        md(f'<div class="card-title">{t("co_own")}</div><div class="stats" style="margin-top:.6rem">'
           + "".join(f'<div class="stat"><div class="k">{k}</div><div class="v">{v}</div></div>' for k, v in stats) + "</div>")
    if p.get("business"):
        with st.expander(t("co_business")):
            st.write(p["business"])
    md(f'<p class="muted">{t("co_la_source")}</p>')


def company_tab(sym, info):
    cur = info.get("currency") or "USD"
    if data.market_of(sym) == "LA":
        _lao_company(sym, info)
        return
    if data.market_of(sym) == "TH":
        st.caption(t("co_th_note"))
    with st.spinner(t("loading")):
        prof = data.load_profile(sym)
    _profile_card(sym, info)
    left, right = st.columns([3, 2])
    with left:
        _officers(info, cur)
    with right:
        _ownership(prof)
    left, right = st.columns([1, 1])
    with left:
        _holders("co_inst", prof.get("institutions"), cur, "card_coinst")
    with right:
        _holders("co_funds", prof.get("funds"), cur, "card_cofunds")
    _insiders(prof, cur)
    if info.get("longBusinessSummary"):
        with st.expander(t("about")):
            st.write(info["longBusinessSummary"])


# ---------- แท็บ "ข่าว" ----------
def _news_cards(items, publisher):
    html = ""
    for n in items:
        url = _url(n.get("url"))
        if url:
            html += (f'<a class="news" href="{esc(url)}" target="_blank" rel="noopener noreferrer"><div>'
                     f'<div class="nt">{esc(n["title"])}</div><div class="nm">{esc(publisher)} · {esc(n["date"])}</div></div></a>')
    md(f'<div class="news-list">{html}</div>')


def _lao_news(sym):
    """แท็บ "ข่าว" ของหุ้นลาว: ประกาศของบริษัท (ผลประกอบการ มติ ประชุมผู้ถือหุ้น ฯลฯ) + ข่าวของตลาด LSX"""
    with st.spinner(t("loading")):
        d = data.load_lao_news(sym, st.session_state.get("lang", "lo"))
    md(f'<h3 style="margin:.2rem 0 .5rem">{t("news_company")}</h3>')
    if d["company"]:
        _news_cards(d["company"], "LSX Disclosure")
    else:
        st.info(t("news_la_none"))
    md(f'<h3 style="margin:1.2rem 0 .5rem">{t("news_market")}</h3>')
    if d["market"]:
        _news_cards(d["market"], "LSX")
    md(f'<p class="muted" style="margin-top:.6rem">{t("news_la_note")}</p>')


def news_tab(sym):
    if data.market_of(sym) == "LA":
        _lao_news(sym)
        return
    if data.market_of(sym) == "TH":
        st.caption(t("co_th_note"))
    with st.spinner(t("loading")):
        items = data.load_profile(sym).get("news") or []
    if not items:
        st.info(t("news_none"))
        return
    html = ""
    for n in items:
        url = _url(n["url"])
        if not url:
            continue
        img = f'<img src="{esc(_url(n["thumb"]))}" alt="" loading="lazy">' if _url(n.get("thumb")) else ""
        html += (f'<a class="news" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{img}<div>'
                 f'<div class="nt">{esc(n["title"])}</div>'
                 f'<div class="ns">{esc(n["summary"][:220])}</div>'
                 f'<div class="nm">{esc(n["publisher"])} · {esc(n["date"])}</div></div></a>')
    md(f'<div class="news-list">{html}</div>')
    md(f'<p class="muted" style="margin-top:.6rem">{t("news_note")}</p>')


# ---------- โครงสร้างรายได้ (จาก 10-K) ----------
def _save_contact():
    from core import sec
    if sec.set_contact(st.session_state.get("sec_email", "")):
        st.session_state.pop("sec_email", None)
        data.load_segments.clear()
        st.session_state.sec_saved = True
    else:
        st.session_state.sec_bad = True


def _contact_form():
    with st.container(key="card_seccontact"):
        md(f'<div class="card-title">{t("rs_title")}</div><p class="muted" style="margin:.3rem 0 .6rem">{t("rs_need_contact")}</p>')
        c1, c2 = st.columns([3, 1])
        c1.text_input(t("rs_email"), key="sec_email", placeholder="name@example.com", label_visibility="collapsed")
        c2.button(t("la_save"), type="primary", on_click=_save_contact, width="stretch")
        if st.session_state.pop("sec_bad", False):
            st.error(t("rs_bad_email"))


def revenue_structure(sym):
    """การ์ดโครงสร้างรายได้: วงแหวน + แถบสัดส่วนแต่ละธุรกิจ (เลือกดูตามสินค้า / กลุ่มธุรกิจ / ภูมิภาค)"""
    if data.market_of(sym) != "US":
        return None
    with st.spinner(t("rs_loading")):
        seg = data.load_segments(sym)
    if seg.get("need_contact"):
        _contact_form()
        return None
    kinds = [k for k in ("product", "segment", "region") if seg.get(k)]
    if not kinds:
        return seg
    c = theme.tokens()
    palette = [c["accent"], c["series2"], c["series3"], c["series4"], c["violet"], c["muted"]]
    with st.container(key="card_revstruct"):
        h1, h2 = st.columns([3, 2])
        h1.markdown(f'<div class="card-title">{t("rs_title")}</div><div class="muted">{t("rs_sub")}</div>',
                    unsafe_allow_html=True)
        kind = h2.segmented_control("rs_kind", kinds, default=kinds[0], key=f"rs_kind_{sym}",
                                    format_func=lambda k: t("rs_" + k), label_visibility="collapsed") or kinds[0]
        year = seg[kind]["years"][-1]
        items = year["items"]
        # เกิน 6 กลุ่ม → รวมกลุ่มเล็กเป็น "อื่นๆ" (สีมีจำกัด และอ่านง่ายกว่า)
        if len(items) > 6:
            items = items[:5] + [{"name": t("rs_other"), "value": sum(i["value"] for i in items[5:])}]
        total = sum(i["value"] for i in items) or 1
        left, right = st.columns([2, 3])
        with left:
            fig = go.Figure(go.Pie(labels=[i["name"] for i in items], values=[i["value"] for i in items], hole=.62,
                                   sort=False, marker=dict(colors=palette[:len(items)], line=dict(color=c["surface2"], width=2)),
                                   textinfo="none", hovertemplate="%{label}<br>%{percent}<extra></extra>"))
            theme.plot_layout(fig, height=240, legend=False)
            fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), hovermode=False,
                              annotations=[dict(text=f"<b>{year['end'][:4]}</b>", showarrow=False,
                                                font=dict(size=18, color=c["ink"]))])
            st.plotly_chart(fig, theme=None, config=PLOT_CFG, width="stretch")
        with right:
            rows = ""
            for i, col in zip(items, palette):
                share = i["value"] / total
                rows += (f'<div class="rs-row"><div class="rs-top"><span class="sw" style="background:{col}"></span>'
                         f'<span class="nm">{esc(i["name"])}</span><b>{pct(share)}</b></div>'
                         f'<div class="rs-bar"><i style="width:{share * 100:.1f}%;background:{col}"></i></div>'
                         f'<div class="rs-amt">{big(i["value"], "USD")}</div></div>')
            md(f'<div class="rs-list">{rows}</div>')
            for d in year.get("deductions") or []:
                md(f'<p class="muted" style="margin-top:.5rem">{t("rs_deduction").format(name=esc(d["name"]), v=big(abs(d["value"]), "USD"), total=big(year["total"], "USD"))}</p>')
        # ตารางย้อนหลัง (สูงสุด 3 ปีที่มีใน 10-K)
        hist = seg[kind]["years"]
        if len(hist) > 1:
            names = [i["name"] for i in seg[kind]["years"][-1]["items"]][:8]
            head = "".join(f"<th>{y['end'][:4]}</th>" for y in hist)
            body = ""
            for n in names:
                vals = [next((x["value"] for x in y["items"] if x["name"] == n), None) for y in hist]
                body += f"<tr><td>{esc(n)}</td>" + "".join(f"<td>{big(v, 'USD') if v else '–'}</td>" for v in vals) + "</tr>"
            with st.expander(t("rs_history")):
                md(f'<div class="tbl-wrap"><table class="tbl"><thead><tr><th></th>{head}</tr></thead><tbody>{body}</tbody></table></div>')
        md(f'<p class="muted" style="margin-top:.4rem">{t("rs_source")} · '
           f'<a href="{esc(_url(seg.get("url")))}" target="_blank" rel="noopener noreferrer">10-K {esc(seg.get("report_date", ""))}</a></p>')
    return seg


# ---------- แผนภาพการไหลของงบกำไรขาดทุน ----------
def _row(fin, *names):
    for n in names:
        if n in fin.index:
            v = pd.to_numeric(fin.loc[n], errors="coerce").dropna()
            if len(v):
                return float(v.iloc[0])          # คอลัมน์แรก = ปีล่าสุด
    return None


def income_flow(stock, seg=None):
    """Sankey ปีล่าสุด: (ธุรกิจย่อย →) รายได้ → (ต้นทุนขาย | กำไรขั้นต้น) → (R&D, ขายและบริหาร, อื่นๆ | กำไรจากการดำเนินงาน)
    → (ภาษี, รายการนอกการดำเนินงาน | กำไรสุทธิ)   — แสดงเฉพาะกระแสที่เป็นบวก
    seg = โครงสร้างรายได้จาก 10-K (ถ้าเป็นปีเดียวกันและผลรวมตรงกับรายได้ จะแสดงเป็นแหล่งรายได้ทางซ้าย)"""
    fin = stock.get("fin")
    if fin is None or fin.empty:
        return
    c = theme.tokens()
    cur = stock["info"].get("financialCurrency") or stock["info"].get("currency") or "USD"
    rev = _row(fin, "Total Revenue", "Operating Revenue")
    cogs = _row(fin, "Cost Of Revenue", "Reconciled Cost Of Revenue")
    gross = _row(fin, "Gross Profit")
    rnd = _row(fin, "Research And Development")
    sga = _row(fin, "Selling General And Administration")
    opex = _row(fin, "Operating Expense")
    op = _row(fin, "Operating Income", "EBIT")
    pretax = _row(fin, "Pretax Income")
    tax = _row(fin, "Tax Provision")
    ni = _row(fin, "Net Income", "Net Income Common Stockholders")
    if not ok(rev) or rev <= 0 or not ok(ni):
        return
    year = fin.columns[0].year if hasattr(fin.columns[0], "year") else ""

    nodes, links = [], []
    good, bad, neutral = c["good"], c["bad"], c["accent"]

    def node(label, value, color):
        nodes.append((f"{label}<br>{big(value, cur)}", color))
        return len(nodes) - 1

    def link(a, b, v, color):
        if ok(v) and v > 0:
            links.append((a, b, v, color))

    # แหล่งรายได้ (ธุรกิจย่อย) ไหลเข้า "รายได้" — ใช้เมื่อปีบัญชีตรงกันและผลรวมต่างจากรายได้ไม่เกิน 3%
    sources = []
    for kind in ("product", "segment"):
        yrs = ((seg or {}).get(kind) or {}).get("years") or []
        if yrs and str(year) == yrs[-1]["end"][:4]:
            items = yrs[-1]["items"]
            if abs(sum(i["value"] for i in items) - rev) <= rev * 0.03:
                if len(items) > 6:
                    items = items[:5] + [{"name": t("rs_other"), "value": sum(i["value"] for i in items[5:])}]
                sources = items
                break
    src_nodes = [(node(s["name"], s["value"], c["series2"]), s["value"]) for s in sources]
    n_rev = node(t("fl_revenue"), rev, neutral)
    for n_src, v in src_nodes:
        link(n_src, n_rev, v, c["series2"])
    if ok(gross) and ok(cogs) and gross > 0:
        n_cogs = node(t("fl_cogs"), cogs, bad)
        n_gross = node(t("fl_gross"), gross, good)
        link(n_rev, n_cogs, cogs, bad)
        link(n_rev, n_gross, gross, good)
        top = n_gross
        if ok(op) and op > 0:
            other = (opex if ok(opex) else gross - op) - (rnd or 0) - (sga or 0)
            if ok(rnd) and rnd > 0:
                link(top, node(t("fl_rnd"), rnd, bad), rnd, bad)
            if ok(sga) and sga > 0:
                link(top, node(t("fl_sga"), sga, bad), sga, bad)
            if other > rev * 0.002:
                link(top, node(t("fl_other_opex"), other, bad), other, bad)
            n_op = node(t("fl_op"), op, good)
            link(top, n_op, op, good)
            top_val = op
        else:
            top_val, n_op = gross, top
    else:
        # ธนาคาร/ธุรกิจที่ไม่มี "ต้นทุนขาย" → รายได้ไหลไปค่าใช้จ่ายรวม กับกำไรก่อนภาษี
        n_op, top_val = n_rev, rev
    if ok(pretax) and pretax > 0:
        n_pre = node(t("fl_pretax"), pretax, good)
        if pretax <= top_val:
            link(n_op, n_pre, pretax, good)
            gap = top_val - pretax
            if gap > rev * 0.002:
                link(n_op, node(t("fl_nonop_exp") if n_op != n_rev else t("fl_expenses"), gap, bad), gap, bad)
        else:
            link(n_op, n_pre, top_val, good)
            n_extra = node(t("fl_nonop_inc"), pretax - top_val, neutral)
            link(n_extra, n_pre, pretax - top_val, good)
        if ok(tax) and tax > 0:
            link(n_pre, node(t("fl_tax"), tax, bad), tax, bad)
        if ni > 0:
            link(n_pre, node(t("fl_net"), ni, good), min(ni, pretax), good)
    if len(links) < 2:
        return

    def rgba(hex_color, a):
        h = hex_color.lstrip("#")
        return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(label=[n[0] for n in nodes], color=[n[1] for n in nodes], pad=22, thickness=16,
                  line=dict(width=0), hovertemplate="%{label}<extra></extra>"),
        link=dict(source=[l[0] for l in links], target=[l[1] for l in links], value=[l[2] for l in links],
                  color=[rgba(l[3], .32) for l in links], hovertemplate="%{value:,.0f}<extra></extra>"),
        textfont=dict(color=c["ink"], size=12, family=theme.FONT_PLOTLY),
    ))
    theme.plot_layout(fig, height=420, legend=False)
    fig.update_layout(hovermode=False, margin=dict(l=8, r=8, t=8, b=8))
    with st.container(key="card_finflow"):
        md(f'<div class="card-title">{t("fl_title")} <span class="muted">({year} · {esc(cur)})</span></div>'
           f'<div class="muted">{t("fl_sub")}</div>')
        st.plotly_chart(fig, theme=None, config=PLOT_CFG, width="stretch")
