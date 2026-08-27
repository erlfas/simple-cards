#!/usr/bin/env bash
# ==============================================================================
# Simple Cards - Automated VPS Deployment & Daily Update Script
# Target OS: Ubuntu 22.04 LTS / Debian
# Safe to run repeatedly for initial setup and daily code updates.
# ==============================================================================

set -euo pipefail

APP_DIR="/var/www/simplecards"
DOMAIN="${DOMAIN:-simplecards.blottogbar.no}"
DB_NAME="${DB_NAME:-simple_cards}"
DB_USER="${DB_USER:-simplecards_user}"
DB_PASS="${DB_PASSWORD:-$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 16)}"
SSL_EMAIL="${SSL_EMAIL:-admin@${DOMAIN}}"
APP_PORT="${APP_PORT:-8002}"

echo "========================================================="
echo "   🚀 Simple Cards Deployment & Update"
echo "========================================================="

# 1. Require root / sudo
if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run this script with sudo: sudo bash deploy.sh"
  exit 1
fi

# Detect if this is a first-time setup or an update
FIRST_TIME=false
if [ ! -f "${APP_DIR}/.env" ] || [ ! -d "${APP_DIR}/venv" ]; then
  FIRST_TIME=true
  echo "[*] First-time setup detected. Installing system prerequisites..."
  apt update -y
  apt install -y python3-venv python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx certbot python3-certbot-nginx git ufw
  
  # Stop conflicting web servers if present
  systemctl stop apache2 2>/dev/null || true
  systemctl disable apache2 2>/dev/null || true
  rm -f /etc/nginx/sites-enabled/default
else
  echo "[*] Existing installation detected. Performing safe update..."
fi

# 2. Configure PostgreSQL (Idempotent - safe to run repeatedly)
systemctl start postgresql
systemctl enable postgresql

sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1 || \
sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';"

sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 || \
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"

# 3. Pull latest code or sync directory
echo "[*] Updating application code in ${APP_DIR}..."
mkdir -p "${APP_DIR}"
if [ -d "${APP_DIR}/.git" ]; then
  git config --global --add safe.directory "${APP_DIR}" 2>/dev/null || true
  cd "${APP_DIR}"
  git pull origin master || true
elif [ "$(pwd)" != "${APP_DIR}" ]; then
  cp -r . "${APP_DIR}/"
fi
cd "${APP_DIR}"

# 4. Virtual Environment & Dependencies
if [ ! -d "${APP_DIR}/venv" ]; then
  echo "[*] Creating Python virtual environment..."
  python3 -m venv "${APP_DIR}/venv"
fi
echo "[*] Installing/updating Python dependencies..."
"${APP_DIR}/venv/bin/pip" install --quiet --upgrade pip
"${APP_DIR}/venv/bin/pip" install --quiet -r "${APP_DIR}/requirements.txt"

# 5. Environment configuration (.env preserved if already exists)
if [ ! -f "${APP_DIR}/.env" ]; then
  echo "[*] Generating production .env configuration..."
  SECRET_KEY=$("${APP_DIR}/venv/bin/python" -c "import secrets; print(secrets.token_urlsafe(50))")
  FIELD_ENCRYPTION_KEY=$("${APP_DIR}/venv/bin/python" -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
  
  cat << EOF > "${APP_DIR}/.env"
DEBUG=False
SECRET_KEY=${SECRET_KEY}
ALLOWED_HOSTS=${DOMAIN},127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://${DOMAIN}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASS}
DB_HOST=127.0.0.1
DB_PORT=5432
FIELD_ENCRYPTION_KEY=${FIELD_ENCRYPTION_KEY}
EOF
  chmod 600 "${APP_DIR}/.env"
fi

# 6. Run Migrations & Collect Static
echo "[*] Running database migrations..."
"${APP_DIR}/venv/bin/python" "${APP_DIR}/manage.py" migrate --noinput

echo "[*] Collecting static assets..."
"${APP_DIR}/venv/bin/python" "${APP_DIR}/manage.py" collectstatic --noinput

# Set web server file ownership
chown -R www-data:www-data "${APP_DIR}"
chmod -R 755 "${APP_DIR}/staticfiles" 2>/dev/null || true

# 7. Configure Gunicorn Systemd Service
echo "[*] Updating Gunicorn systemd service on port ${APP_PORT}..."
cat << EOF > /etc/systemd/system/gunicorn_simplecards.service
[Unit]
Description=Gunicorn daemon for Simple Cards
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/gunicorn \\
          --workers 3 \\
          --bind 127.0.0.1:${APP_PORT} \\
          --access-logfile - \\
          --error-logfile - \\
          config.wsgi:application

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable gunicorn_simplecards

# Restart Gunicorn to apply changes
echo "[*] Restarting Gunicorn..."
systemctl restart gunicorn_simplecards

# 8. Configure Nginx (Preserves existing SSL / Certbot configuration!)
if [ ! -f "/etc/nginx/sites-available/${DOMAIN}" ]; then
  echo "[*] Creating initial Nginx configuration..."
  cat << EOF > /etc/nginx/sites-available/${DOMAIN}
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    client_max_body_size 10M;

    location /static/ {
        alias ${APP_DIR}/staticfiles/;
        expires 30d;
        access_log off;
        add_header Cache-Control "public, max-age=2592000";
    }

    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
  ln -sf /etc/nginx/sites-available/${DOMAIN} /etc/nginx/sites-enabled/
else
  # If site file already exists, update the proxy_pass port to match APP_PORT
  sed -i "s|proxy_pass http://127.0.0.1:[0-9]*;|proxy_pass http://127.0.0.1:${APP_PORT};|g" "/etc/nginx/sites-available/${DOMAIN}"
fi

nginx -t
systemctl reload nginx

# 9. Configure UFW Firewall (if active)
if command -v ufw >/dev/null 2>&1; then
  ufw allow OpenSSH >/dev/null 2>&1 || true
  ufw allow 'Nginx Full' >/dev/null 2>&1 || true
fi

echo "========================================================="
echo "   ✅ Simple Cards Updated & Live in Production!"
echo "========================================================="
if [ "$FIRST_TIME" = true ]; then
  echo ""
  echo "🔒 First time setup: Activate your SSL certificate by running:"
  echo "   sudo certbot --nginx -d ${DOMAIN} --non-interactive --agree-tos -m ${SSL_EMAIL} --redirect"
fi
echo ""
