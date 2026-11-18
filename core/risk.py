# =====================================================
# risk.py — สูตรคำนวณของหน้า "วัดความเสี่ยง"
# ใช้ราคาปิดรายวันย้อนหลัง → ผลตอบแทนรายวัน → ตัวชี้วัดความเสี่ยง:
#   ความผันผวน (Volatility)   หุ้นแกว่งแรงแค่ไหนต่อปี
#   Beta                      หุ้นขยับกี่เท่าของตลาด
#   VaR / CVaR                ในวันที่แย่ อาจขาดทุนเท่าไร
#   Max Drawdown              เคยตกจากจุดสูงสุดลึกที่สุดเท่าไร
#   Sharpe Ratio              ผลตอบแทนที่ได้ต่อความเสี่ยง 1 หน่วย
# =====================================================
import numpy as np
import pandas as pd

TRADING_DAYS = 252    # จำนวนวันซื้อขายใน 1 ปี (ใช้แปลงค่ารายวันเป็นรายปี)
RISK_FREE = 0.04      # ผลตอบแทนปลอดความเสี่ยงต่อปี (สมมติฐาน ใช้คิด Sharpe) — ปรับได้
VAR_LEVEL = 0.95      # ระดับความเชื่อมั่นของ VaR

# เกณฑ์แบ่งระดับความเสี่ยงจากความผันผวนต่อปี
LOW_VOL, HIGH_VOL = 0.20, 0.35


def analyze(df: pd.DataFrame, years: int) -> dict:
    """df = ตารางราคา (คอลัมน์ stock, bench)   years = ดูย้อนหลังกี่ปี
    คืนค่าตัวชี้วัดทั้งหมด + ชุดข้อมูลสำหรับวาดกราฟ"""
    start = df.index[-1] - pd.DateOffset(years=years)
    df = df[df.index >= start]
    px = df["stock"].dropna()
    r = px.pct_change().dropna()                  # ผลตอบแทนรายวัน
    if len(r) < 30:
        return {}

    span_years = (px.index[-1] - px.index[0]).days / 365.25
    ann_return = (px.iloc[-1] / px.iloc[0]) ** (1 / span_years) - 1 if span_years > 0 else np.nan
    vol = r.std() * np.sqrt(TRADING_DAYS)         # ความผันผวนต่อปี = ส่วนเบี่ยงเบนมาตรฐานรายวัน × √252

    # VaR แบบ Historical: ดูวันที่แย่ที่สุด 5% ในอดีต → ขาดทุนอย่างน้อยเท่าไร
    var = -np.percentile(r, (1 - VAR_LEVEL) * 100)
    tail = r[r <= -var]
    cvar = -tail.mean() if len(tail) else np.nan  # CVaR = ค่าเฉลี่ยของการขาดทุนในวันที่แย่กว่า VaR

    # Drawdown = ราคาปัจจุบันต่ำกว่าจุดสูงสุดก่อนหน้ากี่ %
    dd = px / px.cummax() - 1
    trough = dd.idxmin()
    peak = px[:trough].idxmax()

    downside = r[r < 0].std() * np.sqrt(TRADING_DAYS)   # ความผันผวนเฉพาะขาลง
    sharpe = (ann_return - RISK_FREE) / vol if vol > 0 else np.nan

    # Beta = ความแปรปรวนร่วมกับตลาด ÷ ความแปรปรวนของตลาด
    beta = corr = bench_return = bench_vol = np.nan
    growth_bench = pd.Series(dtype=float)
    both = df.dropna()
    if len(both) > 30:
        rb = both.pct_change().dropna()
        if rb["bench"].var() > 0:
            beta = rb["stock"].cov(rb["bench"]) / rb["bench"].var()
            corr = rb["stock"].corr(rb["bench"])
        b = both["bench"]
        bench_vol = rb["bench"].std() * np.sqrt(TRADING_DAYS)
        bench_return = (b.iloc[-1] / b.iloc[0]) ** (1 / span_years) - 1 if span_years > 0 else np.nan
        growth_bench = b / b.iloc[0] * 100

    level = "low" if vol < LOW_VOL else "high" if vol > HIGH_VOL else "mid"
    return {
        "vol": float(vol), "level": level, "ann_return": float(ann_return),
        "var": float(var), "cvar": float(cvar),
        "mdd": float(dd.min()), "mdd_peak": peak, "mdd_trough": trough,
        "downside": float(downside), "sharpe": float(sharpe),
        "beta": float(beta), "corr": float(corr),
        "bench_return": float(bench_return), "bench_vol": float(bench_vol),
        "best": float(r.max()), "worst": float(r.min()), "up_days": float((r > 0).mean()),
        "last": float(px.iloc[-1]), "days": int(len(r)),
        # ชุดข้อมูลสำหรับกราฟ
        "returns": r, "drawdown": dd,
        "growth": px / px.iloc[0] * 100,          # เงิน 100 โตเป็นเท่าไร
        "growth_bench": growth_bench,
    }
