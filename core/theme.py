# =====================================================
# theme.py — ระบบดีไซน์ (Design System) ของทั้งเว็บ
#   - โทนสี สว่าง (light) / มืด (dark)  → แก้ค่าใน THEMES
#   - CSS ของการ์ด ปุ่ม เมนู ตาราง        → แก้ใน CSS ด้านล่าง
# แนวดีไซน์: แถบเมนูสีเข้ม + พื้นที่เนื้อหาโค้งมน + การ์ดสีพาสเทล
# =====================================================
import streamlit as st

THEMES = {
    "light": {
        "canvas": "radial-gradient(900px 520px at 90% -10%, rgba(183,171,255,.50), transparent 62%), "
                  "radial-gradient(760px 420px at 0% 105%, rgba(212,242,92,.40), transparent 62%), #E9EAE4",
        "bg": "#E9EAE4",
        "panel": "rgba(255,255,255,.92)",   # แผ่นเนื้อหาหลัก (กึ่งโปร่งแสง)
        "panel_line": "rgba(255,255,255,.9)",
        "surface": "#FFFFFF",
        "surface2": "#F4F4EF",
        "ink": "#111113",
        "muted": "#66676E",
        "border": "#E3E3DC",
        "accent": "#5B3FE0",      # สีเน้น + เส้นในกราฟ (ม่วงเข้มบนพื้นขาว)
        "accent_ink": "#FFFFFF",
        "series2": "#E8590C",
        "series3": "#12A670",
        "series4": "#D99100",
        "good": "#0E7F4F",
        "bad": "#C73535",
        "warn": "#946200",
        "tint_blue": "rgba(91,63,224,.08)",
        "tint_lav": "rgba(155,140,255,.18)",
        "tint_mint": "#DDF3E7",
        "tint_cream": "#F8EFD2",
        "lime": "#D4F25C", "lime_ink": "#121310",       # การ์ดเน้น (เขียวมะนาว)
        "violet": "#B7ABFF", "violet_ink": "#14112A",   # การ์ดเน้น (ม่วงอ่อน)
        "btn": "#111113", "btn_ink": "#FFFFFF",
        "side": "#111113",
        "side_ink": "#F3F3EE",
        "side_muted": "#8C8D94",
        "side_active": "#D4F25C",
        "side_active_ink": "#121310",
        "cta": "linear-gradient(135deg, #5B3FE0 0%, #3A27A6 100%)",
        "cta_ink": "#FFFFFF",
    },
    "dark": {
        "canvas": "radial-gradient(900px 520px at 88% -8%, rgba(169,155,255,.34), transparent 62%), "
                  "radial-gradient(760px 420px at 4% 108%, rgba(212,242,92,.12), transparent 62%), #1A1A1D",
        "bg": "#1A1A1D",
        "panel": "rgba(19,19,21,.90)",
        "panel_line": "rgba(255,255,255,.07)",
        "surface": "#141416",
        "surface2": "#1D1E21",
        "ink": "#F3F3EE",
        "muted": "#9B9CA3",
        "border": "#2B2C31",
        "accent": "#D4F25C",
        "accent_ink": "#121310",
        "series2": "#A99BFF",
        "series3": "#4FD8A0",
        "series4": "#FFB547",
        "good": "#5BE3A4",
        "bad": "#FF7A7A",
        "warn": "#F2C14E",
        "tint_blue": "rgba(212,242,92,.10)",
        "tint_lav": "rgba(169,155,255,.14)",
        "tint_mint": "rgba(79,216,160,.12)",
        "tint_cream": "rgba(255,181,71,.12)",
        "lime": "#D4F25C", "lime_ink": "#121310",
        "violet": "#A99BFF", "violet_ink": "#14112A",
        "btn": "#D4F25C", "btn_ink": "#121310",
        "side": "#0D0D0F",
        "side_ink": "#F3F3EE",
        "side_muted": "#8C8D94",
        "side_active": "#D4F25C",
        "side_active_ink": "#121310",
        "cta": "linear-gradient(135deg, #53345F 0%, #2C1F37 55%, #1B1621 100%)",
        "cta_ink": "#F7F0FB",
    },
}


def tokens() -> dict:
    """คืนค่าชุดสีของธีมที่ใช้อยู่ตอนนี้ (ใช้ตอนวาดกราฟ)"""
    return THEMES.get(st.session_state.get("theme", "light"), THEMES["light"])


# ฟอนต์: Plus Jakarta Sans (อังกฤษ/ตัวเลข) + Noto Sans Lao (ลาว — แบบหัวตรง สมัยใหม่ ไม่ใช่แบบ "หัวม้วน/ดอกจำปา")
# ทั้งสองมีน้ำหนักหลายระดับ (บาง 300 → หนา 800) ใช้ทำหัวข้อหนา/ตัวบางสำหรับคำอธิบาย
# ต้องเป็นบล็อก <style> แยกและอยู่ "ก่อน" CSS อื่น เพราะ @import ต้องอยู่บนสุดของสไตล์ชีต ไม่งั้นเบราว์เซอร์ข้ามไป
#
# ฟอนต์ลาว: ไฟล์ Noto Sans Lao ที่ผู้ใช้เตรียมไว้ ฝังในโปรเจกต์ที่ static/fonts/ (6 น้ำหนัก: บาง 300 → หนาพิเศษ 800)
# ใช้เฉพาะตัวอักษรลาว (unicode-range U+0E80–0EFF) — ตัวอังกฤษ/ตัวเลขใช้ Plus Jakarta Sans จึงไม่ปนกัน
# เว็บเรียกไฟล์ผ่าน /app/static/... (เปิดด้วย enableStaticServing ใน .streamlit/config.toml)
_LAO_WEIGHTS = (("Light", 300), ("Regular", 400), ("Medium", 500), ("SemiBold", 600), ("Bold", 700), ("ExtraBold", 800))
FONT_CSS = ("@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300..800&family=Noto+Sans+Lao:wght@300..800&display=swap');\n"
            + "\n".join(
                "@font-face{font-family:'Lao Local';font-style:normal;font-weight:%d;font-display:swap;"
                "src:url('/app/static/fonts/NotoSansLao-%s.ttf') format('truetype');"
                "unicode-range:U+0E80-0EFF,U+200B-200D,U+2022;}" % (w, name) for name, w in _LAO_WEIGHTS))
# ลำดับ: ลาว(ฝังเอง) → อังกฤษ → ตัวสำรอง (ใช้ก็ต่อเมื่อไฟล์ฝังโหลดไม่ได้จริงๆ)
# ตัวที่ 3 'Noto Sans Lao' (จาก Google, ฟอนต์ตระกูลเดียวกับไฟล์ที่ฝัง) ใช้เมื่อโฮสต์ไม่เปิดให้เรียกไฟล์ฝัง เช่น Streamlit Cloud
FONT_STACK = "'Lao Local', 'Plus Jakarta Sans', 'Noto Sans Lao', 'Noto Sans Lao UI', 'Leelawadee UI', sans-serif"
FONT_PLOTLY = "Lao Local, Plus Jakarta Sans, Noto Sans Lao, Noto Sans Lao UI, Leelawadee UI, sans-serif"

# ภาษาลาวมีสระ/วรรณยุกต์ซ้อนบน-ล่าง → ต้องเว้นบรรทัดกว้างกว่าอังกฤษ ไม่งั้นเครื่องหมายชนบรรทัดบน/ล่าง
LAO_CSS = """
.stApp p, .stApp li, .stApp label, .stApp td, .stApp th, .stApp span, .stApp button { line-height: 1.65; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { line-height: 1.4; letter-spacing: 0; }
.stApp h1 { font-weight: 700; }
.tile .value, .stock-head .name, .stock-head .px, .hero-name { letter-spacing: 0; }
.eyebrow, .side-label { letter-spacing: .02em; text-transform: none; }
.tile .label, .stat .k, .sign .k, .co-grid .k { font-weight: 500; }
"""

CSS = """
/* บังคับ "ทุกองค์ประกอบ" ให้ใช้ฟอนต์ชุดเดียว (รวมเมนูที่เปิดลงมา, คำอธิบายเมื่อชี้, ตาราง, ช่องกรอก, ข้อความในกราฟ) */
html, body, .stApp, .stApp *, [data-baseweb="popover"], [data-baseweb="popover"] *,
[data-baseweb="tooltip"], [data-baseweb="tooltip"] *, [data-baseweb="menu"] *, [role="listbox"] *, [role="dialog"] *,
.stApp svg text, .stApp svg tspan, .stApp .js-plotly-plot .plotly text { font-family: %s !important; }
/* ไอคอนเป็น "ฟอนต์ไอคอน" ต้องคืนค่าไว้ ไม่งั้นแสดงเป็นข้อความ เช่น keyboard_double_arrow_left */
body [data-testid="stIconMaterial"], body .material-symbols-rounded, body [class*="material-symbols"],
body span[role="img"][translate="no"] { font-family: "Material Symbols Rounded" !important; }
""" % FONT_STACK + """
.stApp { background: var(--canvas); background-attachment: fixed; color: var(--ink); }
header[data-testid="stHeader"] { background: transparent; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp label, .stApp li { color: var(--ink); }
.stApp h1 { font-size: 1.9rem; font-weight: 800; letter-spacing: -0.02em; padding: 0 0 .2rem 0; }
.stApp h3 { font-size: 1.15rem; font-weight: 700; letter-spacing: -0.01em; }

/* ---------- แผ่นเนื้อหาหลัก: กล่องขาวมุมโค้ง ---------- */
[data-testid="stMainBlockContainer"] {
  background: var(--panel); border-radius: 32px; border: 1px solid var(--panel-line);
  -webkit-backdrop-filter: blur(22px); backdrop-filter: blur(22px);
  padding: 2rem 2.2rem 2.4rem; margin: 3.4rem auto 1.4rem;
  max-width: min(1320px, calc(100% - 2rem));
  box-shadow: 0 24px 70px rgba(0,0,0,.18);
}

/* ---------- แถบเมนูด้านข้าง (สีเข้มทั้งสองธีม) ---------- */
section[data-testid="stSidebar"] { background: var(--side); border-radius: 0; border: 0; }   /* เมนูเต็ม: ขอบเหลี่ยม ชิดซ้าย */
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] small { color: var(--side-ink); }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.12); }
.brand { display:flex; align-items:center; gap:.7rem; padding:.2rem 0 1rem; }
.brand .mark { width:42px; height:42px; border-radius:13px; background: var(--side-active);
  color: var(--side-active-ink); display:grid; place-items:center; font-weight:800; font-size:1.05rem; }
.brand .name { font-weight:800; font-size:1.05rem; color: var(--side-ink); line-height:1.1; }
.brand .tag { font-size:.72rem; color: var(--side-muted); }
.side-label { font-size:.7rem; letter-spacing:.08em; text-transform:uppercase; color: var(--side-muted) !important; margin:.6rem 0 .2rem; }

/* เมนูหลัก: แปลง radio ให้เป็นรายการเมนูแบบเม็ดยา */
.st-key-nav div[role="radiogroup"] { gap: .25rem; }
.st-key-nav label[data-testid="stRadioOption"] {
  width: 100%; padding: .62rem .8rem; border-radius: 14px; margin: 0; cursor: pointer;
  transition: background .15s ease;
}
.st-key-nav label[data-testid="stRadioOption"] > div > div:not([data-testid]) { display: none; }  /* ซ่อนวงกลม radio */
.st-key-nav label[data-testid="stRadioOption"]:hover { background: rgba(255,255,255,.08); }
.st-key-nav label[data-testid="stRadioOption"] p { font-weight: 600; font-size: .93rem; color: var(--side-ink); }
.st-key-nav label[data-testid="stRadioOption"] p span[role="img"] { margin-right: .45rem; vertical-align: -0.2em; }
.st-key-nav label[data-testid="stRadioOption"]:has(input:checked) { background: var(--side-active); }
.st-key-nav label[data-testid="stRadioOption"]:has(input:checked) p,
.st-key-nav label[data-testid="stRadioOption"]:has(input:checked) span { color: var(--side-active-ink) !important; }
.st-key-nav label[data-testid="stRadioOption"]:has(input:focus-visible) { outline: 2px solid var(--side-active); outline-offset: 2px; }
section[data-testid="stSidebar"] button[data-testid^="stBaseButton"] {
  background: transparent; border: 1px solid rgba(255,255,255,.18); border-radius: 12px;
}
section[data-testid="stSidebar"] button[data-testid^="stBaseButton"]:hover { background: rgba(255,255,255,.08); }

/* ---------- การ์ด (st.container ที่ตั้ง key ขึ้นต้นด้วย card) ---------- */
[class*="st-key-card"] {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: 26px; padding: 1.15rem 1.25rem 1.2rem;
}
/* การ์ดสีเด่น: ตั้งตัวแปรสีใหม่เฉพาะในการ์ด ลูกทุกชิ้นจึงเปลี่ยนเป็นตัวอักษรเข้มบนพื้นสดโดยอัตโนมัติ */
[class*="st-key-cardblue"], [class*="st-key-cardlav"] {
  border-color: transparent; --muted: rgba(18,19,16,.66); --border: rgba(18,19,16,.16);
  --surface2: rgba(18,19,16,.07); --btn: #121310; --btn-ink: #fff;
}
[class*="st-key-cardblue"] { background: var(--lime); --ink: var(--lime-ink); --surface: var(--lime); --accent: var(--lime-ink); }
[class*="st-key-cardlav"]  { background: var(--violet); --ink: var(--violet-ink); --surface: var(--violet); --accent: var(--violet-ink); }
[class*="st-key-cardblue"] .tone-good, [class*="st-key-cardlav"] .tone-good { color: #0A5C36 !important; }
[class*="st-key-cardblue"] .tone-bad,  [class*="st-key-cardlav"] .tone-bad  { color: #9B1C1C !important; }
[class*="st-key-cardmint"]  { background: var(--tint-mint);  border-color: transparent; }
[class*="st-key-cardcream"] { background: var(--tint-cream); border-color: transparent; }
[class*="st-key-cardcta"]   { background: var(--cta); border-color: transparent; }
[class*="st-key-cardcta"] p, [class*="st-key-cardcta"] h3 { color: var(--cta-ink) !important; }
[class*="st-key-cardcta"] .muted { color: var(--cta-ink) !important; opacity: .72; }
[class*="st-key-cardcta"] button { background: rgba(255,255,255,.16) !important; border: 1px solid rgba(255,255,255,.34) !important; border-radius: 999px !important; }
[class*="st-key-cardcta"] button p { color: var(--cta-ink) !important; }
[class*="st-key-cardcta"] .tile .label, [class*="st-key-cardcta"] .tile .value,
[class*="st-key-cardcta"] .tile .sub { color: var(--cta-ink); }

/* ---------- ปุ่ม ---------- */
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-secondary"],
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-secondaryFormSubmit"] {
  background: var(--surface); color: var(--ink); border: 1px solid var(--border);
  border-radius: 999px; font-weight: 600; padding: .35rem 1rem;
}
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-secondary"]:hover { border-color: var(--accent); color: var(--accent); }
.stApp button[data-testid="stBaseButton-primary"],
.stApp button[data-testid="stBaseButton-primaryFormSubmit"] {
  background: var(--btn); color: var(--btn-ink); border: 0; border-radius: 999px; font-weight: 700;
}
.stApp button[data-testid="stBaseButton-primary"] p,
.stApp button[data-testid="stBaseButton-primaryFormSubmit"] p { color: var(--btn-ink) !important; }
.stApp button[data-testid="stBaseButton-primary"]:hover,
.stApp button[data-testid="stBaseButton-primaryFormSubmit"]:hover { filter: brightness(1.1); box-shadow: 0 6px 20px rgba(0,0,0,.18); }
.stApp button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
/* ปุ่มเม็ดยา (pills / segmented control) */
.stApp [data-testid="stButtonGroup"] button {
  background: var(--surface); color: var(--ink); border: 1px solid var(--border); border-radius: 999px;
}
.stApp [data-testid="stButtonGroup"] button p { color: inherit !important; font-weight: 600; font-size: .85rem; }
.stApp [data-testid="stButtonGroup"] button:hover { border-color: var(--accent); color: var(--accent); }
.stApp [data-testid="stButtonGroup"] button[aria-checked="true"],
.stApp [data-testid="stButtonGroup"] button[aria-pressed="true"],
.stApp [data-testid="stButtonGroup"] button[data-selected="true"] {
  background: var(--btn) !important; color: var(--btn-ink) !important; border-color: var(--btn) !important;
}
.stApp [data-testid="stButtonGroup"] [role="radiogroup"], .stApp [data-testid="stButtonGroup"] [role="group"] { gap: .35rem; }

/* ---------- ช่องกรอกข้อมูล ---------- */
.stApp [data-testid="stMain"] [data-testid="stTextInputRootElement"] {
  background: var(--surface2); border-radius: 14px; border: 1px solid var(--border);
}
.stApp [data-testid="stMain"] [data-testid="stTextInputRootElement"]:focus-within { border-color: var(--accent); }
.stApp [data-testid="stMain"] [data-testid="stNumberInputContainer"] {
  background: var(--surface); border-radius: 14px; border: 1px solid var(--border); overflow: hidden;
}
.stApp [data-testid="stMain"] [data-testid="stNumberInputContainer"] > div { background: transparent; }
.stApp [data-testid="stMain"] [data-testid="stNumberInputContainer"] button { background: transparent; color: var(--muted); }
.stApp [data-testid="stMain"] [data-testid="stTextInputRootElement"] button { color: var(--muted); }
.stApp [data-testid="stMain"] input { color: var(--ink) !important; background: transparent; -webkit-text-fill-color: var(--ink); }
.stApp [data-testid="stMain"] input::placeholder { color: var(--muted); -webkit-text-fill-color: var(--muted); }
.stApp [data-testid="stMain"] [data-testid="stMultiSelect"] div:has(> [data-testid="stMultiSelectTagsContainer"]) {
  background: var(--surface); border-radius: 14px; border: 1px solid var(--border);
}
.stApp [data-testid="stMain"] [data-testid="stMultiSelect"] svg { color: var(--muted); fill: var(--muted); }
div[data-testid="stForm"] { border: 0; padding: 0; }
/* กล่องเลือก (selectbox), เมนูที่เปิดลงมา, ช่องข้อความหลายบรรทัด, ช่องอัปโหลดไฟล์ */
.stApp [data-testid="stMain"] [data-baseweb="select"] > div,
.stApp [data-testid="stMain"] textarea,
.stApp [data-testid="stMain"] [data-testid="stFileUploaderDropzone"] {
  background: var(--surface2) !important; border: 1px solid var(--border) !important; border-radius: 14px !important; color: var(--ink) !important;
}
.stApp [data-testid="stMain"] [data-baseweb="select"] * { color: var(--ink) !important; }
.stApp [data-testid="stMain"] [data-testid="stFileUploaderDropzone"] * { color: var(--ink) !important; }
[data-baseweb="popover"] ul, [data-baseweb="popover"] [role="listbox"] { background: var(--surface2) !important; }
[data-baseweb="popover"] li, [data-baseweb="popover"] [role="option"] { background: var(--surface2) !important; color: var(--ink) !important; }
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] [role="option"]:hover { background: var(--tint-blue) !important; }
.stApp [data-testid="stDownloadButton"] button { background: var(--surface) !important; color: var(--ink) !important; border: 1px solid var(--border) !important; border-radius: 999px !important; font-weight: 600; }
.stApp [data-testid="stDownloadButton"] button p { color: var(--ink) !important; }

/* ---------- แท็บ / กล่องพับ ---------- */
.stApp [data-testid="stTab"] p { font-weight: 600; color: var(--muted); }
.stApp [data-testid="stTab"][aria-selected="true"] p { color: var(--ink); }
.stApp [data-testid="stTab"] > div[data-rac] { background: var(--accent) !important; border-radius: 3px; }  /* เส้นใต้แท็บที่เลือก */
.stApp [data-testid="stTabs"] [role="tablist"] { border-color: var(--border); }
.stApp div[data-testid="stExpander"] details { border: 1px solid var(--border); border-radius: 16px; background: var(--surface2); }
.stApp div[data-testid="stExpander"] summary p { font-weight: 600; }
.stApp div[data-testid="stExpander"] summary:hover p { color: var(--accent); }

/* ---------- ชิ้นส่วน HTML ที่ใช้ซ้ำ ---------- */
/* แท็บบริษัท: ตารางข้อมูลย่อ */
.co-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: .7rem 1.2rem; margin: .7rem 0 .9rem; }
.co-grid .k { font-size: .74rem; color: var(--muted); font-weight: 600; }
.co-grid .v { font-size: .92rem; font-weight: 700; color: var(--ink); }
/* โครงสร้างรายได้: แถบสัดส่วนแต่ละธุรกิจ */
.rs-list { display: grid; gap: .55rem; margin-top: .3rem; }
.rs-top { display: flex; align-items: center; gap: .5rem; font-size: .88rem; color: var(--ink); }
.rs-top .sw { width: 10px; height: 10px; border-radius: 3px; flex: none; }
.rs-top .nm { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rs-top b { margin-left: auto; font-variant-numeric: tabular-nums; }
.rs-bar { height: 8px; border-radius: 8px; margin-top: .25rem; overflow: hidden;
  background: repeating-linear-gradient(135deg, rgba(127,127,127,.30) 0 2px, rgba(127,127,127,.07) 2px 6px); }
.rs-bar > i { display: block; height: 100%; border-radius: 8px; }
.rs-amt { font-size: .74rem; color: var(--muted); margin-top: .1rem; font-variant-numeric: tabular-nums; }
/* แท็บข่าว */
.news-list { display: grid; gap: .6rem; }
a.news { display: flex; gap: .9rem; align-items: flex-start; text-decoration: none !important; padding: .8rem .9rem;
  background: var(--surface2); border: 1px solid var(--border); border-radius: 18px; transition: border-color .15s ease; }
a.news:hover { border-color: var(--accent); }
a.news img { width: 112px; height: 80px; object-fit: cover; border-radius: 12px; flex: none; }
a.news .nt { font-weight: 700; color: var(--ink); line-height: 1.35; }
a.news .ns { font-size: .84rem; color: var(--muted); margin-top: .2rem; line-height: 1.45; }
a.news .nm { font-size: .74rem; color: var(--muted); margin-top: .35rem; font-weight: 600; }
@media (max-width: 640px) { a.news img { width: 76px; height: 58px; } }
.hero { padding: .4rem 0 .2rem; }
/* หน้าหลักบนจอไม่กว้างมาก (แท็บเล็ต / หน้าต่างเล็ก): คำทักทายอยู่แถวบน การ์ดดัชนี 3 ใบอยู่แถวล่าง
   (ไม่งั้นการ์ดแคบจนตัวเลขตกบรรทัด เช่น "7,56 / 1.67") */
@media (max-width: 1279px) {
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .hero) { flex-wrap: wrap; row-gap: 1rem; }
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .hero) > [data-testid="stColumn"] {
    flex: 1 1 100% !important; min-width: 100% !important; width: 100% !important; }
}
.tile .value { overflow-wrap: normal; word-break: keep-all; }
.hero-name { font-size: clamp(2.2rem, 4.4vw, 3.4rem); font-weight: 800; letter-spacing: -0.03em; line-height: 1.05; color: var(--ink); margin: .15rem 0 .5rem; word-break: break-word; }
.muted { color: var(--muted) !important; font-size: .84rem; }
.eyebrow { font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); font-weight: 700; }
.card-title { font-weight: 700; font-size: 1.02rem; margin: 0 0 .1rem; color: var(--ink); }
.tile .label { font-size: .8rem; color: var(--ink); opacity: .72; font-weight: 600; }
.tile .value { font-size: 1.75rem; font-weight: 800; letter-spacing: -0.02em; color: var(--ink); line-height: 1.2; font-variant-numeric: tabular-nums; }
.tile .value small { font-size: .9rem; font-weight: 600; opacity: .6; }
.tile .sub { font-size: .8rem; color: var(--ink); opacity: .72; margin-top: .15rem; }
/* รางแถบวัดลายเส้นทแยง (hatch) */
.meter { height: 8px; border-radius: 8px; margin-top: .6rem; overflow: hidden;
  background: repeating-linear-gradient(135deg, rgba(127,127,127,.34) 0 2px, rgba(127,127,127,.08) 2px 6px); }
.meter > i { display: block; height: 100%; border-radius: 8px; background: var(--accent); }
.chip { display: inline-block; padding: .18rem .65rem; border-radius: 999px; font-size: .76rem; font-weight: 600;
  background: var(--surface2); border: 1px solid var(--border); color: var(--ink); margin-right: .3rem; }
.tone-good { color: var(--good) !important; } .tone-bad { color: var(--bad) !important; } .tone-neutral { color: var(--muted) !important; }
.stock-head { display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: .8rem; }
.stock-head .name { font-size: 1.7rem; font-weight: 800; letter-spacing: -0.02em; color: var(--ink); line-height: 1.15; }
.stock-head .px { font-size: 1.7rem; font-weight: 800; color: var(--ink); font-variant-numeric: tabular-nums; text-align: right; line-height: 1.15; }
/* แถบคะแนนรายปัจจัย */
.factor { margin: .7rem 0; }
.factor .row { display: flex; justify-content: space-between; font-size: .86rem; font-weight: 600; color: var(--ink); }
.factor .row b { font-variant-numeric: tabular-nums; }
.factor .bar { height: 10px; border-radius: 10px; margin-top: .3rem; overflow: hidden;
  background: repeating-linear-gradient(135deg, rgba(127,127,127,.34) 0 2px, rgba(127,127,127,.08) 2px 6px); }
.factor .bar > i { display: block; height: 100%; border-radius: 8px; background: var(--accent); }
/* สัญญาณธุรกิจ */
.signs { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: .6rem; margin-top: .6rem; }
.sign { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: .6rem .8rem; }
.sign .k { font-size: .76rem; color: var(--muted); font-weight: 600; }
.sign .v { font-size: .88rem; font-weight: 700; color: var(--ink); }
/* แบบประเมิน: คำถาม + ตัวเลือกแบบการ์ด */
.quiz-q { font-size: 1.15rem; font-weight: 700; color: var(--ink); line-height: 1.45; margin-bottom: .8rem; }
.st-key-quizopt, .st-key-quizopt .stElementContainer, .st-key-quizopt .stRadio,
.st-key-quizopt [data-testid="stRadioGroup"], .st-key-quizopt [data-testid="stRadioGroup"] > div { width: 100%; }
.st-key-quizopt div[role="radiogroup"] { gap: .55rem; width: 100%; align-items: stretch; }
.st-key-quizopt label[data-testid="stRadioOption"] { box-sizing: border-box; }
.st-key-quizopt label[data-testid="stRadioOption"] {
  width: 100%; margin: 0; padding: .8rem 1rem; border-radius: 14px; cursor: pointer;
  background: var(--surface); border: 1px solid var(--border); transition: border-color .15s ease;
}
.st-key-quizopt label[data-testid="stRadioOption"]:hover { border-color: var(--accent); }
.st-key-quizopt label[data-testid="stRadioOption"]:has(input:checked) { border-color: var(--accent); background: var(--tint-blue); }
.st-key-quizopt label[data-testid="stRadioOption"]:has(input:focus-visible) { outline: 2px solid var(--accent); outline-offset: 2px; }
.st-key-quizopt label[data-testid="stRadioOption"] p { font-weight: 600; font-size: .95rem; }
/* ขั้นระดับผู้ลงทุน 1–5 */
.levels { display: flex; gap: 4px; margin: .6rem 0 .55rem; }
.levels > i { flex: 1; height: 8px; border-radius: 8px; background: rgba(127,127,127,.25); }
.levels > i.on { background: var(--accent); }
/* แถบสัดส่วนการลงทุน */
.alloc-bar { display: flex; gap: 2px; height: 22px; margin: .9rem 0 .7rem; }
.alloc-bar > i { display: block; height: 100%; border-radius: 4px; min-width: 4px; }
.alloc-row { display: flex; align-items: center; gap: .6rem; padding: .5rem 0; border-bottom: 1px solid var(--border);
  font-size: .9rem; color: var(--ink); }
.alloc-row:last-child { border-bottom: 0; }
.alloc-row .sw { width: 12px; height: 12px; border-radius: 4px; flex: none; }
.alloc-row b { margin-left: auto; font-variant-numeric: tabular-nums; }
.alloc-row .amt { margin-left: auto; color: var(--muted); font-variant-numeric: tabular-nums; }
.alloc-row .amt + b { margin-left: .9rem; min-width: 2.8rem; text-align: right; }
/* หน้าความรู้: กล่องข้อคิด + ตัวเลือกติ๊ก + ตารางคำศัพท์ */
.tip { background: var(--tint-cream); border-radius: 12px; padding: .65rem .9rem; margin-top: .4rem;
  font-size: .9rem; color: var(--ink); }
.tip b { margin-right: .3rem; }
.stApp [data-testid="stMain"] [data-testid="stExpander"] li,
.stApp [data-testid="stMain"] [data-testid="stExpander"] p { color: var(--ink); line-height: 1.65; }
.stApp [data-testid="stMain"] [data-testid="stCheckbox"] p { color: var(--ink); font-size: .92rem; }
.stApp [data-testid="stMain"] [data-testid="stSlider"] p { color: var(--ink); }
.tbl.gloss td { text-align: left; vertical-align: top; }
.tbl.gloss td:first-child { white-space: nowrap; width: 1%; padding-right: 1.4rem; }
/* ตาราง */
.tbl { width: 100%; border-collapse: collapse; font-size: .88rem; border: 0 !important; }
.tbl th, .tbl td { border: 0 !important; border-bottom: 1px solid var(--border) !important; background: transparent; }
.tbl tr:last-child td { border-bottom: 0 !important; }
.tbl th { text-align: right; font-size: .72rem; letter-spacing: .06em; text-transform: uppercase; color: var(--muted);
  font-weight: 700; padding: .5rem .6rem; border-bottom: 1px solid var(--border); }
.tbl td { text-align: right; padding: .62rem .6rem; border-bottom: 1px solid var(--border); color: var(--ink); font-variant-numeric: tabular-nums; }
.tbl th:first-child, .tbl td:first-child { text-align: left; }
.tbl tr:last-child td { border-bottom: 0; }
.tbl tr.me td { background: var(--tint-blue); font-weight: 700; }
.tbl tr.me td:first-child { border-radius: 10px 0 0 10px; } .tbl tr.me td:last-child { border-radius: 0 10px 10px 0; }
.tbl .sym { font-weight: 700; } .tbl .co { color: var(--muted); font-size: .78rem; }
.tbl-wrap { overflow-x: auto; }
.stats { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: .6rem; }
.stat { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: .65rem .8rem; }
.stat .k { font-size: .74rem; color: var(--muted); font-weight: 600; }
.stat .v { font-size: 1.02rem; font-weight: 700; color: var(--ink); font-variant-numeric: tabular-nums; }
"""


# ---------- เมนูด้านซ้าย: ปุ่มย่อ/ขยาย (ใช้ทุกโหมด) ----------
SIDE_CSS = """
/* จอกว้าง ≥ 1024px (คอม / แท็บเล็ตแนวนอน): ซ่อนปุ่มพับเมนูของ Streamlit ใช้ปุ่มย่อ/ขยายของเราแทน
   จอแคบกว่านั้น (มือถือ / แท็บเล็ตแนวตั้ง): ใช้ปุ่ม ☰ ของ Streamlit เปิด-ปิดเมนูแบบเลื่อนทับเนื้อหา
   (Streamlit จะพับเมนูเองเมื่อจอแคบ — ถ้าซ่อนปุ่ม ☰ ที่ขนาดนั้น จะเปิดเมนูไม่ได้เลย) */
@media (min-width: 1024px) {
  [data-testid="stSidebarCollapseButton"], [data-testid="stExpandSidebarButton"],
  [data-testid="stSidebarResizeHandle"] { display: none !important; }
  /* เปิดเว็บตอนหน้าต่างแคบแล้วค่อยขยาย Streamlit จะพับเมนูไว้ (กว้าง 0 / เลื่อนออกนอกจอ) — บังคับให้แสดงเสมอ */
  section[data-testid="stSidebar"] { transform: none !important; visibility: visible !important;
    width: 300px !important; min-width: 300px !important; max-width: 300px !important; }
}
@media (max-width: 1023px) { .st-key-side_toggle { display: none; } }   /* จอแคบ: ซ่อนเฉพาะปุ่มย่อ/ขยาย (ฟันเฟืองยังอยู่) */
/* แท็บเล็ตแนวตั้ง 768–1023px: Streamlit วางเมนูแทรกด้านซ้าย (เนื้อหาถูกบีบจนการ์ดแคบมาก)
   → เปลี่ยนเป็นเมนูเลื่อน "ทับ" เนื้อหาแบบมือถือ เนื้อหาจึงกว้างเต็มจอ (ปิดเมนูด้วยปุ่ม « ด้านบน) */
@media (min-width: 768px) and (max-width: 1023px) {
  section[data-testid="stSidebar"] { position: fixed !important; top: 0; left: 0; height: 100vh !important;
    z-index: 999991; box-shadow: 0 0 60px rgba(0,0,0,.45); }
}
section[data-testid="stSidebar"] { transition: width .2s ease, min-width .2s ease; }
/* ปุ่มย่อ/ขยายเมนู: ดันไปล่างสุดของแถบเมนู ด้วย flex (เนื้อหาเมนูยืดเต็มความสูง แล้วปุ่มใช้ margin-top:auto) */
@media (min-width: 1024px) {
  section[data-testid="stSidebar"] [data-testid="stSidebarContent"] { display: flex; flex-direction: column; }
  section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { flex: 1 0 auto; display: flex; flex-direction: column;
    padding-bottom: 1.1rem !important; }
  section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div { flex: 1 0 auto; display: flex; flex-direction: column; }
  section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] { flex: 1 0 auto; }
  [data-testid="stLayoutWrapper"]:has(> .st-key-side_toggle_wrap) { margin-top: auto; width: 100%; }
  .st-key-side_toggle_wrap { padding-top: 1rem; }
}
.st-key-side_toggle_wrap button { width: 100%; height: 42px; min-height: 42px; border-radius: 12px !important;
  border: 1px solid rgba(255,255,255,.14) !important; background: rgba(255,255,255,.04) !important; }
.st-key-side_toggle_wrap button p { color: var(--side-ink) !important; font-weight: 600; }
.st-key-side_toggle_wrap button:hover { background: var(--side-active) !important; border-color: var(--side-active) !important; }
.st-key-side_toggle_wrap button:hover p, .st-key-side_toggle_wrap button:hover span { color: var(--side-active-ink) !important; }
"""

# ---------- ผู้ใช้ + ปุ่มฟันเฟืองในเมนู และหน้าต่าง "ตั้งค่า" ----------
SETTINGS_CSS = """
.avatar { display: inline-grid; place-items: center; border-radius: 50%; object-fit: cover; flex: none;
  background: var(--lime); color: var(--lime-ink); font-weight: 800; line-height: 1; }
.st-key-side_user { gap: .5rem; flex-wrap: nowrap !important; margin-bottom: .6rem; }
.st-key-side_user > div:first-child { flex: 1 1 auto; min-width: 0; }
.st-key-side_user .stButton, .st-key-side_user .stButton button { width: 42px !important; flex: none; padding: 0 !important; }
.user-chip { display: flex; align-items: center; gap: .6rem; min-width: 0; }
.user-chip .who { min-width: 0; }
.user-chip .nm { font-weight: 700; font-size: .92rem; color: var(--side-ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.3; }
.user-chip .un { font-size: .74rem; color: var(--side-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.3; }
/* หน้าต่างตั้งค่า (dialog) — ใช้สีตามธีมของเว็บ */
div[data-testid="stDialog"] > div { background: var(--surface) !important; color: var(--ink);
  border: 1px solid var(--border); border-radius: 26px !important; }
div[data-testid="stDialog"] [role="dialog"] button[aria-label="Close"] { color: var(--ink); }
div[data-testid="stDialog"] :is(p, label, h1, h2, h3, li, span, small) { color: var(--ink); }
div[data-testid="stDialog"] .muted { color: var(--muted) !important; }
div[data-testid="stDialog"] hr { border-color: var(--border); }
div[data-testid="stDialog"] [data-testid="stTextInputRootElement"] { background: var(--surface2); border: 1px solid var(--border); border-radius: 14px; }
div[data-testid="stDialog"] input { color: var(--ink) !important; -webkit-text-fill-color: var(--ink); background: transparent; }
div[data-testid="stDialog"] input:disabled { -webkit-text-fill-color: var(--muted); }
div[data-testid="stDialog"] [data-testid="stFileUploaderDropzone"] { background: var(--surface2) !important; border: 1px dashed var(--border) !important; border-radius: 14px !important; }
div[data-testid="stDialog"] [data-testid="stFileUploaderDropzone"] * { color: var(--ink) !important; }
div[data-testid="stDialog"] button[data-testid="stBaseButton-primary"] { background: var(--btn); border: 0; border-radius: 999px; font-weight: 700; }
div[data-testid="stDialog"] button[data-testid="stBaseButton-primary"] p { color: var(--btn-ink) !important; }
[data-testid="stToast"] { background: var(--surface2) !important; border: 1px solid var(--border); border-radius: 16px !important; }
[data-testid="stToast"] * { color: var(--ink) !important; }
div[data-testid="stDialog"] button[data-testid="stBaseButton-secondary"],
div[data-testid="stDialog"] [data-testid="stFileUploaderDropzone"] button {
  background: var(--surface2); color: var(--ink); border: 1px solid var(--border); border-radius: 999px; font-weight: 600; }
div[data-testid="stDialog"] [data-testid="stButtonGroup"] button { background: var(--surface2); color: var(--ink);
  border: 1px solid var(--border); border-radius: 999px; min-height: 40px; padding: .3rem 1rem; }
div[data-testid="stDialog"] [data-testid="stButtonGroup"] button p { color: inherit !important; font-weight: 600; }
div[data-testid="stDialog"] [data-testid="stButtonGroup"] button:is([aria-checked="true"], [aria-pressed="true"]) {
  background: var(--btn) !important; color: var(--btn-ink) !important; border-color: var(--btn) !important; }
div[data-testid="stDialog"] [data-testid="stButtonGroup"] button:is([aria-checked="true"], [aria-pressed="true"]) * { color: var(--btn-ink) !important; }
div[data-testid="stDialog"] [data-testid="stExpander"] details { border: 1px solid var(--border); border-radius: 16px; background: var(--surface2); }
.set-title { font-size: 1.15rem; font-weight: 700; color: var(--ink); margin-bottom: .6rem; }
.set-row b { color: var(--ink); } .set-row .muted { margin-top: .1rem; }
/* เมนูหมวดด้านซ้ายของหน้าต่าง */
.st-key-set_nav div[role="radiogroup"] { gap: .25rem; }
.st-key-set_nav label[data-testid="stRadioOption"] { width: 100%; margin: 0; padding: .6rem .8rem; border-radius: 12px; cursor: pointer; border: 1px solid transparent; }
.st-key-set_nav label[data-testid="stRadioOption"] > div > div:not([data-testid]) { display: none; }
.st-key-set_nav label[data-testid="stRadioOption"]:hover { background: var(--surface2); }
.st-key-set_nav label[data-testid="stRadioOption"]:has(input:checked) { background: var(--surface2); border-color: var(--border); }
.st-key-set_nav label[data-testid="stRadioOption"] p { font-weight: 600; font-size: .93rem; }
.st-key-set_nav label[data-testid="stRadioOption"] p span[role="img"] { margin-right: .45rem; vertical-align: -0.2em; }
@media (min-width: 768px) { .st-key-set_nav { border-right: 1px solid var(--border); padding-right: .8rem; min-height: 420px; } }
"""

# ---------- เมนูย่อเหลือไอคอน (เฉพาะจอกว้าง ≥ 1024px) ----------
MINI_CSS = """
@media (min-width: 1024px) {
  /* แถบไอคอนแบบ "เกาะลอย": ตัวแถบโปร่งใส แล้ววาดกล่องมนสีเข้มไว้ด้านใน เว้นระยะจากขอบจอ */
  /* เกาะ: ซ้าย 18px + กว้าง 80px + ขวา 18px  → ช่องไฟซ้าย-ขวาเท่ากัน */
  section[data-testid="stSidebar"] { width: 116px !important; min-width: 116px !important; max-width: 116px !important;
    background: transparent !important; }
  /* แผ่นเนื้อหาหลัก: ชิดเกาะด้วยระยะ 18px และขอบบน/ล่างตรงกับเกาะ (16px) */
  [data-testid="stMainBlockContainer"] { margin: 16px 18px 16px 0 !important; max-width: calc(100% - 18px) !important; }
  [data-testid="stMain"] { padding-left: 0 !important; }
  section[data-testid="stSidebar"] > div:not([data-testid="stSidebarContent"]) { background: transparent !important; }
  /* ตัวเกาะใช้สีเข้มเสมอ (ทั้งธีมมืดและสว่าง) ให้ไอคอนสีขาวตัดกับพื้นชัดเจน */
  section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    background: var(--side) !important; margin: 16px 0 16px 18px; width: 80px !important; height: calc(100vh - 32px); border-radius: 30px;
    border: 1px solid rgba(255,255,255,.07); box-shadow: 0 18px 50px rgba(0,0,0,.28); overflow-x: hidden; }
  /* ซ่อนแถบหัวของ Streamlit (ว่างเปล่า) → โลโก้ SP ขึ้นไปชิดบนสุดของเกาะ เว้นระยะเท่ากับปุ่มขยายด้านล่าง */
  section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] { display: none !important; }
  section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] { gap: 0 !important; }
  .brand { padding: 0 !important; margin: 0 !important; position: relative; }
  section[data-testid="stSidebar"] .stElementContainer:has(.brand) { margin-bottom: 24px !important; }
  section[data-testid="stSidebar"] .stElementContainer:has(.brand) [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
  .brand::after { content: ""; position: absolute; left: 50%; transform: translateX(-50%); top: calc(100% + 11px);
    width: 32px; height: 1px; background: rgba(255,255,255,.16); }   /* เส้นคั่นสั้นๆ ใต้โลโก้ */
  section[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding: 0 !important; }
  section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding: 19px 6px 19px !important;
    margin: 0 !important; width: 100% !important; box-sizing: border-box; }
  section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"],
  section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] .stElementContainer,
  .st-key-nav, .st-key-nav [data-testid="stRadioGroup"] { width: 100% !important; }
  .brand .mark { flex: none; }
  .st-key-nav label[data-testid="stRadioOption"] { border-radius: 50% !important; width: 48px !important; height: 48px;
    margin: 0 auto !important; }
  .st-key-nav div[role="radiogroup"] { gap: .55rem; align-items: center; }
  .brand { justify-content: center; padding: .1rem 0 .5rem; }
  .brand .brand-text, .side-label { display: none !important; }
  /* ปุ่มขยาย: วงกลมกลางเกาะ ด้านล่าง */
  .st-key-side_toggle_wrap { align-items: center; width: 100% !important; }
  .st-key-side_toggle_wrap .stElementContainer { width: 100% !important; display: flex; justify-content: center; }
  .st-key-side_toggle_wrap .stButton { width: 40px !important; margin: 0 auto; }
  .st-key-side_toggle_wrap { gap: .55rem !important; }
  /* รายการเมนู: เหลือแต่ไอคอน วางกลาง */
  .st-key-nav label[data-testid="stRadioOption"] { justify-content: center; padding: .7rem 0; }
  .st-key-nav label[data-testid="stRadioOption"] p { font-size: 0 !important; line-height: 0; text-align: center; }
  .st-key-nav label[data-testid="stRadioOption"] p span[role="img"] { font-size: 1.35rem !important; line-height: 1.35rem; margin: 0 !important; }
  .st-key-nav label[data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] { width: 100%; }
  .st-key-side_toggle_wrap button { border-radius: 50% !important; width: 40px; height: 40px; min-height: 40px; padding: 0 !important; }
}
"""


# ---------- หน้า login: ไม่มีเมนูด้านข้าง + ปุ่มกลม 2 ปุ่ม (ภาษา / ธีม) มุมขวาบน ----------
LOGIN_CSS = """
section[data-testid="stSidebar"], [data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
/* แผ่นเนื้อหามี backdrop-filter → position:fixed จะอิงแผ่นนี้ = ปุ่มอยู่มุมขวาบนของแผ่น login */
.st-key-login_tools { position: fixed; top: 20px; right: 22px; z-index: 1000; width: auto !important; gap: 10px; }
.st-key-login_tools button { width: 42px; height: 42px; min-height: 42px; padding: 0 !important;
  border-radius: 50% !important; font-weight: 700; }
.st-key-login_tools button p { font-size: .8rem; }
@media (max-width: 767px) { .st-key-login_tools { right: 14px; top: 14px; } }
"""


def apply(theme_name: str, mini: bool = False, login: bool = False):
    """ใส่ CSS ตามธีมที่เลือกลงในหน้าเว็บ (ค่าสีส่งผ่านตัวแปร CSS --ชื่อ)
    mini=True → เมนูด้านซ้ายย่อเหลือแถบไอคอน,  login=True → หน้าเข้าสู่ระบบ (ไม่มีเมนูด้านข้าง)"""
    c = THEMES.get(theme_name, THEMES["light"])
    variables = ";".join(f"--{k.replace('_', '-')}:{v}" for k, v in c.items())
    extra = LOGIN_CSS if login else (SIDE_CSS + SETTINGS_CSS + (MINI_CSS if mini else ""))
    lang_css = LAO_CSS if st.session_state.get("lang", "lo") == "lo" else ""
    # 2 บล็อกแยกกัน (คนละ st.markdown) — ถ้าอยู่บรรทัดเดียวกัน บล็อกที่สองจะถูกแปลเป็นข้อความธรรมดา
    st.markdown(f"<style>{FONT_CSS}</style>".replace("\n", " "), unsafe_allow_html=True)
    body =f":root{{{variables}}}{CSS}{lang_css}{extra}"
    # ลบบรรทัดว่างทั้งหมด — บรรทัดว่างในบล็อก <style> ทำให้ markdown เลิกมองว่าเป็น HTML แล้วแสดง CSS เป็นข้อความ
    body = "\n".join(line for line in body.splitlines() if line.strip())
    st.markdown(f"<style>{body}</style>", unsafe_allow_html=True)


def plot_layout(fig, height=320, legend=True):
    """จัดหน้าตากราฟ Plotly ให้เข้ากับธีม: พื้นใส เส้นกริดจาง ตัวอักษรสีรอง"""
    c = tokens()
    fig.update_layout(
        height=height, margin=dict(l=58, r=12, t=10 if not legend else 36, b=34),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_PLOTLY, color=c["muted"], size=12),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(color=c["ink"], size=12), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=c["surface"], bordercolor=c["border"],
                        font=dict(color=c["ink"], family=FONT_PLOTLY)),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, linecolor=c["border"], tickfont=dict(color=c["muted"]), zeroline=False)
    fig.update_yaxes(gridcolor=c["border"], linecolor="rgba(0,0,0,0)", tickfont=dict(color=c["muted"]), zeroline=False)
    return fig
