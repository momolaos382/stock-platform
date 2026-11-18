# =====================================================
# lao_fundamentals.py — อ่านงบการเงินหุ้นลาวจากไฟล์ PDF "Factsheet" ของตลาดหลักทรัพย์ลาว
#
# LSX ไม่มีงบการเงินใน API แต่ทุกไตรมาสจะออก Factsheet (PDF 2 หน้า) ของแต่ละบริษัท
# Factsheet ไตรมาส 4 (และฉบับรายปี 2020–2021) มีคอลัมน์แรกเป็น "ทั้งปี" → ใช้ทำงบรายปี
#
# ขั้นตอน:  รายชื่อไฟล์จาก API → ดาวน์โหลดเก็บไว้ data/lao/_factsheets/ (ไม่ดาวน์โหลดซ้ำ)
#           → อ่านตัวเลขด้วย pdfplumber → บันทึก data/lao/<CODE>/fundamentals.csv
#
# ข้อควรรู้: ตัวเลขเป็นไปตามที่ LSX เผยแพร่ (หน่วยพันล้านกีบ) บางไฟล์มีความคลาดเคลื่อนจากต้นทาง
#            ข้อความใน PDF มีช่องว่างแทรกในตัวเลข (เช่น "1 ,710") จึงอ่านจาก "ตำแหน่ง" ของตัวอักษรแทน
# =====================================================
import re
from pathlib import Path

import pandas as pd

from core import lao

CACHE = lao.ROOT / "_factsheets"
RENAMED = {"LCC": "LCTC"}            # บริษัทที่เปลี่ยนชื่อย่อ (Lao Cement → Lao Culture Tourism)
BILLION = 1e9

# ชื่อแถวใน Factsheet → ชื่อคอลัมน์ของเรา (แต่ละบริษัทใช้คำต่างกันเล็กน้อย จึงเทียบด้วย regex, ตัวพิมพ์เล็ก)
ROWS = [
    (r"^revenue", "sales"),
    (r"^total (operating )?income", "total_income"),
    (r"^(earning|profit) before tax", "ebt"),
    (r"^ebitda", "ebitda"),
    (r"^net (profit|income)(?!.*margin)", "net_income"),
    (r"^(total )?current assets?", "cur_assets"),
    (r"^current liabilit", "cur_liab"),
    (r"^total liabilit", "liabilities"),
    (r"^total (shareholders'? )?equity", "equity"),
    (r"^total assets?", "assets"),
    (r"^(net cash flows? from (\(used in\) )?)?operating activities|^net cash flows? from (\(used in\) )?operating", "op_cf"),
    (r"^net cash flows? from (\(used in\) )?investing", "inv_cf"),
    (r"^net cash flows? from (\(used in\) )?financing", "fin_cf"),
    (r"^eps", "eps"),
    (r"^listed share", "shares"),
]
HEADERS = ("item", "financial data", "statistic", "ratio")
NUM_RE = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?%?$")


# ---------- 1) รายชื่อ Factsheet รายปี ----------
def annual_list() -> dict:
    """{CODE: {ปี: ชื่อไฟล์}} เฉพาะฉบับที่มีตัวเลขทั้งปี (Q4 หรือฉบับรายปี)"""
    items = []
    for page in range(1, 10):
        rows = lao._api(f"factsheet?lang=en&page={page}&pageSize=100")
        items += rows
        if len(rows) < 100:
            break
    out = {}
    for x in items:
        title = x.get("title") or ""
        files = [f["fileName"] for f in x.get("attached_files", []) if f["fileName"].lower().endswith(".pdf")]
        if not files:
            continue
        m = re.search(r"(?:of\s+)?([A-Za-z\-]+)\s*[_ ]\s*Q4\s*[- ]?\s*(\d{4})", title) or \
            re.search(r"(?:of\s+)?([A-Za-z\-]+)\s*[_ ]\s*(\d{4})\s*$", title.strip())
        if not m:
            continue
        code = lao.clean_code(m.group(1))
        code = RENAMED.get(code, code)
        if code:
            out.setdefault(code, {}).setdefault(int(m.group(2)), files[0])
    return out


def _download(file_name: str) -> Path:
    import urllib.request
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / file_name
    if not path.exists() or path.stat().st_size == 0:
        req = urllib.request.Request(lao.API + "attach-file/" + file_name, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            path.write_bytes(r.read())
    return path


# ---------- 2) อ่านตัวเลขจาก PDF ----------
def _num(tok: str):
    t = tok.replace(" ", "")
    if not NUM_RE.match(t):
        return None
    neg = t.startswith("(") or t.startswith("-")
    t = t.strip("()%-").replace(",", "")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def _cell(c) -> str:
    return re.sub(r"\s+", " ", (c or "")).strip()


def parse(path: Path) -> dict:
    """อ่านตารางทุกตารางใน PDF (เส้นตารางช่วยแยกคอลัมน์ได้แม่นกว่าการอ่านข้อความ)
    คืนค่า {ชื่อคอลัมน์: ตัวเลขคอลัมน์ "ทั้งปี"} + 'dps': {ปี: ปันผลต่อหุ้น}"""
    import pdfplumber
    found, dps = {}, {}
    with pdfplumber.open(path) as pdf:
        tables = [tb for page in pdf.pages for tb in page.extract_tables()]
    for tb in tables:
        rows = [[_cell(c) for c in r] for r in tb if r]
        if not rows:
            continue
        head = [h.lower() for h in rows[0]]
        # ตารางปันผล: หัวตาราง Year | Payment Date | LAK/Share
        if head and head[0] == "year" and any("lak/share" in h for h in head):
            k = next(i for i, h in enumerate(head) if "lak/share" in h)
            for r in rows[1:]:
                m = re.match(r"annual\s+(\d{4})", r[0].lower())
                if m and k < len(r) and _num(r[k]) is not None:
                    dps[int(m.group(1))] = _num(r[k])
            continue
        # ตารางที่มีหัวคอลัมน์ตามช่วงเวลา: คอลัมน์แรกต้องเป็นปีล้วน (= ทั้งปี) ถึงจะใช้
        # (ตารางแถวเดียวที่ถูกตัดข้ามหน้า เช่น "Total Asset" จะไม่มีหัวตาราง → ใช้ได้เลย)
        col = 1
        if head[0] in HEADERS and len(head) >= 3 and not re.fullmatch(r"\d{4}", head[1] or ""):
            continue
        for r in rows:
            if len(r) <= col:
                continue
            low = r[0].lower()
            if "operating" in low and "investing" in low:      # เซลล์ป้ายชื่อติดกันผิดพลาด → ข้าม
                continue
            for pattern, name in ROWS:
                if re.search(pattern, low):
                    v = _num(r[col])
                    if v is not None and name not in found:
                        found[name] = v
                    break
    found["dps"] = dps
    return found


# ---------- 3) รวมเป็นตารางรายปี แล้วบันทึก ----------
def build(code: str, files: dict) -> pd.DataFrame:
    rows = []
    for year, fname in sorted(files.items()):
        try:
            v = parse(_download(fname))
        except Exception:
            continue
        dps = v.pop("dps", {})
        v["year"] = year
        v["dps"] = dps.get(year)
        rows.append(v)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.set_index("year").sort_index()
    for c in ("sales", "total_income", "ebt", "ebitda", "net_income", "equity", "shares", "eps",
              "liabilities", "assets", "cur_liab"):
        if c not in df:
            df[c] = float("nan")
    # ---- กรองค่าที่ผิดชัดเจนจากต้นทาง ----
    # จำนวนหุ้นปีเดียวที่ต่างจากปีก่อนและปีหลัง (ซึ่งเท่ากัน) → พิมพ์ผิด ใช้ค่าข้างเคียง (เช่น LAT 2021)
    sh = df["shares"].copy()
    for i in range(1, len(sh) - 1):
        if sh.iloc[i - 1] == sh.iloc[i + 1] and sh.iloc[i] != sh.iloc[i - 1]:
            sh.iloc[i] = sh.iloc[i - 1]
    df["shares"] = sh
    if "total_income" in df:
        bad = df["ebitda"].abs() > 5 * df["total_income"].abs()        # EBITDA เกินรายได้หลายเท่า (เช่น LALCO 2024)
        df.loc[bad, "ebitda"] = float("nan")
    if {"liabilities", "assets"} <= set(df.columns):
        bad = df["liabilities"] > 1.5 * df["assets"]                     # หนี้สินมากกว่าสินทรัพย์รวมผิดปกติ
        df.loc[bad, ["liabilities", "cur_liab"]] = float("nan")
    if {"liabilities", "equity", "assets"} <= set(df.columns):
        bad = (df["liabilities"] <= 0) & (df["assets"] > 0)
        df.loc[bad, "liabilities"] = float("nan")
    # EPS ใน Factsheet บางปีผิด (ไม่ตรงกับ กำไร ÷ จำนวนหุ้น) → คำนวณเองจากกำไรสุทธิ
    # ถ้าไม่มีกำไรสุทธิแต่มี EPS → ย้อนคำนวณกำไรจาก EPS × จำนวนหุ้น
    calc = df["net_income"] * BILLION / df["shares"]
    df["net_income"] = df["net_income"].fillna(df["eps"] * df["shares"] / BILLION)
    df["eps_calc"] = calc.fillna(df["eps"])
    df["bv_calc"] = df["equity"] * BILLION / df["shares"]
    return df


def sync(codes=None, force=False) -> dict:
    """ดึง + อ่าน Factsheet ของทุกบริษัท (หรือเฉพาะ codes) → data/lao/<CODE>/fundamentals.csv
    ถ้าไม่มี Factsheet ใหม่และทุกบริษัทมีไฟล์แล้ว → ข้าม (อ่าน PDF ทั้งหมดใช้เวลา 1–2 นาที)"""
    ok, failed = [], []
    listing = annual_list()
    universe = {lao.code_of(s) for s in lao.universe()}
    if not force:
        wanted = {c: f for c, f in listing.items() if c in universe}
        up_to_date = all((CACHE / fn).exists() for files in wanted.values() for fn in files.values()) and \
            all((lao.ROOT / c / "fundamentals.csv").exists() for c in wanted)
        if up_to_date:
            return {"ok": [], "failed": [], "skipped": True}
    built = {}
    for code, files in listing.items():
        if code not in universe or (codes and code not in codes):
            continue
        try:
            df = build(code, files)
            if df.empty:
                failed.append(code)
                continue
            built[code] = df
        except Exception:
            failed.append(code)
    # กระแสเงินสดที่ "เหมือนกันทุกหลัก" กับบริษัทอื่นในปีเดียวกัน = คัดลอกผิดในต้นทาง (เช่น JDB 2025 = BCEL 2025)
    # → ลบออกจากบริษัทที่จดทะเบียนทีหลัง (มีข้อมูลน้อยปีกว่า)
    cf = ["op_cf", "inv_cf"]
    for a in built:
        for b in built:
            if a >= b or not set(cf) <= set(built[a].columns) or not set(cf) <= set(built[b].columns):
                continue
            for year in built[a].index.intersection(built[b].index):
                va, vb = built[a].loc[year, cf], built[b].loc[year, cf]
                if va.notna().all() and (va.values == vb.values).all():
                    victim = a if len(built[a]) < len(built[b]) else b
                    built[victim].loc[year, cf] = float("nan")
    for code, df in built.items():
        df.to_csv(lao.ROOT / code / "fundamentals.csv")
        ok.append(code)
    return {"ok": ok, "failed": failed}
