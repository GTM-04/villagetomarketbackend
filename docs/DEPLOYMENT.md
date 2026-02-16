# Village to Market - Deployment Guide

## Production Deployment

### Prerequisites

- Ubuntu 20.04+ server
- Domain name (e.g., api.villagetomarket.zw)
- SSL certificate (Let's Encrypt)
- At least 2GB RAM, 2 CPU cores

### 1. Server Setup

#### Update System

```bash
sudo apt update && sudo apt upgrade -y
```

#### Install Dependencies

```bash
sudo apt install -y python3.9 python3-pip python3-venv postgresql postgresql-contrib redis-server nginx
```

#### Install Docker (Optional)

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2. Database Setup

#### PostgreSQL

```bash
sudo -u postgres psql

CREATE DATABASE villagetomarket;
CREATE USER vtm_user WITH PASSWORD 'secure_password';
ALTER ROLE vtm_user SET client_encoding TO 'utf8';
ALTER ROLE vtm_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE vtm_user SET timezone TO 'Africa/Harare';
GRANT ALL PRIVILEGES ON DATABASE villagetomarket TO vtm_user;
\q
```

### 3. Application Setup

#### Clone Repository

```bash
cd /var/www
sudo git clone <repository-url> villagetomarket
cd villagetomarket
```

#### Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
pip install gunicorn
```

#### Configure Environment

```bash
sudo nano .env
```

Set production environment variables:

```env
DEBUG=False
SECRET_KEY=your-super-secret-key-here
DJANGO_SETTINGS_MODULE=config.settings.production
DATABASE_URL=postgresql://vtm_user:secure_password@localhost:5432/villagetomarket
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
ALLOWED_HOSTS=api.villagetomarket.zw,.villagetomarket.zw

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Twilio
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-number
```

#### Run Migrations

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_data
python manage.py createsuperuser
```

### 4. Gunicorn Setup

#### Create Systemd Service

```bash
sudo nano /etc/systemd/system/villagetomarket.service
```

```ini
[Unit]
Description=Village to Market Django API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/villagetomarket
Environment="PATH=/var/www/villagetomarket/venv/bin"
ExecStart=/var/www/villagetomarket/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/villagetomarket/villagetomarket.sock \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

#### Create FastAPI Service

```bash
sudo nano /etc/systemd/system/villagetomarket-api.service
```

```ini
[Unit]
Description=Village to Market FastAPI
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/villagetomarket
Environment="PATH=/var/www/villagetomarket/venv/bin"
ExecStart=/var/www/villagetomarket/venv/bin/uvicorn \
    api.main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --workers 2

[Install]
WantedBy=multi-user.target
```

#### Start Services

```bash
sudo systemctl start villagetomarket
sudo systemctl enable villagetomarket
sudo systemctl start villagetomarket-api
sudo systemctl enable villagetomarket-api
```

### 5. Celery Setup

#### Create Celery Worker Service

```bash
sudo nano /etc/systemd/system/villagetomarket-celery.service
```

```ini
[Unit]
Description=Village to Market Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/villagetomarket
Environment="PATH=/var/www/villagetomarket/venv/bin"
ExecStart=/var/www/villagetomarket/venv/bin/celery -A config worker --loglevel=info --pidfile=/var/run/celery.pid

[Install]
WantedBy=multi-user.target
```

#### Create Celery Beat Service

```bash
sudo nano /etc/systemd/system/villagetomarket-celerybeat.service
```

```ini
[Unit]
Description=Village to Market Celery Beat
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/villagetomarket
Environment="PATH=/var/www/villagetomarket/venv/bin"
ExecStart=/var/www/villagetomarket/venv/bin/celery -A config beat --loglevel=info

[Install]
WantedBy=multi-user.target
```

#### Start Celery Services

```bash
sudo systemctl start villagetomarket-celery
sudo systemctl enable villagetomarket-celery
sudo systemctl start villagetomarket-celerybeat
sudo systemctl enable villagetomarket-celerybeat
```

### 6. Nginx Configuration

#### Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/villagetomarket
```

```nginx
upstream django_app {
    server unix:/var/www/villagetomarket/villagetomarket.sock fail_timeout=0;
}

upstream fastapi_app {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name api.villagetomarket.zw;

    client_max_body_size 10M;

    # Django Admin and Static Files
    location /admin {
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static/ {
        alias /var/www/villagetomarket/static/;
    }

    location /media/ {
        alias /var/www/villagetomarket/media/;
    }

    # FastAPI
    location / {
        proxy_pass http://fastapi_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://fastapi_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/villagetomarket /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. SSL Certificate

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.villagetomarket.zw
```

### 8. Monitoring and Logging

#### View Logs

```bash
# Django
sudo journalctl -u villagetomarket -f

# FastAPI
sudo journalctl -u villagetomarket-api -f

# Celery
sudo journalctl -u villagetomarket-celery -f

# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 9. Backup Script

```bash
sudo nano /usr/local/bin/backup-villagetomarket.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/villagetomarket"
mkdir -p $BACKUP_DIR

# Backup Database
pg_dump -U vtm_user villagetomarket > "$BACKUP_DIR/db_$DATE.sql"

# Backup Media Files
tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" /var/www/villagetomarket/media/

# Delete old backups (keep 7 days)
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
sudo chmod +x /usr/local/bin/backup-villagetomarket.sh
```

#### Schedule Backups

```bash
sudo crontab -e
```

Add:

```
0 2 * * * /usr/local/bin/backup-villagetomarket.sh
```

## Docker Deployment

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Health Checks

```bash
# Check services
systemctl status villagetomarket
systemctl status villagetomarket-api
systemctl status villagetomarket-celery
systemctl status nginx

# Check API
curl http://localhost:8001/health
```

## Troubleshooting

### Service won't start

```bash
sudo journalctl -u villagetomarket -n 50
```

### Database connection error

```bash
sudo -u postgres psql -c "SELECT 1"
```

### Permission issues

```bash
sudo chown -R www-data:www-data /var/www/villagetomarket
```

## Updates

```bash
cd /var/www/villagetomarket
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart villagetomarket villagetomarket-api
```
