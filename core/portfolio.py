# =====================================================
# portfolio.py — สูตรของหน้า "จัดสรรพอร์ต" (ทฤษฎีพอร์ตสมัยใหม่ของ Markowitz)
#   prepare()   ราคารายวัน → ผลตอบแทนคาดหวังต่อปี (mu) + ความแปรปรวนร่วม (cov)
#   optimize()  หาน้ำหนักหุ้นแต่ละตัว 3 วิธี:
#                 equal   แบ่งเท่ากันทุกตัว
#                 minvol  ความผันผวนของพอร์ตต่ำสุด
#                 sharpe  ผลตอบแทนต่อความเสี่ยง (Sharpe) สูงสุด
#   stats()     ผลตอบแทน / ความผันผวน / Sharpe ของพอร์ต
#   cloud()     สุ่มพอร์ตจำนวนมาก ไว้วาดแผนที่ความเสี่ยง–ผลตอบแทน
#   save / list / delete  บันทึกพอร์ตของผู้ใช้ในฐานข้อมูล
# =====================================================
import json
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from core import auth
from core.risk import RISK_FREE, TRADING_DAYS

METHODS = ["equal", "minvol", "sharpe"]
MAX_STOCKS = 10
MAX_WEIGHT = 0.40     # หุ้น 1 ตัวถือได้ไม่เกิน 40% ของส่วนหุ้น (กันการกระจุกตัว)


def prepare(prices: pd.DataFrame):
    """คืนค่า (mu, cov) เป็นรายปี — mu = ค่าเฉลี่ยผลตอบแทนรายวัน × 252"""
    r = prices.pct_change().dropna()
    return r.mean().values * TRADING_DAYS, r.cov().values * TRADING_DAYS


def stats(w, mu, cov) -> dict:
    ret = float(w @ mu)
    vol = float(np.sqrt(w @ cov @ w))
    return {"ret": ret, "vol": vol, "sharpe": (ret - RISK_FREE) / vol if vol > 0 else float("nan")}


def optimize(mu, cov, method: str):
    """หาน้ำหนัก (รวมกัน = 1, ไม่ติดลบ = ไม่ขายชอร์ต, ไม่เกินเพดานต่อตัว)"""
    n = len(mu)
    w0 = np.full(n, 1 / n)
    if method == "equal" or n < 2:
        return w0
    cap = max(MAX_WEIGHT, 1 / n) if n > 2 else 1.0
    if method == "minvol":
        objective = lambda w: w @ cov @ w                                    # noqa: E731
    else:
        objective = lambda w: -(w @ mu - RISK_FREE) / np.sqrt(w @ cov @ w)   # noqa: E731
    res = minimize(objective, w0, method="SLSQP", bounds=[(0, cap)] * n,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}])
    w = res.x if res.success else w0
    w = np.where(w < 1e-4, 0, w)      # ปัดน้ำหนักที่เล็กมากให้เป็น 0
    return w / w.sum()


def cloud(mu, cov, n: int = 1200, seed: int = 7):
    """สุ่มน้ำหนัก n ชุด → (ความผันผวน, ผลตอบแทน) ของแต่ละชุด"""
    w = np.random.default_rng(seed).dirichlet(np.ones(len(mu)), n)
    return np.sqrt(np.einsum("ij,jk,ik->i", w, cov, w)), w @ mu


# ---------- บันทึกพอร์ต (ตาราง portfolios) ----------
def save(user_id: int, name: str, data: dict):
    with auth.get_conn() as conn:
        conn.execute("INSERT INTO portfolios (user_id, name, data_json, created_at) VALUES (?, ?, ?, ?)",
                     (user_id, name.strip()[:60], json.dumps(data), datetime.now().isoformat()))


def list_saved(user_id: int) -> list:
    with auth.get_conn() as conn:
        rows = conn.execute("SELECT id, name, data_json, created_at FROM portfolios "
                            "WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    return [{"id": r[0], "name": r[1], "data": json.loads(r[2]), "created_at": r[3]} for r in rows]


def delete(user_id: int, portfolio_id: int):
    with auth.get_conn() as conn:
        conn.execute("DELETE FROM portfolios WHERE id = ? AND user_id = ?", (portfolio_id, user_id))
