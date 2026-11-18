#!/usr/bin/env bash
# =====================================================
# setup_ubuntu.sh — ติดตั้ง Stock Platform บนเซิร์ฟเวอร์ Ubuntu 22.04 / 24.04 (AWS Lightsail / EC2)
#
# วิธีใช้ (บนเซิร์ฟเวอร์ หลังแตก zip แล้ว เข้าไปในโฟลเดอร์โปรเจกต์):
#     sudo bash deploy/setup_ubuntu.sh                       # เข้าเว็บด้วยเลข IP (http)
#     sudo bash deploy/setup_ubuntu.sh เว็บของฉัน.com you@mail.com   # มีโดเมน → ใส่ HTTPS ให้ด้วย (Let's Encrypt)
#
# ทำอะไรบ้าง: ติดตั้ง Python/nginx → คัดลอกโปรเจกต์ไป /opt/stock-platform → สร้าง venv + ติดตั้งไลบรารี
#             → ตั้งให้เว็บรันเป็น service (เปิดเองตอนเครื่องรีสตาร์ต / ล่มแล้วเปิดใหม่เอง)
#             → ตั้ง nginx ให้เข้าทางพอร์ต 80 (รองรับ websocket ที่ Streamlit ต้องใช้)
# รันซ้ำได้ (อัปเดตโค้ดโดยไม่ลบฐานข้อมูลผู้ใช้ /opt/stock-platform/data/app.db)
# =====================================================
set -euo pipefail

APP_DIR=/opt/stock-platform
SERVICE=stockplatform
DOMAIN="${1:-}"
EMAIL="${2:-}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$(id -u)" -ne 0 ]; then echo "กรุณารันด้วย sudo"; exit 1; fi
echo "==> โปรเจกต์ต้นทาง: $SRC"

echo "==> [1/6] ติดตั้งโปรแกรมที่ต้องใช้"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-venv python3-pip nginx rsync unzip curl

# เครื่อง RAM น้อย (≤ 1.5GB) → เพิ่ม swap 2GB กันโปรแกรมถูกปิดเพราะหน่วยความจำไม่พอ
MEM_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
if [ "$MEM_MB" -lt 1500 ] && [ ! -f /swapfile ]; then
  echo "==> RAM ${MEM_MB}MB น้อย → สร้าง swap 2GB"
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "==> [2/6] คัดลอกโปรเจกต์ไป $APP_DIR (ไม่ทับฐานข้อมูลผู้ใช้ / อีเมล SEC ที่มีอยู่)"
mkdir -p "$APP_DIR"
rsync -a --delete \
  --exclude '.venv' --exclude '__pycache__' --exclude 'dist' \
  --exclude 'data/app.db' --exclude 'data/sec/config.json' --exclude 'data/test-account.txt' \
  "$SRC"/ "$APP_DIR"/
mkdir -p "$APP_DIR/data"

echo "==> [3/6] สร้าง virtual environment + ติดตั้งไลบรารี (ใช้เวลา 2–5 นาที)"
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip -q
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q

echo "==> [4/6] ตั้ง service ให้เว็บรันอัตโนมัติ"
id -u stockapp >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin stockapp
chown -R stockapp:stockapp "$APP_DIR"
cp "$APP_DIR/deploy/stockplatform.service" /etc/systemd/system/$SERVICE.service
systemctl daemon-reload
systemctl enable $SERVICE >/dev/null
systemctl restart $SERVICE

echo "==> [5/6] ตั้ง nginx"
SERVER_NAME="${DOMAIN:-_}"
sed "s/__SERVER_NAME__/$SERVER_NAME/" "$APP_DIR/deploy/nginx.conf" > /etc/nginx/sites-available/$SERVICE
ln -sf /etc/nginx/sites-available/$SERVICE /etc/nginx/sites-enabled/$SERVICE
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

if [ -n "$DOMAIN" ]; then
  echo "==> [6/6] ใส่ HTTPS ให้ $DOMAIN (โดเมนต้องชี้มาที่ IP เครื่องนี้ก่อน)"
  apt-get install -y certbot python3-certbot-nginx
  certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "${EMAIL:-admin@$DOMAIN}" --redirect \
    || echo "!! ใส่ HTTPS ไม่สำเร็จ — ตรวจว่าโดเมนชี้มาที่เครื่องนี้แล้ว แล้วรันคำสั่งเดิมซ้ำได้"
else
  echo "==> [6/6] ข้าม HTTPS (ไม่ได้ระบุโดเมน)"
fi

sleep 4
if systemctl is-active --quiet $SERVICE && curl -fsS http://127.0.0.1:8501/_stcore/health >/dev/null; then
  IP=$(curl -fsS https://checkip.amazonaws.com 2>/dev/null || hostname -I | awk '{print $1}')
  echo
  echo "✅ ติดตั้งสำเร็จ"
  echo "   เปิดเว็บที่: http://${DOMAIN:-$IP}   (ถ้าใส่ HTTPS แล้ว: https://$DOMAIN)"
  echo "   ดู log:       sudo journalctl -u $SERVICE -f"
  echo "   รีสตาร์ต:     sudo systemctl restart $SERVICE"
else
  echo "❌ เว็บยังไม่ทำงาน — ดู log: sudo journalctl -u $SERVICE -n 80 --no-pager"
  exit 1
fi
