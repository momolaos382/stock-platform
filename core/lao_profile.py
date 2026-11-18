# =====================================================
# lao_profile.py — ข้อมูลบริษัท + ข่าว/ประกาศ ของหุ้นลาว (LSX)
#
#   profile(code)        โปรไฟล์บริษัทจากหน้าแรกของ Factsheet (PDF) ล่าสุด:
#                        ที่อยู่ โทร เว็บไซต์ วันก่อตั้ง วันจดทะเบียน ราคา IPO ที่ปรึกษาการเงิน
#                        กรรมการ (ชื่อ-ตำแหน่ง) จำนวนผู้ถือหุ้น สัดส่วนหุ้นเสรี/ต่างชาติ
#   disclosures(code)    ประกาศ/ข่าวของบริษัทจากระบบเปิดเผยข้อมูลของ LSX (ผลประกอบการ มติ ประชุมผู้ถือหุ้น
#                        ข่าวประชาสัมพันธ์ ฯลฯ) พร้อมลิงก์ไปเอกสารต้นฉบับ — API สาธารณะ ไม่ต้องล็อกอิน
#   market_news()        ข่าวของตลาดหลักทรัพย์ลาวเอง (LSX News)
# =====================================================
import json
import re

from core import lao, lao_fundamentals as lf

LSX_SITE = "http://lsx.com.la"


# ---------- โปรไฟล์จาก Factsheet ----------
def _latest_factsheets() -> dict:
    """{CODE: ชื่อไฟล์ PDF ของฉบับล่าสุด} (postId มากสุด)"""
    best = {}
    for page in range(1, 4):
        rows = lao._api(f"factsheet?lang=en&page={page}&pageSize=100")
        for x in rows:
            files = [f["fileName"] for f in x.get("attached_files", []) if f["fileName"].lower().endswith(".pdf")]
            m = re.search(r"(?:of\s+)?([A-Za-z\-]+)\s*[_ ]\s*(?:Q[1-4]\s*[- ]?\s*)?\d{4}\s*$", (x.get("title") or "").strip())
            if not files or not m:
                continue
            code = lao.clean_code(m.group(1))
            code = lf.RENAMED.get(code, code)
            if code and int(x["postId"]) > best.get(code, (0, ""))[0]:
                best[code] = (int(x["postId"]), files[0])
        if len(rows) < 100:
            break
    return {c: v[1] for c, v in best.items()}


def _num(text):
    t = re.sub(r"[\s,]", "", text or "")
    try:
        return float(t.rstrip("%"))
    except ValueError:
        return None


def parse_profile(path) -> dict:
    """อ่านหน้า 1 ของ Factsheet — ฝั่งซ้าย: โปรไฟล์ + ตารางหุ้น + กรรมการ"""
    import pdfplumber
    out = {}
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        left = page.crop((0, 0, page.width * 0.52, page.height))
        text = left.extract_text() or ""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        def after(label):
            for i, ln in enumerate(lines):
                if ln.lower().startswith(label):
                    return ln[len(label):].strip(" :")
            return None

        def clean(s):
            s = re.sub(r"(?<=\d)(?=[A-Za-z])|(?<=[a-z])(?=\d)", " ", s or "").strip()      # "11January2011" → "11 January 2011"
            m = re.match(r"^(.*?\b(?:19|20)\d{2})\b", s)                                      # ตัดเลขที่ติดมาท้ายปี (มาจากคอลัมน์ข้างๆ)
            return (m.group(1) if m else s) or None

        # ที่อยู่อาจยาว 2 บรรทัด (บรรทัดถัดไปไม่มีป้ายกำกับ)
        for i, ln in enumerate(lines):
            if ln.lower().startswith("address:"):
                addr = ln[8:].strip()
                nxt = lines[i + 1] if i + 1 < len(lines) else ""
                if nxt and not re.match(r"^(tel|website|establishment|listing|ipo|financial)\b", nxt, re.I) and len(nxt) < 60:
                    addr += " " + nxt
                out["address"] = addr
                break
        out["phone"] = after("tel:")
        out["website"] = after("website:")
        out["established"] = clean(after("establishment date:"))
        out["listed"] = clean(after("listing date on lsx:"))
        out["ipo_price"] = after("ipo price:")
        out["advisor"] = after("financial advisor:")
        # คำอธิบายธุรกิจ: ข้อความใต้หัวข้อ "Type of Business" จนถึง "Information of Listed Share"
        body, on = [], False
        for ln in lines:
            if ln.lower().startswith("type of business"):
                on = True
                continue
            if on and re.match(r"^(information of listed|market price|listing date)", ln, re.I):
                break
            if on:
                body.append(ln)
        out["business"] = " ".join(body).strip() or None

        for tb in page.extract_tables():
            rows = [[re.sub(r"\s+", " ", (c or "")).strip() for c in r] for r in tb if r]
            if not rows:
                continue
            if rows[0] and "name and surname" in " ".join(rows[0]).lower():          # ตารางกรรมการ
                out["board"] = [{"name": r[1], "position": r[-1]} for r in rows[1:]
                                if len(r) >= 3 and r[0].isdigit() and r[1]]
            elif any(r[0].lower().startswith("market price") for r in rows if r):
                for r in rows:
                    if len(r) < 2:
                        continue
                    k = r[0].lower()
                    if k.startswith("free float"):
                        out["free_float"] = _num(r[1])
                    elif k.startswith("portion of foreign"):
                        out["foreign"] = _num(r[1])
                    elif k.startswith("total shareholder"):
                        out["shareholders"] = _num(r[1])
                    elif k.startswith("listed share"):
                        out["listed_shares"] = _num(r[1])
    return {k: v for k, v in out.items() if v not in (None, "", [])}


def profile(code: str):
    """โปรไฟล์ที่เก็บไว้ (data/lao/<CODE>/profile.json) / None"""
    try:
        return json.loads((lao.ROOT / code / "profile.json").read_text(encoding="utf-8"))
    except Exception:
        return None


def sync_profiles() -> dict:
    """อ่านโปรไฟล์ของทุกบริษัท (ทำใหม่เฉพาะเมื่อมี Factsheet ฉบับใหม่กว่าที่เก็บไว้)"""
    ok, failed = [], []
    latest = _latest_factsheets()
    for sym in lao.universe():
        code = lao.code_of(sym)
        fname = latest.get(code)
        if not fname:
            continue
        old = profile(code)
        if old and old.get("_factsheet") == fname:
            continue
        try:
            data = parse_profile(lf._download(fname))
            data["_factsheet"] = fname
            (lao.ROOT / code / "profile.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            ok.append(code)
        except Exception:
            failed.append(code)
    return {"ok": ok, "failed": failed}


# ---------- ประกาศ / ข่าว ----------
def _isin(code: str):
    return (lao._read_info(code) or {}).get("isin")


def disclosures(code: str, lang: str = "en", limit: int = 20) -> list:
    """ประกาศล่าสุดของบริษัท (ชื่อเรื่อง วันที่ ลิงก์ไปเอกสารต้นฉบับ) — ดึงสดจาก LSX / ไม่ได้ → []"""
    isin = _isin(code)
    if not isin:
        return []
    try:
        rows = lao._api(f"disclosure/public?lang={lang}&security_tab=stocks&page=1&page_size={limit}&search={isin}")
    except Exception:
        return []
    out = []
    for r in rows:
        if r.get("isin_code") and r["isin_code"] != isin:
            continue
        title = (r.get("disclosure_title_lo") if lang == "lo" else r.get("disclosure_title_en")) or r.get("disclosure_title")
        if title and r.get("link"):
            out.append({"title": title.strip(), "date": (r.get("approved_date_order") or "")[:10], "url": r["link"]})
    return out


def market_news(lang: str = "en", limit: int = 6) -> list:
    """ข่าวของ LSX เอง (กิจกรรม ตลาด หลักทรัพย์ใหม่) — ลิงก์ไปหน้าข่าวบนเว็บ LSX"""
    try:
        rows = lao._api(f"news?lang={'lo' if lang == 'lo' else 'en'}&page=1&pageSize={limit}")
    except Exception:
        return []
    return [{"title": (r.get("title") or "").strip(), "date": (r.get("regDate") or "")[:10],
             "url": f"{LSX_SITE}/{'lo' if lang == 'lo' else 'en'}/about/news/content?postId={r['postId']}"}
            for r in rows if r.get("title") and r.get("postId")]
