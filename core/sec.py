# =====================================================
# sec.py — โครงสร้างรายได้แยกตามธุรกิจ/ภูมิภาค จากรายงานประจำปี 10-K ที่ยื่นต่อ SEC (สหรัฐฯ)
#
# ขั้นตอน:
#   1) ชื่อย่อหุ้น → เลข CIK ของบริษัท           (sec.gov/files/company_tickers.json)
#   2) หา 10-K ฉบับล่าสุด                         (data.sec.gov/submissions/CIK##########.json)
#   3) เปิดไฟล์ XBRL ของรายงานนั้น (*_htm.xml)    ตัวเลขทุกตัวในงบมี "ป้าย" บอกว่าเป็นของธุรกิจ/ภูมิภาคไหน
#   4) เลือกตัวเลข "รายได้" ที่ติดป้ายแกนเดียว:  สินค้า/บริการ, กลุ่มธุรกิจ (segment), ภูมิภาค
#   5) ชื่อแต่ละกลุ่มอ่านจากไฟล์ป้ายชื่อ (*_lab.xml) เช่น aapl:IPhoneMember → "iPhone"
# ผลลัพธ์เก็บไว้ data/sec/ (1 รายงานอ่านครั้งเดียว)
#
# SEC บังคับให้ทุกคำขอระบุ "ชื่อโปรแกรม + อีเมลติดต่อ" ใน User-Agent
# → ผู้ใช้กรอกอีเมลเองในเว็บ (แท็บบริษัท) ระบบเก็บไว้ที่ data/sec/config.json หรือกำหนดผ่านตัวแปร SEC_USER_AGENT
# =====================================================
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data" / "sec"
CONFIG = ROOT / "config.json"
APP = "StockPlatform/1.0"

REVENUE_CONCEPTS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
    "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet", "SalesRevenueGoodsNet",
]
AXES = {
    "product": ["ProductOrServiceAxis"],
    "segment": ["StatementBusinessSegmentsAxis"],
    "region": ["StatementGeographicalAxis"],
}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class NeedContact(Exception):
    """ยังไม่ได้ตั้งอีเมลติดต่อสำหรับ SEC"""


# ---------- การตั้งค่าอีเมลติดต่อ ----------
def contact() -> str:
    env = os.environ.get("SEC_USER_AGENT")
    if env:
        return env
    try:
        email = json.loads(CONFIG.read_text(encoding="utf-8")).get("email", "")
        return f"{APP} {email}" if email else ""
    except Exception:
        return ""


def set_contact(email: str) -> bool:
    email = (email or "").strip()
    if not _EMAIL_RE.match(email):
        return False
    ROOT.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps({"email": email}), encoding="utf-8")
    return True


def _get(url: str) -> bytes:
    import urllib.request
    ua = contact()
    if not ua:
        raise NeedContact()
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


# ---------- 1–2) หา CIK และ 10-K ล่าสุด ----------
def _cik(ticker: str):
    path = ROOT / "company_tickers.json"
    if not path.exists() or path.stat().st_size == 0:
        ROOT.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_get("https://www.sec.gov/files/company_tickers.json"))
    t = json.loads(path.read_text(encoding="utf-8"))
    tk = ticker.upper().replace(".", "-")             # BRK.B → BRK-B ตามรูปแบบของ SEC
    return next((int(v["cik_str"]) for v in t.values() if v["ticker"].upper() == tk), None)


def _latest_10k(cik: int):
    sub = json.loads(_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))
    pages = [sub["filings"]["recent"]]
    # บริษัทที่ยื่นเอกสารเยอะมาก (เช่น Exxon) 10-K อาจไม่อยู่ใน 1,000 รายการล่าสุด → เปิดไฟล์รายการเก่าต่อ
    older = [f["name"] for f in sub["filings"].get("files", [])]
    for idx in range(len(older) + 1):
        if idx > 0:
            pages = [json.loads(_get(f"https://data.sec.gov/submissions/{older[idx - 1]}"))]
        r = pages[0]
        # ใช้ 10-K ฉบับจริง (ฉบับแก้ไข 10-K/A มักมีแค่ส่วนผู้บริหาร ไม่มีงบการเงิน — เช่น Tesla)
        for i, form in enumerate(r["form"]):
            if form == "10-K":
                return {"acc": r["accessionNumber"][i], "report_date": r["reportDate"][i],
                        "doc": r["primaryDocument"][i], "name": sub.get("name")}
        if idx >= 1:
            break
    return None


# ---------- 3–5) อ่าน XBRL ----------
def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _labels(xml: bytes) -> dict:
    """ไฟล์ป้ายชื่อ → {prefix_ElementName: ป้ายที่อ่านง่าย} (ชอบ terseLabel ก่อน label ปกติ)"""
    root = ET.fromstring(xml)
    XL = "{http://www.w3.org/1999/xlink}"
    out, rank = {}, {}
    for link in root.iter():
        if _local(link.tag) != "labelLink":
            continue
        loc = {e.get(XL + "label"): e.get(XL + "href", "").split("#")[-1]
               for e in link if _local(e.tag) == "loc"}
        res = {}
        for e in link:
            if _local(e.tag) == "label":
                res.setdefault(e.get(XL + "label"), []).append((e.get(XL + "role", ""), (e.text or "").strip()))
        for e in link:
            if _local(e.tag) == "labelArc":
                el = loc.get(e.get(XL + "from"))
                for role, text in res.get(e.get(XL + "to"), []):
                    r = 0 if role.endswith("terseLabel") else 1 if role.endswith("/label") else 2
                    if el and text and r < rank.get(el, 9):
                        out[el], rank[el] = text, r
    return out


def _pretty(member: str, labels: dict) -> str:
    if member == "_unallocated":
        return "Not broken out"
    key = member.replace(":", "_")
    if key in labels:
        return re.sub(r"\s*\[Member\]\s*$", "", labels[key]).strip()
    # ไม่มีไฟล์ป้ายชื่อ (เช่น Microsoft) → แยกคำจากชื่อในโค้ด แล้วแก้คำที่พบบ่อย
    name = member.split(":")[-1]
    name = re.sub(r"(Segment)?Member$", "", name)
    name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name).strip()
    for a, b in (("Three Six Five", "365"), ("Linked In", "LinkedIn"), ("You Tube", "YouTube"),
                 ("Non Us", "Non-US"), (" Corporation", ""), ("And", "&")):
        name = name.replace(a, b)
    return name


def _parse(instance: bytes, labels: dict) -> dict:
    root = ET.fromstring(instance)
    contexts = {}
    for ctx in root.iter():
        if _local(ctx.tag) != "context":
            continue
        start = end = None
        dims = {}
        for e in ctx.iter():
            n = _local(e.tag)
            if n == "startDate":
                start = e.text
            elif n == "endDate":
                end = e.text
            elif n == "explicitMember":
                dims[e.get("dimension", "").split(":")[-1]] = (e.text or "").strip()
            elif n == "typedMember":
                dims[e.get("dimension", "").split(":")[-1]] = "typed"
        if start and end:
            contexts[ctx.get("id")] = (start, end, dims)

    # facts[concept][(axis หรือ None)] = {(start, end, member): value}
    facts = {}
    for e in root:
        concept = _local(e.tag)
        if concept not in REVENUE_CONCEPTS or e.get("contextRef") not in contexts:
            continue
        try:
            v = float(e.text)
        except (TypeError, ValueError):
            continue
        start, end, dims = contexts[e.get("contextRef")]
        # ป้าย "เป็นส่วนงานดำเนินงาน" (ConsolidationItemsAxis = OperatingSegments) ไม่ใช่การแบ่งกลุ่มเพิ่ม → ตัดทิ้ง
        # (Apple, Tesla ฯลฯ รายงานรายได้ตามกลุ่มธุรกิจคู่กับป้ายนี้)
        if dims.get("ConsolidationItemsAxis", "").endswith("OperatingSegmentsMember"):
            dims = {k: v for k, v in dims.items() if k != "ConsolidationItemsAxis"}
        if len(dims) > 1:
            continue
        axis, member = next(iter(dims.items())) if dims else (None, None)
        facts.setdefault(concept, {}).setdefault(axis, {})[(start, end, member)] = v

    out = {}
    for kind, axis_names in AXES.items():
        for concept in REVENUE_CONCEPTS:
            byaxis = facts.get(concept, {})
            axis = next((a for a in axis_names if a in byaxis), None)
            if not axis:
                continue
            total = byaxis.get(None, {})
            years = {}
            for (start, end, member), v in byaxis[axis].items():
                days = (_d(end) - _d(start)).days
                if 340 <= days <= 380 and member != "typed":     # เฉพาะตัวเลขทั้งปี
                    years.setdefault(end, {})[member] = v
            if not years:
                continue
            series = []
            for end in sorted(years)[-3:]:
                items = _dedupe(years[end], next((tv for (s, e2, _), tv in total.items()
                                                  if e2 == end and 340 <= (_d(e2) - _d(s)).days <= 380), None))
                series.append({"end": end, "total": items["total"],
                               "items": [{"name": _pretty(m, labels), "member": m, "value": v}
                                         for m, v in sorted(items["parts"].items(), key=lambda kv: -kv[1])],
                               "deductions": [{"name": _pretty(m, labels), "value": v}
                                              for m, v in (items.get("deductions") or {}).items()]})
            if series and len(series[-1]["items"]) >= 2:
                out[kind] = {"concept": concept, "years": series}
                break
    return out


def _d(s):
    from datetime import date
    return date.fromisoformat(s)


def _dedupe(parts: dict, total):
    """บางบริษัทรายงานทั้ง "กลุ่มใหญ่" และ "กลุ่มย่อย" บนแกนเดียวกัน (ผลรวมเกินรายได้รวม)
    → ตัดกลุ่มใหญ่ที่เท่ากับผลรวมของกลุ่มอื่นบางส่วนออก จนผลรวมไม่เกินรายได้รวมเกิน 2%"""
    from itertools import combinations
    negatives = {m: v for m, v in parts.items() if v < 0}      # รายการหักออก เช่น Visa "Client incentives"
    parts = {m: v for m, v in parts.items() if v > 0}
    neg = sum(negatives.values())

    def fits(p, with_neg):
        return abs(sum(p.values()) + (neg if with_neg else 0) - total) <= total * 0.02

    over = total and total > 0 and sum(parts.values()) > total * 1.02     # ซ้อนกัน = ผลรวม "เกิน" เท่านั้น
    if over and not (negatives and fits(parts, True)):
        # 1) ส่วนเกินเท่ากับ 1–2 รายการพอดี → รายการนั้นคือการแบ่งอีกแบบที่ซ้อนอยู่
        #    (เช่น Microsoft/Disney "Product", JPM "Total international", Visa "Value-Added Services")
        #    ลองทั้งแบบไม่รวม และรวมรายการหักออก — เลือกชุดที่ใกล้ที่สุด
        best = None
        for with_neg in ([False, True] if negatives else [False]):
            excess = sum(parts.values()) + (neg if with_neg else 0) - total
            if excess <= total * 0.02:
                continue
            for k in (1, 2):
                for c in combinations(parts, k):
                    diff = abs(sum(parts[m] for m in c) - excess)
                    if diff <= total * 0.005 and (best is None or (k, diff) < best[:2]):
                        best = (k, diff, c, with_neg)
            if best:
                break
        if best:
            for m in best[2]:
                parts.pop(m)
        # 2) ยังไม่ลงตัว → ตัด "ยอดรวมย่อย" (= ผลรวมของรายการอื่นตั้งแต่ 2 ตัว) ไล่จากตัวใหญ่สุด
        #    เช่น Tesla "Automotive revenues" = ขายรถ + เครดิต + ให้เช่า
        if not fits(parts, False) and not (negatives and fits(parts, True)):
            for m in sorted(parts, key=parts.get, reverse=True):
                others = [o for o in parts if o != m and parts[o] < parts[m]]
                if len(others) > 14:
                    continue
                tol = parts[m] * 0.005
                if any(abs(sum(parts[o] for o in c) - parts[m]) <= tol
                       for k in range(2, len(others) + 1) for c in combinations(others, k)):
                    parts.pop(m)
                    if fits(parts, False) or (negatives and fits(parts, True)):
                        break
    # ยอดบวกเกิน แต่รวมรายการหักออกแล้วเท่ารายได้รวม → แสดงยอดก่อนหัก พร้อมบอกยอดที่หัก (เช่น Visa)
    if total and negatives and not fits(parts, False) and fits(parts, True):
        return {"parts": parts, "total": total, "deductions": negatives}
    if total and total > 0:
        # 3) ยังเกินอยู่ → ตัดตัวใหญ่สุดทีละตัว
        while sum(parts.values()) > total * 1.02 and len(parts) > 2:
            # ตัดตัวที่ "ใหญ่ที่สุด" ก่อน (กลุ่มแม่มักใหญ่กว่ากลุ่มลูก)
            big = max(parts, key=parts.get)
            rest = sum(parts.values()) - parts[big]
            if rest < total * 0.9:
                break
            parts.pop(big)
        # ผลรวม "ขาด" (บริษัทแยกให้ดูแค่บางส่วน เช่น Disney) → เติมส่วนที่เหลือเป็น "ไม่ได้แยกรายละเอียด"
        gap = total - sum(parts.values())
        if gap > total * 0.02:
            parts["_unallocated"] = gap
    return {"parts": parts, "total": total if total else sum(parts.values())}


def segments(ticker: str) -> dict:
    """โครงสร้างรายได้จาก 10-K ล่าสุด
    คืนค่า {"company", "form", "report_date", "url", "product"/"segment"/"region": {...}}  หรือ {} ถ้าหาไม่ได้
    โยน NeedContact ถ้ายังไม่ได้ตั้งอีเมล"""
    cik = _cik(ticker)
    if not cik:
        return {}
    f = _latest_10k(cik)
    if not f:
        return {}
    acc = f["acc"].replace("-", "")
    cache = ROOT / f"{cik}_{acc}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/"
    files = [x["name"] for x in json.loads(_get(base + "index.json"))["directory"]["item"]]
    inst = next((n for n in files if n.endswith("_htm.xml")), None) or \
        next((n for n in files if re.search(r"\d{8}\.xml$", n) and "_" not in n), None)
    if not inst:
        return {}
    lab = next((n for n in files if n.endswith("_lab.xml")), None)
    labels = _labels(_get(base + lab)) if lab else {}
    data = _parse(_get(base + inst), labels)
    data.update({"company": f["name"], "form": "10-K", "report_date": f["report_date"], "url": base + f["doc"]})
    ROOT.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data
