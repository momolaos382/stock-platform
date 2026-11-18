# =====================================================
# auth.py — ระบบสมาชิก (สมัคร / เข้าสู่ระบบ)
# เก็บข้อมูลผู้ใช้ในฐานข้อมูล SQLite (ไฟล์ data/app.db)
# รหัสผ่านไม่ได้เก็บตรงๆ แต่เก็บเป็น "ค่าแฮช" (hash) เพื่อความปลอดภัย
# =====================================================
import hashlib
import os
import sqlite3
from datetime import datetime

# ตำแหน่งไฟล์ฐานข้อมูล: โฟลเดอร์ data ข้างๆ โปรเจกต์
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "app.db")


def get_conn():
    """เปิดการเชื่อมต่อฐานข้อมูล (ถ้ายังไม่มีโฟลเดอร์ data จะสร้างให้)"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """สร้างตารางในฐานข้อมูล ถ้ายังไม่มี (เรียกครั้งเดียวตอนเปิดแอป)"""
    with get_conn() as conn:
        # ตาราง users: เก็บผู้ใช้
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt          TEXT NOT NULL,
                created_at    TEXT NOT NULL
            )
        """)
        # ตาราง portfolios: เก็บพอร์ตที่ผู้ใช้บันทึก (จะใช้ในขั้นต่อไป)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                name       TEXT NOT NULL,
                data_json  TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        # ตาราง risk_profiles: ผลแบบประเมินระดับความเสี่ยงของผู้ใช้ (ดู core/quiz.py)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS risk_profiles (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                score        INTEGER NOT NULL,
                level        INTEGER NOT NULL,
                answers_json TEXT NOT NULL,
                created_at   TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)


def _hash_password(password: str, salt: str) -> str:
    """แปลงรหัสผ่านเป็นค่าแฮชด้วย PBKDF2-SHA256 (มาตรฐานความปลอดภัย)
    salt = ข้อความสุ่มที่เติมเข้าไป ทำให้รหัสเดียวกันได้แฮชไม่เหมือนกัน"""
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def register(username: str, password: str) -> bool:
    """สมัครสมาชิกใหม่ → คืนค่า True ถ้าสำเร็จ, False ถ้าชื่อผู้ใช้ซ้ำ"""
    salt = os.urandom(16).hex()
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, salt, created_at) VALUES (?, ?, ?, ?)",
                (username.strip(), _hash_password(password, salt), salt, datetime.now().isoformat()),
            )
        return True
    except sqlite3.IntegrityError:  # ชื่อผู้ใช้ซ้ำ (UNIQUE)
        return False


def login(username: str, password: str):
    """ตรวจสอบการเข้าสู่ระบบ → คืนค่า dict ข้อมูลผู้ใช้ ถ้าถูกต้อง, None ถ้าผิด"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, salt FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()
    if row and _hash_password(password, row[3]) == row[2]:
        return {"id": row[0], "username": row[1]}
    return None


# =====================================================
# โปรไฟล์ + การตั้งค่าของผู้ใช้ (ใช้ในหน้าต่าง "ตั้งค่า" — views/settings.py)
#   ตาราง user_settings: ชื่อที่แสดง, รูปโปรไฟล์ (เก็บเป็นไฟล์ JPEG ขนาด 256×256 ในฐานข้อมูล),
#   และค่าที่เลือกไว้ (ภาษา ธีม รูปแบบเมนู การแจ้งเตือน) เป็น JSON
# =====================================================
import base64  # noqa: E402
import io      # noqa: E402
import json    # noqa: E402

DEFAULT_PREFS = {
    "notify_moves": True,      # แจ้งเตือนเมื่อหุ้นในหน้าหลักขึ้น/ลงแรงในวันนี้
    "move_threshold": 3,       # เกณฑ์ "แรง" (% ต่อวัน)
    "notify_lao": True,        # แจ้งเมื่ออัปเดตข้อมูลหุ้นลาวจาก LSX เสร็จ
    "notify_quiz": True,       # เตือนให้ทำแบบประเมินผู้ลงทุน ถ้ายังไม่เคยทำ
}


def _ensure_settings_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id      INTEGER PRIMARY KEY,
            display_name TEXT,
            avatar       BLOB,
            prefs_json   TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


def get_profile(user_id: int) -> dict:
    """คืนค่า {"display_name", "avatar_uri" (data URI หรือ None), "prefs": dict}"""
    with get_conn() as conn:
        _ensure_settings_table(conn)
        row = conn.execute("SELECT display_name, avatar, prefs_json FROM user_settings WHERE user_id = ?",
                           (user_id,)).fetchone()
    name, avatar, prefs = row if row else (None, None, None)
    try:
        saved = json.loads(prefs) if prefs else {}
    except ValueError:
        saved = {}
    uri = "data:image/jpeg;base64," + base64.b64encode(avatar).decode() if avatar else None
    return {"display_name": name or "", "avatar_uri": uri, "prefs": {**DEFAULT_PREFS, **saved}}


def _upsert(user_id: int, column: str, value):
    # column มาจากโค้ดเราเองเท่านั้น (ไม่ใช่ข้อความจากผู้ใช้) จึงต่อเข้า SQL ได้อย่างปลอดภัย
    assert column in ("display_name", "avatar", "prefs_json")
    with get_conn() as conn:
        _ensure_settings_table(conn)
        conn.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,))
        conn.execute(f"UPDATE user_settings SET {column} = ? WHERE user_id = ?", (value, user_id))


def save_display_name(user_id: int, name: str):
    _upsert(user_id, "display_name", (name or "").strip()[:40])


def save_prefs(user_id: int, prefs: dict):
    _upsert(user_id, "prefs_json", json.dumps(prefs, ensure_ascii=False))


def save_avatar(user_id: int, raw: bytes) -> bool:
    """รับไฟล์รูป → ตัดเป็นสี่เหลี่ยมจัตุรัสกลางภาพ ย่อเหลือ 256×256 แล้วเก็บเป็น JPEG  (รูปเสีย → False)
    raw=None → ลบรูป"""
    if raw is None:
        _upsert(user_id, "avatar", None)
        return True
    try:
        from PIL import Image, ImageOps
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
        side = min(img.size)
        left, top = (img.width - side) // 2, (img.height - side) // 2
        img = img.crop((left, top, left + side, top + side)).resize((256, 256))
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=85)
    except Exception:
        return False
    _upsert(user_id, "avatar", out.getvalue())
    return True


def change_password(user_id: int, old: str, new: str) -> bool:
    """เปลี่ยนรหัสผ่าน (ต้องใส่รหัสเดิมถูก) → True ถ้าสำเร็จ"""
    with get_conn() as conn:
        row = conn.execute("SELECT password_hash, salt FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row or _hash_password(old, row[1]) != row[0]:
            return False
        salt = os.urandom(16).hex()
        conn.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                     (_hash_password(new, salt), salt, user_id))
    return True
