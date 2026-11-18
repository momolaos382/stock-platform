# =====================================================
# data.py — ดึงข้อมูลหุ้นจาก Yahoo Finance (ผ่านไลบรารี yfinance)
#   load_stock(symbol)   → ข้อมูลหุ้น 1 ตัว (ราคา 10 ปี + งบการเงินรายปี)
#   load_many(symbols)   → หลายตัวพร้อมกัน (ใช้เทียบคู่แข่ง)
#   load_quotes(symbols) → ราคาล่าสุด + % เปลี่ยนแปลง (ใช้ในหน้าหลัก)
# ผลลัพธ์ถูกจำไว้ (cache) เพื่อไม่ต้องดึงซ้ำทุกครั้งที่กดปุ่ม
# =====================================================
import os
import re
import shutil
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor


def _fix_cert_path():
    """แก้ปัญหา: ถ้าโฟลเดอร์โปรเจกต์มีอักษรที่ไม่ใช่ภาษาอังกฤษ (เช่น ชื่อโฟลเดอร์ภาษาลาว)
    ตัวเชื่อมต่อเน็ตของ yfinance จะเปิดไฟล์ใบรับรอง SSL ไม่ได้
    → คัดลอกไฟล์ใบรับรองไปไว้โฟลเดอร์ที่ชื่อเป็นภาษาอังกฤษล้วน แล้วชี้ไปที่นั่นแทน
    (ต้องทำก่อน import yfinance)"""
    if any(os.environ.get(k) for k in ("SSL_CERT_FILE", "CURL_CA_BUNDLE", "REQUESTS_CA_BUNDLE")):
        return
    try:
        import certifi
        src = certifi.where()
        if src.isascii():
            return
        for base in (os.environ.get("LOCALAPPDATA"), tempfile.gettempdir()):
            if base and base.isascii():
                dst_dir = os.path.join(base, "stock-platform")
                os.makedirs(dst_dir, exist_ok=True)
                dst = os.path.join(dst_dir, "cacert.pem")
                if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src):
                    shutil.copyfile(src, dst)
                os.environ["CURL_CA_BUNDLE"] = dst
                return
    except Exception:
        pass  # ถ้าแก้ไม่ได้ ปล่อยให้ yfinance แจ้ง error เอง


_fix_cert_path()

import pandas as pd          # noqa: E402
import streamlit as st       # noqa: E402
import yfinance as yf        # noqa: E402

# ข้อมูลบริษัทที่เราใช้จาก Yahoo (เลือกเฉพาะที่จำเป็น)
INFO_KEYS = [
    "shortName", "longName", "sector", "industry", "currency", "financialCurrency",
    "fullExchangeName", "exchange", "currentPrice", "previousClose", "marketCap",
    "trailingEps", "trailingPE", "bookValue", "beta", "dividendRate",
    "longBusinessSummary", "country",
    # ข้อมูลบริษัท (แท็บ "บริษัท")
    "website", "irWebsite", "fullTimeEmployees", "address1", "city", "state", "zip", "phone", "companyOfficers",
]

# กลุ่มหุ้นที่รู้จักกันดี ใช้สำหรับ "เทียบกับคู่แข่ง" และรายการแนะนำในหน้าหลัก
# รูปแบบ: ชื่อย่อ: (ชื่อบริษัท, กลุ่มอุตสาหกรรม)   หุ้นไทยลงท้ายด้วย .BK
UNIVERSE = {
    "AAPL": ("Apple", "Technology"), "MSFT": ("Microsoft", "Technology"),
    "NVDA": ("NVIDIA", "Technology"), "ORCL": ("Oracle", "Technology"),
    "CSCO": ("Cisco", "Technology"), "ADBE": ("Adobe", "Technology"),
    "GOOGL": ("Alphabet", "Communication Services"), "META": ("Meta Platforms", "Communication Services"),
    "NFLX": ("Netflix", "Communication Services"), "DIS": ("Walt Disney", "Communication Services"),
    "AMZN": ("Amazon", "Consumer Cyclical"), "TSLA": ("Tesla", "Consumer Cyclical"),
    "HD": ("Home Depot", "Consumer Cyclical"), "MCD": ("McDonald's", "Consumer Cyclical"),
    "NKE": ("Nike", "Consumer Cyclical"),
    "KO": ("Coca-Cola", "Consumer Defensive"), "PEP": ("PepsiCo", "Consumer Defensive"),
    "WMT": ("Walmart", "Consumer Defensive"), "PG": ("Procter & Gamble", "Consumer Defensive"),
    "COST": ("Costco", "Consumer Defensive"),
    "JPM": ("JPMorgan Chase", "Financial Services"), "BAC": ("Bank of America", "Financial Services"),
    "V": ("Visa", "Financial Services"), "MA": ("Mastercard", "Financial Services"),
    "JNJ": ("Johnson & Johnson", "Healthcare"), "PFE": ("Pfizer", "Healthcare"),
    "UNH": ("UnitedHealth", "Healthcare"), "LLY": ("Eli Lilly", "Healthcare"),
    "XOM": ("Exxon Mobil", "Energy"), "CVX": ("Chevron", "Energy"),
    "PTT.BK": ("PTT", "Energy"), "PTTEP.BK": ("PTT Exploration & Production", "Energy"),
    "CPALL.BK": ("CP ALL", "Consumer Defensive"), "CPF.BK": ("Charoen Pokphand Foods", "Consumer Defensive"),
    "KBANK.BK": ("Kasikornbank", "Financial Services"), "SCB.BK": ("SCB X", "Financial Services"),
    "BBL.BK": ("Bangkok Bank", "Financial Services"),
    "ADVANC.BK": ("Advanced Info Service", "Communication Services"), "TRUE.BK": ("True Corporation", "Communication Services"),
    "AOT.BK": ("Airports of Thailand", "Industrials"), "BEM.BK": ("Bangkok Expressway & Metro", "Industrials"),
}

from core import lao  # noqa: E402

_SYMBOL_RE = re.compile(r"^[A-Z0-9.\-^=]{1,15}$")


def universe() -> dict:
    """หุ้นทั้งหมดที่ระบบรู้จัก = สหรัฐฯ + ไทย (UNIVERSE) + ลาว (อ่านจากไฟล์ใน data/lao)"""
    return {**UNIVERSE, **lao.universe()}


_LAO_SYNC = {"running": False, "at": 0.0}
_LAO_LOCK = threading.Lock()


def lao_sync_at() -> float:
    """เวลาที่ดึงข้อมูลหุ้นลาวเสร็จล่าสุด (0 = ยังไม่เคย) — ใช้กับการแจ้งเตือน"""
    return _LAO_SYNC["at"]


def refresh_lao(every_hours: float = 6):
    """อัปเดตราคาหุ้นลาวจากเว็บ LSX แบบเบื้องหลัง (ไม่ทำให้หน้าเว็บค้าง)
    ทำอย่างมาก 1 ครั้งทุก 6 ชั่วโมง ดึงเฉพาะวันที่ยังไม่มี / เน็ตใช้ไม่ได้ → ใช้ข้อมูลเดิมในเครื่อง"""
    with _LAO_LOCK:
        if _LAO_SYNC["running"] or time.time() - _LAO_SYNC["at"] < every_hours * 3600:
            return
        _LAO_SYNC["running"] = True

    def work():
        try:
            try:
                lao.sync()                   # ราคา + ดัชนี
            except Exception:
                pass
            try:
                from core import lao_fundamentals
                lao_fundamentals.sync()      # งบการเงินจาก Factsheet (ทำเฉพาะเมื่อมีไฟล์ใหม่)
            except Exception:
                pass
            try:
                from core import lao_profile
                lao_profile.sync_profiles()  # โปรไฟล์บริษัท/กรรมการ จาก Factsheet ฉบับล่าสุด
            except Exception:
                pass
            st.cache_data.clear()            # ให้ทุกหน้าเห็นข้อมูลใหม่
        finally:
            _LAO_SYNC.update(running=False, at=time.time())

    threading.Thread(target=work, daemon=True).start()


def market_of(symbol: str) -> str:
    """'LA' หุ้นลาว / 'TH' หุ้นไทย / 'US' อื่นๆ"""
    return "LA" if lao.is_lao(symbol) else "TH" if symbol.endswith(".BK") else "US"


class StockNotFound(Exception):
    """ไม่พบหุ้น หรือดึงข้อมูลไม่สำเร็จ"""


def clean_symbol(text: str):
    """ทำความสะอาดชื่อย่อหุ้นที่ผู้ใช้พิมพ์ → ตัวพิมพ์ใหญ่ / คืน None ถ้ารูปแบบผิด"""
    s = (text or "").strip().upper()
    if s + lao.SUFFIX in lao.universe():      # พิมพ์ BCEL เฉยๆ ก็รู้ว่าเป็นหุ้นลาว
        return s + lao.SUFFIX
    return s if _SYMBOL_RE.match(s) else None


def _statement(getter) -> pd.DataFrame:
    try:
        df = getter()
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _fetch(symbol: str) -> dict:
    """ดึงข้อมูลดิบของหุ้น 1 ตัว (ไม่ cache — ให้ฟังก์ชันด้านล่างเป็นคน cache)"""
    if lao.is_lao(symbol):
        try:
            return lao.load(symbol)
        except Exception as e:
            raise StockNotFound(symbol) from e
    tk = yf.Ticker(symbol)
    try:
        # ราคาปิดรายเดือนย้อนหลัง 10 ปี (ปรับการแตกหุ้นแล้ว แต่ไม่รวมปันผล)
        price = tk.history(period="10y", interval="1mo", auto_adjust=False)["Close"].dropna()
    except Exception as e:
        raise StockNotFound(symbol) from e
    if price.empty:
        raise StockNotFound(symbol)
    price.index = price.index.tz_localize(None)
    try:
        info = dict(tk.info or {})
    except Exception:
        info = {}
    return {
        "symbol": symbol,
        "info": {k: info.get(k) for k in INFO_KEYS},
        "price": price,
        "fin": _statement(lambda: tk.financials),      # งบกำไรขาดทุน (รายปี)
        "bs": _statement(lambda: tk.balance_sheet),    # งบดุล
        "cf": _statement(lambda: tk.cashflow),         # งบกระแสเงินสด
    }


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def load_stock(symbol: str) -> dict:
    """ข้อมูลหุ้น 1 ตัว (จำไว้ 6 ชั่วโมง)"""
    return _fetch(symbol)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def load_many(symbols: tuple) -> dict:
    """ดึงหลายตัวพร้อมกัน (ตัวไหนดึงไม่ได้จะถูกข้าม)"""
    def one(sym):
        try:
            return sym, _fetch(sym)
        except Exception:
            return sym, None
    with ThreadPoolExecutor(max_workers=4) as pool:
        return {s: d for s, d in pool.map(one, symbols) if d}


@st.cache_data(ttl=900, show_spinner=False)
def load_quotes(symbols: tuple) -> dict:
    """ราคาล่าสุด, % เปลี่ยนแปลงจากวันก่อน และราคา 1 เดือน (สำหรับเส้นกราฟจิ๋ว)"""
    out = {}
    for s in symbols:                       # หุ้นลาวอ่านจากไฟล์ในเครื่อง
        if lao.is_lao(s):
            try:
                c = lao.daily(s).tail(22)
                if len(c) >= 2:
                    out[s] = {"price": float(c.iloc[-1]), "chg": float(c.iloc[-1] / c.iloc[-2] - 1),
                              "spark": [float(x) for x in c]}
            except Exception:
                pass
    symbols = tuple(s for s in symbols if not lao.is_lao(s))
    if not symbols:
        return out
    try:
        close = yf.download(list(symbols), period="1mo", interval="1d",
                            auto_adjust=False, progress=False, threads=True)["Close"]
    except Exception:
        return out
    for s in symbols:
        if s in close:
            c = close[s].dropna()
            if len(c) >= 2:
                out[s] = {"price": float(c.iloc[-1]), "chg": float(c.iloc[-1] / c.iloc[-2] - 1),
                          "spark": [float(x) for x in c]}
    return out


def _records(getter, limit=None) -> list:
    """DataFrame จาก yfinance → list ของ dict (ดึงไม่ได้/ว่าง → [])"""
    try:
        df = getter()
        if not isinstance(df, pd.DataFrame) or df.empty:
            return []
        df = df.reset_index() if df.index.name else df
        rows = df.head(limit) if limit else df
        return [{k: (None if pd.isna(v) else (v.isoformat()[:10] if hasattr(v, "isoformat") else v))
                 for k, v in r.items()} for r in rows.to_dict("records")]
    except Exception:
        return []


def _news(tk, limit=12) -> list:
    """ข่าวล่าสุด: หัวข้อ, สำนักข่าว, วันที่, ลิงก์, สรุป, รูปย่อ"""
    out = []
    try:
        items = tk.news or []
    except Exception:
        return out
    for it in items[:limit]:
        c = it.get("content", it) or {}
        url = (c.get("clickThroughUrl") or {}).get("url") or (c.get("canonicalUrl") or {}).get("url") or c.get("link")
        thumb = None
        for r in ((c.get("thumbnail") or {}).get("resolutions") or []):
            if r.get("tag") == "170x128":
                thumb = r.get("url")
        if c.get("title") and url:
            out.append({"title": c["title"], "summary": c.get("summary") or "", "url": url, "thumb": thumb,
                        "publisher": (c.get("provider") or {}).get("displayName") or c.get("publisher") or "",
                        "date": (c.get("pubDate") or "")[:10]})
    return out


@st.cache_data(ttl=12 * 3600, show_spinner=False)
def load_profile(symbol: str) -> dict:
    """ข้อมูลเชิงลึกของบริษัท (หุ้นสหรัฐฯ ครบที่สุด): สัดส่วนผู้ถือหุ้น, สถาบัน/กองทุนที่ถือ,
    ผู้บริหารที่ถือหุ้น, การซื้อขายของผู้บริหาร, ข่าว  — หุ้นลาวยังไม่มีแหล่งข้อมูลนี้ → {}"""
    if lao.is_lao(symbol):
        return {}
    tk = yf.Ticker(symbol)
    major = {}
    try:
        mh = tk.major_holders
        if isinstance(mh, pd.DataFrame) and not mh.empty:
            major = {str(k): float(v) for k, v in mh.iloc[:, 0].items()}
    except Exception:
        pass
    return {
        "major": major,
        "institutions": _records(lambda: tk.institutional_holders, 10),
        "funds": _records(lambda: tk.mutualfund_holders, 10),
        "insiders": _records(lambda: tk.insider_roster_holders, 12),
        "insider_tx": _records(lambda: tk.insider_transactions, 15),
        "news": _news(tk),
    }


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def load_segments(symbol: str) -> dict:
    """โครงสร้างรายได้แยกตามธุรกิจ/ภูมิภาค จากรายงาน 10-K (เฉพาะหุ้นสหรัฐฯ)
    คืนค่า {} ถ้าไม่มีข้อมูล / {"need_contact": True} ถ้ายังไม่ได้ตั้งอีเมลสำหรับ SEC"""
    if market_of(symbol) != "US":
        return {}
    from core import sec
    try:
        return sec.segments(symbol)
    except sec.NeedContact:
        return {"need_contact": True}
    except Exception:
        return {}


@st.cache_data(ttl=1800, show_spinner=False)
def load_lao_news(symbol: str, lang: str) -> dict:
    """ประกาศของบริษัท + ข่าวตลาดหลักทรัพย์ลาว (ดึงสดจาก LSX แคช 30 นาที / ดึงไม่ได้ → ว่าง)"""
    from core import lao_profile
    code = lao.code_of(symbol)
    return {"company": lao_profile.disclosures(code, lang), "market": lao_profile.market_news(lang)}


def benchmark_of(symbol: str) -> tuple:
    """ตลาดที่ใช้เทียบ   คืนค่า (ชื่อย่อ Yahoo, ชื่อที่แสดง)
    หุ้นไทย → กองทุน TDEX ที่ลงทุนตามดัชนี SET50 (Yahoo ไม่มีข้อมูลย้อนหลังของดัชนี SET โดยตรง)
    อื่นๆ   → ดัชนี S&P 500"""
    if lao.is_lao(symbol):
        return ("LSXC", "LSX Composite")
    return ("TDEX.BK", "SET50") if symbol.endswith(".BK") else ("^GSPC", "S&P 500")


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def load_daily(symbol: str) -> pd.DataFrame:
    """ราคาปิดรายวันย้อนหลัง 5 ปี (รวมปันผลแล้ว) ของหุ้น + ดัชนีตลาด
    คืนตาราง 2 คอลัมน์: stock, bench   ใช้ในหน้าวัดความเสี่ยง"""
    bench = benchmark_of(symbol)[0]
    if lao.is_lao(symbol):
        try:
            s = lao.daily(symbol)
        except Exception as e:
            raise StockNotFound(symbol) from e
        idx = lao.index_daily()               # ไม่มีไฟล์ดัชนี → ไม่มีค่า Beta (หน้าความเสี่ยงรองรับอยู่แล้ว)
        df = pd.DataFrame({"stock": s, "bench": idx if idx is not None else float("nan")})
        return df.dropna(subset=["stock"]).tail(5 * 252)
    try:
        close = yf.download([symbol, bench], period="5y", interval="1d",
                            auto_adjust=True, progress=False, threads=True)["Close"]
    except Exception as e:
        raise StockNotFound(symbol) from e
    if symbol not in close or close[symbol].dropna().empty:
        raise StockNotFound(symbol)
    df = pd.DataFrame({"stock": close[symbol],
                       "bench": close[bench] if bench in close else float("nan")})
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df.dropna(subset=["stock"])


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def load_prices(symbols: tuple) -> pd.DataFrame:
    """ราคาปิดรายวันย้อนหลัง 3 ปี (รวมปันผล) ของหุ้นหลายตัว — 1 คอลัมน์ = 1 หุ้น
    ใช้ในหน้าจัดสรรพอร์ต  (หุ้นที่ดึงไม่ได้หรือข้อมูลน้อยเกินไปจะถูกตัดออก)"""
    la = [s for s in symbols if lao.is_lao(s)]
    other = [s for s in symbols if not lao.is_lao(s)]
    parts = []
    if other:
        try:
            close = yf.download(other, period="3y", interval="1d",
                                auto_adjust=True, progress=False, threads=True)["Close"]
            if isinstance(close, pd.Series):
                close = close.to_frame(other[0])
            close.index = pd.to_datetime(close.index).tz_localize(None)
            parts.append(close)
        except Exception:
            pass
    for s in la:
        try:
            parts.append(lao.daily(s).rename(s).tail(3 * 252).to_frame())
        except Exception:
            pass
    if not parts:
        return pd.DataFrame()
    close = pd.concat(parts, axis=1)
    keep = [s for s in symbols if s in close and close[s].notna().sum() > 120]
    return close[keep].dropna()


def peers_of(symbol: str, sector: str, limit: int = 5) -> list:
    """หาคู่แข่ง: หุ้นในกลุ่มอุตสาหกรรมเดียวกันและตลาดเดียวกัน จากรายการ UNIVERSE"""
    mk = market_of(symbol)
    same = [s for s, (_, sec) in universe().items()
            if sec == sector and s != symbol and market_of(s) == mk]
    return same[:limit]
