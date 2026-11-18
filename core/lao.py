# =====================================================
# lao.py — หุ้นตลาดหลักทรัพย์ลาว (LSX)
# Yahoo Finance ไม่มีข้อมูลหุ้นลาว จึงเก็บเป็นไฟล์ CSV ในโฟลเดอร์ data/lao/ เอง
#
#   data/lao/<CODE>/info.json        ชื่อบริษัท กลุ่มธุรกิจ EPS ฯลฯ
#   data/lao/<CODE>/prices.csv       คอลัมน์ date, close   (รายวัน)
#   data/lao/<CODE>/financials.csv   งบกำไรขาดทุน  (แถว = รายการ, คอลัมน์ = ปี)
#   data/lao/<CODE>/balance.csv      งบดุล
#   data/lao/<CODE>/cashflow.csv     งบกระแสเงินสด
#   data/lao/_index.csv              ดัชนี LSX Composite (date, close) — ใช้เทียบความเสี่ยง (ไม่บังคับ)
#
# ชื่อย่อในระบบ = <CODE>.LSX  เช่น BCEL.LSX
# เพิ่ม/แก้ข้อมูลได้ที่หน้า "ข้อมูลหุ้นลาว" ในเว็บ หรือวางไฟล์เองก็ได้
# =====================================================
import io
import json
import re
from pathlib import Path

import pandas as pd

SUFFIX = ".LSX"
ROOT = Path(__file__).resolve().parent.parent / "data" / "lao"
_CODE_RE = re.compile(r"^[A-Z0-9\-]{2,12}$")

# ชื่อรายการในงบการเงิน (ต้องตรงกับที่ valuation.py อ่าน)
FIN_ITEMS = ["Total Revenue", "Operating Income", "Interest Expense", "Net Income",
             "Diluted EPS", "Diluted Average Shares"]
BS_ITEMS = ["Stockholders Equity", "Total Debt", "Current Assets", "Current Liabilities"]
CF_ITEMS = ["Operating Cash Flow", "Capital Expenditure", "Free Cash Flow", "Cash Dividends Paid"]
FILES = {"fin": ("financials.csv", FIN_ITEMS), "bs": ("balance.csv", BS_ITEMS), "cf": ("cashflow.csv", CF_ITEMS)}


def is_lao(symbol: str) -> bool:
    return (symbol or "").upper().endswith(SUFFIX)


def code_of(symbol: str) -> str:
    return symbol[: -len(SUFFIX)] if is_lao(symbol) else symbol


def clean_code(text: str):
    """BCEL / bcel / BCEL.LSX → 'BCEL'  (None ถ้ารูปแบบไม่ถูก)"""
    s = (text or "").strip().upper()
    if s.endswith(SUFFIX):
        s = s[: -len(SUFFIX)]
    return s if _CODE_RE.match(s) else None


def _read_info(code: str) -> dict:
    try:
        return json.loads((ROOT / code / "info.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def universe() -> dict:
    """หุ้นลาวที่มีข้อมูลในเครื่อง → {ชื่อย่อ.LSX: (ชื่อบริษัท, กลุ่มธุรกิจ)}"""
    out = {}
    if ROOT.exists():
        for d in sorted(ROOT.iterdir()):
            if d.is_dir() and _CODE_RE.match(d.name) and (d / "prices.csv").exists():
                info = _read_info(d.name)
                out[d.name + SUFFIX] = (info.get("name") or d.name, info.get("sector") or "Other")
    return out


def _prices(code: str) -> pd.Series:
    """ราคาปิดรายวัน "ปรับแล้ว" (adjusted close)
    วันที่มีการแตกหุ้น/เพิ่มทุน/ขึ้นเครื่องหมาย XD ตลาดจะตั้งราคาฐาน (base) ไม่เท่ากับราคาปิดวันก่อน (prev)
    → อัตราส่วน base ÷ prev คือตัวคูณ ใช้ปรับราคาย้อนหลังทั้งหมดก่อนวันนั้น
    (เช่น BCEL แตกหุ้น 5:1 วันที่ 14 ก.พ. 2025: 1,270 ÷ 6,350 = 0.2) ไม่ปรับ → กราฟจะดิ่ง 80% ทั้งที่ไม่ได้ขาดทุนจริง"""
    s, adj = _raw_and_factor(code)
    return s * adj


def _raw_and_factor(code: str):
    """(ราคาปิดดิบ, ตัวคูณปรับราคาสะสม) รายวัน"""
    df = pd.read_csv(ROOT / code / "prices.csv")
    df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date", "close"]).drop_duplicates("date", keep="last").sort_values("date")
    s = df.set_index("date")["close"].astype(float)
    adj = pd.Series(1.0, index=s.index)
    if {"base", "prev"} <= set(df.columns):
        base = pd.to_numeric(df["base"], errors="coerce").values
        prev = pd.to_numeric(df["prev"], errors="coerce").values
        factor = pd.Series(1.0, index=s.index)
        mask = (base > 0) & (prev > 0) & (base != prev)
        factor[mask] = base[mask] / prev[mask]
        # ตัวคูณของวันนั้นใช้กับทุกวัน "ก่อนหน้า" → คูณสะสมจากท้ายมาหน้า แล้วเลื่อน 1 วัน
        adj = factor[::-1].cumprod()[::-1].shift(-1).fillna(1.0)
    return s, adj


def _factor_at(adj: pd.Series, date) -> float:
    """ตัวคูณปรับราคา ณ วันที่ (ใช้ปรับ EPS/มูลค่าตามบัญชี/ปันผลต่อหุ้นของปีเก่าให้เทียบกับราคาที่ปรับแล้วได้)"""
    if adj.empty:
        return 1.0
    if date < adj.index[0]:
        return float(adj.iloc[0])
    return float(adj.asof(date))


def _from_fundamentals(code: str, sector: str):
    """สร้างงบ 3 ตาราง (หน้าตาแบบ yfinance) จาก fundamentals.csv ที่อ่านมาจาก Factsheet ของ LSX
    คืนค่า (fin, bs, cf, ค่าล่าสุดสำหรับ info) / None ถ้าไม่มีไฟล์"""
    path = ROOT / code / "fundamentals.csv"
    if not path.exists():
        return None
    f = pd.read_csv(path, index_col="year").sort_index()
    if f.empty:
        return None
    _, adj = _raw_and_factor(code)
    B = 1e9
    dates = [pd.Timestamp(year=int(y), month=12, day=31) for y in f.index]
    k = pd.Series([_factor_at(adj, d) for d in dates], index=f.index)
    col = lambda name: f[name] if name in f else pd.Series(float("nan"), index=f.index)   # noqa: E731
    eps_adj = col("eps_calc") * k
    ni = col("net_income") * B
    shares_adj = ni / eps_adj
    op_inc = col("ebt").fillna(col("ebitda")) * B          # ไม่มี EBIT ใน Factsheet → ใช้กำไรก่อนภาษี (หรือ EBITDA)
    revenue = col("total_income").fillna(col("sales")) * B
    debt = col("liabilities") * B if sector != "Financial Services" else pd.Series(float("nan"), index=f.index)
    op_cf, inv_cf = col("op_cf") * B, col("inv_cf") * B
    dividends = col("dps") * col("shares")                 # ปันผลต่อหุ้น (ดิบ) × จำนวนหุ้นปีนั้น

    def table(rows: dict) -> pd.DataFrame:
        df = pd.DataFrame(rows).T
        df.columns = dates
        return df.loc[:, ::-1]                             # ใหม่ → เก่า เหมือน yfinance

    fin = table({"Total Revenue": revenue.values, "Operating Income": op_inc.values, "Net Income": ni.values,
                 "Diluted EPS": eps_adj.values, "Diluted Average Shares": shares_adj.values})
    bs = table({"Stockholders Equity": (col("equity") * B).values, "Total Debt": debt.values,
                "Current Assets": (col("cur_assets") * B).values, "Current Liabilities": (col("cur_liab") * B).values})
    cf = table({"Operating Cash Flow": op_cf.values, "Capital Expenditure": inv_cf.where(inv_cf < 0).values,
                "Free Cash Flow": (op_cf + inv_cf).values, "Cash Dividends Paid": (-dividends).values})
    last = {
        "eps": eps_adj.dropna().iloc[-1] if eps_adj.notna().any() else None,
        "book_value": (col("bv_calc") * k).dropna().iloc[-1] if (col("bv_calc") * k).notna().any() else None,
        "dividend": (col("dps") * k).dropna().iloc[-1] if (col("dps") * k).notna().any() else None,
        "year": int(f.index[-1]),
    }
    return fin, bs, cf, last


def _statement(code: str, key: str) -> pd.DataFrame:
    """อ่านงบ: ไฟล์ CSV แถว=รายการ คอลัมน์=ปี → ตารางหน้าตาเหมือนของ yfinance (คอลัมน์เป็นวันที่ ใหม่→เก่า)"""
    path = ROOT / code / FILES[key][0]
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, index_col=0)
        df.index = [str(i).strip() for i in df.index]
        df.columns = [pd.Timestamp(year=int(str(c).strip()[:4]), month=12, day=31) for c in df.columns]
        df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
        return df.sort_index(axis=1, ascending=False)
    except Exception:
        return pd.DataFrame()


def load(symbol: str) -> dict:
    """ข้อมูลหุ้นลาว 1 ตัว — โครงสร้างเดียวกับ data._fetch (ใช้ร่วมกับหน้าวิเคราะห์ได้เลย)"""
    code = code_of(symbol)
    daily = _prices(code)
    if daily.empty:
        raise FileNotFoundError(symbol)
    monthly = daily.resample("ME").last().dropna()
    inf = _read_info(code)
    last, prev = float(daily.iloc[-1]), float(daily.iloc[-2]) if len(daily) > 1 else None
    shares = inf.get("shares")
    # งบการเงิน: ไฟล์ที่ผู้ใช้อัปโหลดเอง (financials.csv) มาก่อน / ไม่มี → ใช้ที่อ่านจาก Factsheet ของ LSX
    fin, bs, cf = _statement(code, "fin"), _statement(code, "bs"), _statement(code, "cf")
    auto = None if not fin.empty else _from_fundamentals(code, inf.get("sector"))
    if auto:
        fin, bs, cf, latest = auto
        for k in ("eps", "book_value", "dividend"):
            if inf.get(k) is None and latest.get(k) is not None:
                inf[k] = float(latest[k])
    eps = inf.get("eps")
    return {
        "symbol": symbol,
        "info": {
            "shortName": inf.get("name") or code, "longName": inf.get("name") or code,
            "sector": inf.get("sector"), "industry": inf.get("industry"),
            "currency": inf.get("currency") or "LAK", "financialCurrency": inf.get("currency") or "LAK",
            "fullExchangeName": "Lao Securities Exchange", "exchange": "LSX",
            "currentPrice": last, "previousClose": prev,
            "marketCap": last * shares if shares else None,
            "trailingEps": eps, "trailingPE": (last / eps) if eps else None,
            "bookValue": inf.get("book_value"), "beta": None, "dividendRate": inf.get("dividend"),
            "longBusinessSummary": inf.get("description"), "country": "Laos",
        },
        "price": monthly,
        "fin": fin, "bs": bs, "cf": cf,
    }


def daily(symbol: str) -> pd.Series:
    return _prices(code_of(symbol))


def index_daily():
    """ดัชนี LSX Composite รายวัน (ถ้ามีไฟล์) ไม่มี → None"""
    p = ROOT / "_index.csv"
    if not p.exists():
        return None
    try:
        df = pd.read_csv(p)
        df.columns = [c.strip().lower() for c in df.columns]
        s = pd.Series(pd.to_numeric(df["close"], errors="coerce").values, index=pd.to_datetime(df["date"], errors="coerce"))
        return s[s.index.notna()].dropna().sort_index()
    except Exception:
        return None


# ---------- นำเข้าข้อมูล (ใช้ในหน้า "ข้อมูลหุ้นลาว") ----------
def template(kind: str) -> str:
    """ไฟล์ตัวอย่าง (CSV) ให้ดาวน์โหลดไปกรอก"""
    if kind == "prices":
        return "date,close\n2025-01-02,0\n2025-01-03,0\n"
    items = FILES[kind][1]
    return "item,2021,2022,2023,2024\n" + "".join(f"{i},,,,\n" for i in items)


def parse_prices(raw: bytes) -> pd.DataFrame:
    """ตรวจไฟล์ราคา: ต้องมีคอลัมน์ date, close และอย่างน้อย 30 แถวที่ใช้ได้"""
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = [c.strip().lower() for c in df.columns]
    if not {"date", "close"} <= set(df.columns):
        raise ValueError("columns")
    out = pd.DataFrame({"date": pd.to_datetime(df["date"], errors="coerce"),
                        "close": pd.to_numeric(df["close"], errors="coerce")}).dropna()
    out = out[out["close"] > 0].drop_duplicates("date", keep="last").sort_values("date")
    if len(out) < 30:
        raise ValueError("rows")
    return out


def save(code: str, info: dict, prices: pd.DataFrame, statements: dict):
    """บันทึกหุ้น 1 ตัว  statements = {'fin': bytes|None, 'bs': ..., 'cf': ...}"""
    d = ROOT / code
    d.mkdir(parents=True, exist_ok=True)
    (d / "info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    prices.assign(date=prices["date"].dt.strftime("%Y-%m-%d")).to_csv(d / "prices.csv", index=False)
    for key, raw in (statements or {}).items():
        if raw:
            (d / FILES[key][0]).write_bytes(raw)


def save_index(prices: pd.DataFrame):
    ROOT.mkdir(parents=True, exist_ok=True)
    prices.assign(date=prices["date"].dt.strftime("%Y-%m-%d")).to_csv(ROOT / "_index.csv", index=False)


# ---------- ดึงข้อมูลอัตโนมัติจากเว็บตลาดหลักทรัพย์ลาว ----------
# เว็บ lsx.com.la มี API สาธารณะ (ใช้ http ธรรมดา — https ของเว็บนี้เชื่อมต่อไม่ได้)
#   stock/issue-list                 รายชื่อหุ้นทั้งหมด
#   stock/daily-closing-price        ราคารายวันย้อนหลัง (มีตั้งแต่ ม.ค. 2011)
#   stock/list-company-info          จำนวนหุ้นจดทะเบียน
#   index/daily-closing-list         ดัชนี LSX Composite รายวัน
# งบการเงินไม่มีใน API (มีเป็น PDF factsheet) → ต้องกรอก EPS/งบเองในหน้า "ข้อมูลหุ้นลาว" ถ้าต้องการคะแนนคุณภาพ
API = "http://lsx.com.la/api-server/api/"
FIRST_DATE = "20110101"

# กลุ่มธุรกิจของแต่ละบริษัท (จัดเองจากประเภทธุรกิจ — API ให้มาเป็นรหัสตัวเลขที่ไม่มีคำอธิบาย)
SECTOR_OF = {
    "BCEL": "Financial Services", "JDB": "Financial Services", "LALCO": "Financial Services",
    "MHTL": "Financial Services", "LCS": "Financial Services", "EDL-GEN": "Utilities",
    "PTL": "Energy", "SVN": "Consumer Cyclical", "LCTC": "Consumer Cyclical",
    "PCD": "Industrials", "LAT": "Consumer Defensive", "VCL": "Real Estate",
}


def _api(path: str):
    import urllib.request
    req = urllib.request.Request(API + path, headers={"User-Agent": "Mozilla/5.0 (stock-platform)"})
    with urllib.request.urlopen(req, timeout=90) as r:     # เซิร์ฟเวอร์ LSX ตอบช้า
        return json.loads(r.read().decode("utf-8")).get("data") or []


def _from_date(path: Path) -> str:
    """ถ้ามีไฟล์อยู่แล้ว ดึงต่อจากวันล่าสุด (ย้อน 10 วันเผื่อข้อมูลแก้ไข) ไม่มี → ดึงทั้งหมด"""
    try:
        df = pd.read_csv(path)
        if path.name == "prices.csv" and "base" not in df.columns:   # ไฟล์รุ่นเก่า (ไม่มีราคาฐาน) → ดึงใหม่ทั้งหมด
            return FIRST_DATE
        last = df["date"].max()
        return (pd.Timestamp(last) - pd.Timedelta(days=10)).strftime("%Y%m%d")
    except Exception:
        return FIRST_DATE


def _merge_save(path: Path, new: pd.DataFrame):
    if path.exists():
        try:
            old = pd.read_csv(path, parse_dates=["date"])
            new = pd.concat([old, new])
        except Exception:
            pass
    new = new.drop_duplicates("date", keep="last").sort_values("date")
    new.assign(date=new["date"].dt.strftime("%Y-%m-%d")).to_csv(path, index=False)


def sync() -> dict:
    """ดึงราคาหุ้นทุกตัว + ดัชนี จาก LSX แล้วบันทึกลง data/lao/  คืนค่า {สำเร็จ: [...], ผิดพลาด: [...]}"""
    today = pd.Timestamp.today().strftime("%Y%m%d")
    ok, failed = [], []
    issues = _api("stock/issue-list")
    shares = {x["ICode"]: x.get("NLStock") for x in _api("stock/list-company-info")}
    for it in issues:
        code = clean_code(it.get("INameEnglishAbbrev"))
        if not code:
            continue
        try:
            d = ROOT / code
            d.mkdir(parents=True, exist_ok=True)
            rows = _api(f"stock/daily-closing-price?ICode={it['ICode']}&fromDate={_from_date(d / 'prices.csv')}&toDate={today}")
            df = pd.DataFrame([{"date": pd.to_datetime(r["ODate"]), "close": r["CPrice"], "open": r["OPrice"],
                                "high": r["HPrice"], "low": r["LPrice"], "volume": r["TVolume"],
                                "base": r.get("BPrice"), "prev": r.get("PDCPrice")}
                               for r in rows if r.get("CPrice")])
            if not df.empty:
                _merge_save(d / "prices.csv", df)
            # ข้อมูลบริษัท: อัปเดตชื่อ/จำนวนหุ้นจาก LSX แต่เก็บค่าที่ผู้ใช้กรอกเอง (EPS ฯลฯ) ไว้
            info = _read_info(code)
            info.update({"name": (it.get("INameEnglish") or code).strip(), "name_lo": (it.get("IName") or "").strip(),
                         "isin": it["ICode"], "currency": "LAK", "source": "lsx.com.la"})
            info.setdefault("sector", SECTOR_OF.get(code, "Other"))
            if shares.get(it["ICode"]):
                info["shares"] = shares[it["ICode"]]
            (d / "info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
            ok.append(code)
        except Exception:
            failed.append(code)
    try:
        p = ROOT / "_index.csv"
        rows = _api(f"index/daily-closing-list?fromDate={_from_date(p)}&toDate={today}")
        df = pd.DataFrame([{"date": pd.to_datetime(r["ODate"]), "close": r["IndexIndex"]}
                           for r in rows if r.get("IICode") == "001" and r.get("IndexIndex")])
        if not df.empty:
            _merge_save(p, df)
    except Exception:
        failed.append("LSX Composite")
    return {"ok": ok, "failed": failed}


def last_sync():
    """เวลาที่ดึงข้อมูลล่าสุด (จากเวลาแก้ไขไฟล์ดัชนี) / None"""
    p = ROOT / "_index.csv"
    from datetime import datetime
    return datetime.fromtimestamp(p.stat().st_mtime) if p.exists() else None


def delete(code: str):
    import shutil
    if _CODE_RE.match(code) and (ROOT / code).is_dir():
        shutil.rmtree(ROOT / code)
