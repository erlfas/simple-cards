# Simple Cards - Production Deployment Guide (Ubuntu 22.04 LTS)

This guide walks you through deploying **Simple Cards** to an **Ubuntu 22.04 LTS** VPS using **PostgreSQL**, **Gunicorn (Systemd)**, **Nginx**, and **Let's Encrypt (Certbot)** for SSL/TLS.

It includes commands to **detect, clean up, and overwrite any pre-existing or conflicting configurations** from previous setups.

---

## Architecture Overview

* **Application:** Simple Cards (Spaced Repetition Flashcard App)
* **Default Domain:** `simplecards.blottogbar.no`
* **Application Path:** `/var/www/simplecards`
* **WSGI Application Server:** Gunicorn (`config.wsgi:application` bound to `127.0.0.1:8002`)
* **Reverse Proxy:** Nginx (port 80 → 443 SSL redirect, proxying dynamic traffic to Gunicorn and serving `/static/`)
* **Database:** PostgreSQL (`simple_cards` database)
* **Application-Level Encryption:** Fernet (AES-128-CBC + HMAC-SHA256) via `FIELD_ENCRYPTION_KEY`
* **SSL/TLS:** Let's Encrypt automated via Certbot

---

## ⚡ Fast Automated 1-Command Deployment (Recommended)

After cloning the repository onto your VPS, you can run the included automated setup script to handle everything (packages, PostgreSQL, `.env`, virtualenv, migrations, static assets, Gunicorn, and Nginx):

```bash
# 1. Create web directory and clone repository
sudo mkdir -p /var/www/simplecards
sudo chown -R $USER:www-data /var/www/simplecards
git clone https://github.com/erlfas/simple-cards.git /var/www/simplecards

# 2. Run the automated deployment script
cd /var/www/simplecards
sudo bash deploy.sh
```

*(Once complete, follow the prompt to activate SSL with `sudo certbot --nginx -d simplecards.blottogbar.no`)*

---

## Step 0: Clean Up Conflicting Services & Old Setups

If your VPS already has an older version of this app or conflicting default web servers running, run these cleanup steps first:

### 1. Stop & Disable Conflicting Web Services (e.g. Apache)
```bash
# Stop and disable Apache if it was installed (prevent port 80/443 conflicts)
sudo systemctl stop apache2 2>/dev/null || true
sudo systemctl disable apache2 2>/dev/null || true

# Stop old Gunicorn service if present
sudo systemctl stop gunicorn_simplecards 2>/dev/null || true
sudo systemctl disable gunicorn_simplecards 2>/dev/null || true
```

### 2. Clean Conflicting Nginx Site Configurations
```bash
# Remove default Nginx site if active
sudo rm -f /etc/nginx/sites-enabled/default

# Remove old/stale simplecards symlinks
sudo rm -f /etc/nginx/sites-enabled/simplecards*
```

### 3. (Optional) Reset PostgreSQL User & Database (Clean Slate)
> [!CAUTION]
> This wipes any previous `simple_cards` database data on the VPS. Skip if you want to preserve existing data!
```bash
sudo -u postgres psql -c "DROP DATABASE IF EXISTS simple_cards;"
sudo -u postgres psql -c "DROP USER IF EXISTS simplecards_user;"
```

---

## Step 1: System Packages & PostgreSQL Setup

SSH into your VPS and install/verify dependencies:

```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Install Python, PostgreSQL, Nginx, Certbot, and build tools
sudo apt install -y python3-venv python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx certbot python3-certbot-nginx git ufw

# 3. Configure Host Firewall (UFW)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# 4. Create dedicated PostgreSQL user & database
sudo -u postgres psql -c "CREATE USER simplecards_user WITH PASSWORD 'YOUR_STRONG_DB_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE simple_cards OWNER simplecards_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE simple_cards TO simplecards_user;"
```

---

## Step 2: Clone Code & Virtual Environment

```bash
# 1. Create web directory & set user permissions
sudo mkdir -p /var/www/simplecards
sudo chown -R $USER:www-data /var/www/simplecards

# 2. Clone repository
git clone https://github.com/erlfas/simple-cards.git /var/www/simplecards

# 3. Create virtual environment & install dependencies
cd /var/www/simplecards
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 3: Production Environment Variables (`.env`)

Create the environment file `/var/www/simplecards/.env`:

```bash
cat << 'EOF' > /var/www/simplecards/.env
DEBUG=False
SECRET_KEY=CHANGE_THIS_TO_A_RANDOM_LONG_SECRET_KEY_STRING_1234567890
ALLOWED_HOSTS=simplecards.blottogbar.no,127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://simplecards.blottogbar.no
DB_NAME=simple_cards
DB_USER=simplecards_user
DB_PASSWORD=YOUR_STRONG_DB_PASSWORD
DB_HOST=127.0.0.1
DB_PORT=5432
FIELD_ENCRYPTION_KEY=YOUR_32_BYTE_BASE64_FERNET_KEY
EOF

# Lock down permissions (readable only by owner/root)
chmod 600 /var/www/simplecards/.env
```

> [!TIP]
> Generate a fresh encryption key with:
> `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

---

## Step 4: Run Migrations & Collect Static Assets

```bash
cd /var/www/simplecards
source venv/bin/activate

# Apply database schema migrations on PostgreSQL
python manage.py migrate

# Collect static assets into /var/www/simplecards/staticfiles/
python manage.py collectstatic --noinput

# (Optional) Seed demo flashcards
python manage.py seed_demo_data

# Set web server file ownership & permissions
sudo chown -R www-data:www-data /var/www/simplecards
sudo chmod -R 755 /var/www/simplecards/staticfiles
```

---

## Step 5: Systemd Service for Gunicorn

Create `/etc/systemd/system/gunicorn_simplecards.service`:

```bash
sudo tee /etc/systemd/system/gunicorn_simplecards.service << 'EOF'
[Unit]
Description=Gunicorn daemon for Simple Cards
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/simplecards
EnvironmentFile=/var/www/simplecards/.env
ExecStart=/var/www/simplecards/venv/bin/gunicorn \
          --workers 3 \
          --bind 127.0.0.1:8002 \
          --access-logfile - \
          --error-logfile - \
          config.wsgi:application

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

Start and enable Gunicorn:

```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn_simplecards
sudo systemctl enable gunicorn_simplecards

# Verify service status
sudo systemctl status gunicorn_simplecards
```

---

## Step 6: Configure Nginx & SSL Certificate

1. Create Nginx site config at `/etc/nginx/sites-available/simplecards.blottogbar.no`:

```bash
sudo tee /etc/nginx/sites-available/simplecards.blottogbar.no << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name simplecards.blottogbar.no;

    client_max_body_size 10M;

    # Static Assets served directly by Nginx
    location /static/ {
        alias /var/www/simplecards/staticfiles/;
        expires 30d;
        access_log off;
        add_header Cache-Control "public, max-age=2592000";
    }

    # Pass dynamic traffic to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

2. Enable the site configuration and test Nginx syntax:

```bash
sudo ln -sf /etc/nginx/sites-available/simplecards.blottogbar.no /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

3. Obtain / Re-issue SSL Certificate with Certbot:

```bash
sudo certbot --nginx -d simplecards.blottogbar.no --non-interactive --agree-tos --redirect -m your-email@example.com
```

---

## Step 7: Troubleshooting & Verification

* **View live application logs:**
  ```bash
  sudo journalctl -u gunicorn_simplecards -f
  ```
* **View Nginx error logs:**
  ```bash
  sudo tail -f /var/log/nginx/error.log
  ```
* **Create Django Superuser (for `/admin/`):**
  ```bash
  cd /var/www/simplecards
  source venv/bin/activate
  python manage.py createsuperuser
  ```
