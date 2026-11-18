# =====================================================
# valuation.py — สูตรคำนวณทั้งหมดของหน้า "วิเคราะห์หุ้น"
#   build_table()  → ตารางตัวเลขงบการเงินรายปี (1 แถว = 1 ปีบัญชี)
#   score()        → คะแนนคุณภาพธุรกิจ 0–10 จาก 5 ปัจจัย
#   fair_value()   → มูลค่าที่เหมาะสม (สูตร Benjamin Graham ฉบับปรับปรุง)
#   loss_chance()  → โอกาสขาดทุนถ้าถือ 1 ปี (จากสถิติย้อนหลัง)
#   signs()        → สัญญาณธุรกิจ สรุปเป็นข้อความสั้น
# ทุกสูตรใช้ข้อมูลจริงจากงบการเงิน ไม่มีการสุ่มหรือเดาค่า
# =====================================================
import numpy as np
import pandas as pd

AAA_YIELD = 5.0   # อัตราผลตอบแทนพันธบัตรบริษัทเกรด AAA (%) — สมมติฐาน ปรับได้
# อัตราผลตอบแทนอ้างอิงตามสกุลเงินของหุ้น (ดอกเบี้ยเงินกีบสูงกว่าดอลลาร์มาก ถ้าใช้ 5% กับหุ้นลาว มูลค่าจะสูงเกินจริง)
# 10% = ค่าประมาณระดับดอกเบี้ยนโยบาย/พันธบัตรเงินกีบช่วงปี 2024–2026 — เป็นสมมติฐาน ปรับได้
YIELD_BY_CURRENCY = {"LAK": 10.0}


def yield_for(info: dict) -> float:
    return YIELD_BY_CURRENCY.get((info or {}).get("currency"), AAA_YIELD)
MAX_GROWTH = 0.15  # จำกัดอัตราเติบโตที่ใช้ประเมินมูลค่าไว้ไม่เกิน 15% ต่อปี (กันมองโลกแง่ดีเกินไป)

FACTORS = ["growth", "recent", "strength", "shareholder", "moat"]


# ---------- เครื่องมือช่วย ----------
def _row(df, *names) -> pd.Series:
    """หยิบ 1 บรรทัดจากงบการเงิน (ลองหลายชื่อ เผื่อบางบริษัทใช้ชื่อบรรทัดต่างกัน)"""
    if df is not None and not df.empty:
        for n in names:
            if n in df.index:
                return pd.to_numeric(df.loc[n], errors="coerce")
    return pd.Series(dtype=float)


def _scale(x, lo, hi):
    """แปลงค่า x เป็นคะแนน 0–100 (x ≤ lo ได้ 0, x ≥ hi ได้ 100) / ถ้า lo > hi = ยิ่งน้อยยิ่งดี"""
    if x is None or not np.isfinite(x):
        return np.nan
    return float(np.clip((x - lo) / (hi - lo), 0, 1) * 100)


def _avg(values):
    """ค่าเฉลี่ยโดยข้ามค่าที่ไม่มีข้อมูล → None ถ้าไม่มีข้อมูลเลย"""
    v = [x for x in values if x is not None and np.isfinite(x)]
    return float(np.mean(v)) if v else None


def _last(s: pd.Series, back: int = 1):
    s = s.dropna()
    return float(s.iloc[-back]) if len(s) >= back else np.nan


def cagr(s: pd.Series):
    """อัตราเติบโตเฉลี่ยทบต้นต่อปี (CAGR) จากค่าแรกถึงค่าสุดท้าย"""
    s = s.dropna()
    if len(s) < 2 or s.iloc[0] <= 0:
        return np.nan
    if s.iloc[-1] <= 0:
        return -1.0
    years = (s.index[-1] - s.index[0]).days / 365.25
    return float((s.iloc[-1] / s.iloc[0]) ** (1 / years) - 1) if years > 0 else np.nan


# ---------- 1) ตารางงบการเงินรายปี ----------
def build_table(stock: dict) -> pd.DataFrame:
    fin, bs, cf, price = stock["fin"], stock["bs"], stock["cf"], stock["price"]
    t = pd.DataFrame({
        "revenue": _row(fin, "Total Revenue", "Operating Revenue"),
        "net_income": _row(fin, "Net Income", "Net Income Common Stockholders"),
        "eps": _row(fin, "Diluted EPS", "Basic EPS"),
        "op_income": _row(fin, "Operating Income", "EBIT"),
        "ebit": _row(fin, "EBIT", "Operating Income"),
        "interest": _row(fin, "Interest Expense"),
        "shares": _row(fin, "Diluted Average Shares", "Basic Average Shares"),
        "equity": _row(bs, "Stockholders Equity", "Common Stock Equity"),
        "debt": _row(bs, "Total Debt"),
        "cur_assets": _row(bs, "Current Assets"),
        "cur_liab": _row(bs, "Current Liabilities"),
        "op_cf": _row(cf, "Operating Cash Flow"),
        "capex": _row(cf, "Capital Expenditure").abs(),
        "fcf": _row(cf, "Free Cash Flow"),
        "dividends": _row(cf, "Cash Dividends Paid", "Common Stock Dividend Paid").abs(),
        "buyback": _row(cf, "Repurchase Of Capital Stock").abs(),
    })
    if t.empty:
        return t
    t.index = pd.to_datetime(t.index)
    t = t.sort_index()
    t = t[t["revenue"].notna()]                       # ตัดปีที่ไม่มีข้อมูลรายได้
    if t.empty:
        return t
    # อัตราส่วนทางการเงิน
    t["op_margin"] = t["op_income"] / t["revenue"]    # อัตรากำไรจากการดำเนินงาน
    t["net_margin"] = t["net_income"] / t["revenue"]  # อัตรากำไรสุทธิ
    t["roe"] = (t["net_income"] / t["equity"]).where(t["equity"] > 0)   # ผลตอบแทนผู้ถือหุ้น
    t["de"] = (t["debt"] / t["equity"]).where(t["equity"] > 0)          # หนี้สินต่อทุน
    t["cur_ratio"] = t["cur_assets"] / t["cur_liab"]  # สภาพคล่อง
    t["rev_g"] = t["revenue"].pct_change()            # รายได้โตจากปีก่อน
    t["eps_g"] = t["eps"].diff() / t["eps"].shift().abs()
    # ราคาหุ้น ณ วันสิ้นปีบัญชี → มูลค่าตลาด ณ ตอนนั้น
    t["price"] = [price.asof(d) if d >= price.index[0] else np.nan for d in t.index]
    t["mcap"] = t["price"] * t["shares"]
    return t


# ---------- 2) คะแนนคุณภาพธุรกิจ ----------
def score(t: pd.DataFrame) -> dict:
    """คืนค่า {"score": 0–10, "factors": {ชื่อปัจจัย: 0–100 หรือ None}}
    คะแนนรวม = ค่าเฉลี่ยของ 5 ปัจจัย ÷ 10"""
    if t is None or len(t) < 2:
        return {"score": None, "factors": {k: None for k in FACTORS}}

    # (1) โอกาสเติบโต: รายได้และกำไรต่อหุ้นโตเฉลี่ยกี่ % ต่อปี
    growth = _avg([_scale(cagr(t["revenue"]), 0, 0.20), _scale(cagr(t["eps"]), 0, 0.25)])

    # (2) ผลงานล่าสุด: ปีล่าสุดเทียบปีก่อน
    margin_change = _last(t["op_margin"]) - _last(t["op_margin"], 2)
    recent = _avg([_scale(_last(t["rev_g"]), -0.05, 0.20),
                   _scale(_last(t["eps_g"]), -0.10, 0.30),
                   _scale(margin_change, -0.03, 0.03)])

    # (3) ความแข็งแกร่งทางการเงิน: หนี้น้อย สภาพคล่องดี จ่ายดอกเบี้ยไหว มีเงินสดเหลือ
    interest = _last(t["interest"])
    coverage = _last(t["ebit"]) / interest if np.isfinite(interest) and interest > 0 else np.nan
    strength = _avg([_scale(_last(t["de"]), 2.5, 0.3),
                     _scale(_last(t["cur_ratio"]), 0.6, 2.0),
                     _scale(coverage, 1.5, 15),
                     _scale(_last(t["fcf"]) / _last(t["revenue"]), 0, 0.20)])

    # (4) ผลตอบแทนคืนผู้ถือหุ้น: ปันผล + ซื้อหุ้นคืน และจำนวนหุ้นลดลง
    payout = t["dividends"].fillna(0) + t["buyback"].fillna(0)
    sh = t["shares"].dropna()
    share_shrink = np.nan
    if len(sh) >= 2 and sh.iloc[-1] > 0:
        yrs = (sh.index[-1] - sh.index[0]).days / 365.25
        share_shrink = (sh.iloc[0] / sh.iloc[-1]) ** (1 / yrs) - 1 if yrs > 0 else np.nan
    div_years = (t["dividends"].fillna(0) > 0).mean() * 100   # จ่ายปันผลกี่ % ของจำนวนปี
    shareholder = _avg([_scale(_last(payout) / _last(t["mcap"]), 0, 0.06),
                        _scale(share_shrink, -0.02, 0.03),
                        div_years])

    # (5) ความได้เปรียบในการแข่งขัน: กำไรสูงและสม่ำเสมอ
    om = t["op_margin"].dropna()
    stability = 1 - om.std() / abs(om.mean()) if len(om) >= 2 and om.mean() != 0 else np.nan
    moat = _avg([_scale(t["roe"].mean(), 0.05, 0.30),
                 _scale(om.mean() if len(om) else np.nan, 0.05, 0.30),
                 _scale(stability, 0.5, 0.95)])

    factors = dict(zip(FACTORS, [growth, recent, strength, shareholder, moat]))
    total = _avg(list(factors.values()))
    return {"score": round(total / 10, 2) if total is not None else None, "factors": factors}


def score_history(t: pd.DataFrame) -> list:
    """คะแนนย้อนหลังรายปี: คำนวณซ้ำโดยใช้ข้อมูลเท่าที่มี ณ สิ้นปีนั้น → [(ปี, คะแนน)]"""
    out = []
    for i in range(2, len(t) + 1):
        s = score(t.iloc[:i])["score"]
        if s is not None:
            out.append((t.index[i - 1].year, s))
    return out


# ---------- 3) มูลค่าที่เหมาะสม ----------
def fair_value(t: pd.DataFrame, info: dict) -> dict:
    """สูตร Graham ฉบับปรับปรุง:   V = EPS × (8.5 + 2g) × 4.4 / Y
         EPS = กำไรต่อหุ้น,  g = อัตราเติบโตที่คาด (% ต่อปี),  Y = ผลตอบแทนพันธบัตร AAA (%)
       8.5 คือ P/E ของธุรกิจที่ไม่เติบโต, 4.4 คือผลตอบแทนพันธบัตรในยุคของ Graham
    คืนค่า: now = มูลค่าปัจจุบัน, line = มูลค่ารายปี (ไว้ลากเป็นเส้นในกราฟ)"""
    empty = {"now": None, "line": pd.Series(dtype=float), "g": None, "multiple": None, "eps": None}
    if t is None or t.empty:
        return empty
    g = _avg([cagr(t["revenue"]), cagr(t["eps"])])
    g = float(np.clip(g if g is not None else 0.0, 0.0, MAX_GROWTH))
    y = yield_for(info)
    multiple = (8.5 + 2 * g * 100) * 4.4 / y

    eps_hist = t["eps"].copy()
    eps_last = _last(eps_hist)
    eps_now = info.get("trailingEps")
    eps_now = float(eps_now) if eps_now is not None and np.isfinite(eps_now) else eps_last
    # ถ้างบรายงานคนละสกุลเงินกับราคาหุ้น (เช่น ADR) → ปรับสเกล EPS ย้อนหลังให้เข้ากับ EPS ปัจจุบัน
    if info.get("financialCurrency") and info.get("currency") and info["financialCurrency"] != info["currency"]:
        if np.isfinite(eps_last) and eps_last > 0 and eps_now > 0:
            eps_hist = eps_hist * (eps_now / eps_last)

    line = (eps_hist.where(eps_hist > 0) * multiple).dropna()
    now = eps_now * multiple if np.isfinite(eps_now) and eps_now > 0 else None
    return {"now": now, "line": line, "g": g, "multiple": multiple, "eps": eps_now, "y": y}


# ---------- 4) โอกาสขาดทุน ----------
def loss_chance(price: pd.Series):
    """จากราคารายเดือนย้อนหลัง: ถ้าซื้อแล้วถือ 12 เดือน มีกี่ % ของช่วงเวลาที่ขาดทุน"""
    r = price.pct_change(12).dropna()
    return float((r < 0).mean()) if len(r) >= 24 else None


# ---------- 5) สัญญาณธุรกิจ ----------
def signs(t: pd.DataFrame) -> list:
    """คืนรายการ (หัวข้อ, ผลสรุป, โทน)  โทน = good / neutral / bad
    หัวข้อและผลสรุปเป็น "คีย์" ไว้แปลภาษาใน i18n.py"""
    out = []
    if t is None or len(t) < 2:
        return out
    n = min(3, len(t) - 1)   # ดูย้อนหลังสูงสุด 3 ปี

    def add(topic, verdict, tone):
        out.append((topic, verdict, tone))

    rg, eg = t["rev_g"].dropna().tail(n), t["eps_g"].dropna().tail(n)
    if len(rg) and len(eg):
        if (rg > 0).all() and (eg > 0).all():
            add("sg_growth", "sv_growth_consistent", "good")
        elif (rg < 0).all() or (eg < 0).all():
            add("sg_growth", "sv_growth_decline", "bad")
        else:
            add("sg_growth", "sv_growth_mixed", "neutral")

    om = t["op_margin"].dropna()
    if len(om) >= 2:
        d = om.iloc[-1] - om.iloc[-min(len(om), n + 1)]
        add("sg_margin", *(("sv_margin_up", "good") if d > 0.01 else
                           ("sv_margin_down", "bad") if d < -0.01 else ("sv_margin_flat", "neutral")))

    de = _last(t["de"])
    if np.isfinite(de):
        add("sg_debt", *(("sv_debt_low", "good") if de < 0.5 else
                         ("sv_debt_high", "bad") if de > 1.5 else ("sv_debt_mid", "neutral")))
    elif _last(t["equity"]) <= 0:
        add("sg_debt", "sv_debt_high", "bad")

    roe = t["roe"].dropna().tail(n + 1)
    if len(roe):
        add("sg_roe", *(("sv_roe_high", "good") if (roe > 0.15).all() else
                        ("sv_roe_low", "bad") if roe.iloc[-1] < 0.08 else ("sv_roe_mid", "neutral")))

    div = t["dividends"].fillna(0)
    if (div > 0).all() and (div.diff().dropna() > 0).all():
        add("sg_div", "sv_div_up", "good")
    elif div.iloc[-1] > 0:
        add("sg_div", "sv_div_pay", "neutral")
    else:
        add("sg_div", "sv_div_none", "neutral")

    bb = t["buyback"].fillna(0)
    add("sg_buyback", *(("sv_bb_every", "good") if (bb > 0).all() else
                        ("sv_bb_some", "neutral") if (bb > 0).any() else ("sv_bb_none", "neutral")))

    capex_ratio = _last(t["capex"]) / _last(t["op_cf"]) if _last(t["op_cf"]) > 0 else np.nan
    if np.isfinite(capex_ratio):
        add("sg_capex", *(("sv_capex_low", "good") if capex_ratio < 0.25 else
                          ("sv_capex_high", "bad") if capex_ratio > 0.7 else ("sv_capex_mid", "neutral")))

    fcf = t["fcf"].dropna()
    if len(fcf):
        add("sg_fcf", *(("sv_fcf_pos", "good") if (fcf > 0).all() else
                        ("sv_fcf_neg", "bad") if fcf.iloc[-1] < 0 else ("sv_fcf_mixed", "neutral")))
    return out


# ---------- รวมทุกอย่างสำหรับหุ้น 1 ตัว ----------
def analyze(stock: dict) -> dict:
    info, price = stock["info"], stock["price"]
    t = build_table(stock)
    sc = score(t)
    fv = fair_value(t, info)
    last_price = info.get("currentPrice") or float(price.iloc[-1])
    gap = last_price / fv["now"] - 1 if fv["now"] else None   # + = แพงกว่ามูลค่า, − = ถูกกว่า
    return {"table": t, "score": sc["score"], "factors": sc["factors"], "fair": fv,
            "price": last_price, "gap": gap, "loss": loss_chance(price)}
