# Production Hardening Guide

This document outlines the steps required to deploy the Asset Management System to production safely and securely.

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Security Configuration](#security-configuration)
4. [Database Configuration](#database-configuration)
5. [Static Files & Media](#static-files--media)
6. [Docker Production Setup](#docker-production-setup)
7. [Nginx Configuration](#nginx-configuration)
8. [SSL/TLS Setup](#ssltls-setup)
9. [Backup & Restore](#backup--restore)
10. [Monitoring & Logging](#monitoring--logging)
11. [Performance Optimization](#performance-optimization)
12. [Maintenance Procedures](#maintenance-procedures)

---

## Overview

The development environment uses Django's built-in development server and includes debugging tools like pgAdmin. The production environment requires:

- **Gunicorn** as the WSGI application server
- **Nginx** as a reverse proxy for static files and SSL termination
- **PostgreSQL** with proper connection pooling
- **Secure settings** (SECRET_KEY, DEBUG=False, etc.)
- **Monitoring and logging** for operational visibility
- **Backup procedures** for data protection

---

## Pre-Deployment Checklist

Before deploying to production:

- [ ] All unit tests pass (`./run-tests.sh`)
- [ ] All validation tests completed (see `VALIDATION-CHECKLIST.md`)
- [ ] Security audit completed (see [Security Configuration](#security-configuration))
- [ ] Database backup procedure tested
- [ ] Restore procedure tested
- [ ] Performance testing completed with realistic data volume
- [ ] Documentation reviewed and updated
- [ ] Runbook created for operations team
- [ ] Incident response plan documented

---

## Security Configuration

### 1. Django Secret Key

**Never use the default SECRET_KEY in production!**

Generate a new secret key:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Store it securely:

```bash
# Create .env file (add to .gitignore!)
echo "SECRET_KEY='your-generated-secret-key-here'" > .env
```

Update `config/settings.py`:

```python
import os
from pathlib import Path

# Read SECRET_KEY from environment
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set in production")
```

### 2. Debug Mode

**CRITICAL:** Always set `DEBUG = False` in production.

In `config/settings.py`:

```python
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
```

In production `.env`:

```bash
DEBUG=False
```

### 3. Allowed Hosts

Configure allowed hostnames in `config/settings.py`:

```python
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Example: ALLOWED_HOSTS=assets.company.com,192.168.1.100
```

In production `.env`:

```bash
ALLOWED_HOSTS=assets.yourcompany.com,192.168.1.100
```

### 4. CSRF & Session Security

Add to `config/settings.py`:

```python
# CSRF Protection
CSRF_COOKIE_SECURE = True  # Require HTTPS
CSRF_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = ['https://assets.yourcompany.com']

# Session Security
SESSION_COOKIE_SECURE = True  # Require HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_AGE = 86400  # 24 hours

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = True  # Force HTTPS
```

### 5. Database Credentials

Never hardcode database credentials. Use environment variables:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'assetdb'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

In production `.env`:

```bash
DB_NAME=assetdb_prod
DB_USER=assetdb_user
DB_PASSWORD=strong_random_password_here
DB_HOST=localhost
DB_PORT=5432
```

### 6. Remove Development Tools

In production `docker-compose.yml`, remove:

- pgAdmin service
- Volume mounts that expose source code
- Debug ports
- Any `--profile dev` services

---

## Database Configuration

### 1. Production Database Setup

Create dedicated PostgreSQL user:

```sql
CREATE USER assetdb_user WITH PASSWORD 'strong_random_password';
CREATE DATABASE assetdb_prod OWNER assetdb_user;
GRANT ALL PRIVILEGES ON DATABASE assetdb_prod TO assetdb_user;
```

### 2. Connection Pooling

Add connection pooling to reduce database overhead:

```bash
pip install psycopg2-binary
```

In `config/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
        'CONN_MAX_AGE': 60,  # Keep connections alive for 60 seconds
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

### 3. Run Migrations

Always run migrations before starting the application:

```bash
docker compose exec web python manage.py migrate --no-input
```

Or add a migration init container to `docker-compose.yml`:

```yaml
services:
  migrate:
    image: your-web-image:latest
    command: python manage.py migrate --no-input
    depends_on:
      - db
    restart: "no"
```

---

## Static Files & Media

### 1. Collect Static Files

Configure static files in `config/settings.py`:

```python
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Optional: media files for future use
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')
```

Collect static files:

```bash
docker compose exec web python manage.py collectstatic --no-input
```

### 2. Serve Static Files with Nginx

Nginx should serve static files directly (not Django):

```nginx
location /static/ {
    alias /app/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}

location /media/ {
    alias /app/mediafiles/;
    expires 7d;
}
```

---

## Docker Production Setup

### Production docker-compose.yml

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - backend

  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 60
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=${DEBUG}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - DB_PORT=5432
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/mediafiles
    depends_on:
      - db
    restart: unless-stopped
    networks:
      - backend
      - frontend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/mediafiles:ro
    depends_on:
      - web
    restart: unless-stopped
    networks:
      - frontend

volumes:
  postgres_data:
  static_volume:
  media_volume:

networks:
  frontend:
  backend:
```

### Production Dockerfile

Create `Dockerfile.prod`:

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Collect static files
RUN python manage.py collectstatic --no-input

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

---

## Nginx Configuration

### Production nginx.conf

Create `nginx/nginx.conf`:

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;  # Allow large LSHW JSON uploads

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;

    upstream web {
        server web:8000;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name assets.yourcompany.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name assets.yourcompany.com;

        # SSL certificates
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Static files
        location /static/ {
            alias /app/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        location /media/ {
            alias /app/mediafiles/;
            expires 7d;
        }

        # Application
        location / {
            limit_req zone=general burst=20 nodelay;
            
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
            proxy_buffering off;
        }

        # API endpoints (if you add JSON APIs)
        location /api/ {
            limit_req zone=api burst=50 nodelay;
            
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

---

## SSL/TLS Setup

### Option 1: Let's Encrypt (Free)

Install certbot:

```bash
sudo apt-get install certbot python3-certbot-nginx
```

Generate certificate:

```bash
sudo certbot --nginx -d assets.yourcompany.com
```

Auto-renewal:

```bash
sudo certbot renew --dry-run
```

### Option 2: Self-Signed (Development/Internal)

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/CN=assets.yourcompany.com"
```

### Option 3: Corporate Certificate

If your organization provides certificates, place them in `nginx/ssl/`:

- `nginx/ssl/fullchain.pem` (certificate chain)
- `nginx/ssl/privkey.pem` (private key)

---

## Backup & Restore

### Database Backup

**Daily automated backup script** (`backup.sh`):

```bash
#!/bin/bash
set -e

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="assetdb_${DATE}.sql.gz"

mkdir -p "$BACKUP_DIR"

docker compose exec -T db pg_dump -U assetdb_user assetdb_prod | gzip > "$BACKUP_DIR/$FILENAME"

echo "Backup completed: $FILENAME"

# Keep only last 30 days
find "$BACKUP_DIR" -name "assetdb_*.sql.gz" -mtime +30 -delete
```

**Add to crontab**:

```bash
0 2 * * * /path/to/backup.sh >> /var/log/assetdb_backup.log 2>&1
```

### Database Restore

```bash
# Stop the application
docker compose down

# Restore from backup
gunzip -c /backups/postgres/assetdb_20240115_020000.sql.gz | \
  docker compose exec -T db psql -U assetdb_user assetdb_prod

# Restart application
docker compose up -d
```

### Application Files Backup

Backup uploaded media files:

```bash
tar -czf mediafiles_$(date +%Y%m%d).tar.gz mediafiles/
```

---

## Monitoring & Logging

### 1. Application Logging

Configure logging in `config/settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/django.log',
            'maxBytes': 1024 * 1024 * 100,  # 100 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'assets': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 2. Docker Logs

View logs:

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web

# Last 100 lines
docker compose logs --tail=100 web
```

### 3. Health Checks

Add health check to `docker-compose.prod.yml`:

```yaml
services:
  web:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

Create health check view in `assets/views.py`:

```python
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Simple health check endpoint for monitoring"""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "healthy", "database": "ok"})
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=500)
```

### 4. Monitoring Tools (Optional)

Consider adding:

- **Prometheus** + **Grafana** for metrics
- **Sentry** for error tracking
- **Uptime monitoring** (UptimeRobot, Pingdom)

---

## Performance Optimization

### 1. Database Indexes

Ensure indexes exist on frequently queried fields:

```python
# In models.py, add db_index=True to frequently queried fields
class Asset(models.Model):
    asset_tag = models.CharField(max_length=100, unique=True, db_index=True)
    status = models.CharField(max_length=50, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
```

### 2. Query Optimization

Use `select_related()` and `prefetch_related()` to reduce queries:

```python
# In views.py
assets = Asset.objects.select_related('created_by').prefetch_related('hardware_scans', 'drives')
```

### 3. Caching (Optional)

Add Redis caching for frequently accessed data:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
    }
}
```

### 4. Gunicorn Workers

Adjust worker count based on CPU cores:

```bash
# Formula: (2 x CPU cores) + 1
# For 4 cores: 9 workers
gunicorn config.wsgi:application --workers 9 --bind 0.0.0.0:8000
```

---

## Maintenance Procedures

### Regular Maintenance Tasks

**Weekly:**
- [ ] Review error logs
- [ ] Check disk space usage
- [ ] Review backup logs
- [ ] Check database size growth

**Monthly:**
- [ ] Review and archive old audit logs (if needed)
- [ ] Update dependencies (`pip list --outdated`)
- [ ] Review security advisories
- [ ] Test backup restore procedure

**Quarterly:**
- [ ] Performance review and optimization
- [ ] Security audit
- [ ] Disaster recovery drill

### Updating the Application

1. **Test in staging first**
2. **Backup database**
3. **Pull new code**:
   ```bash
   git pull origin main
   ```
4. **Rebuild containers**:
   ```bash
   docker compose build
   ```
5. **Run migrations**:
   ```bash
   docker compose exec web python manage.py migrate
   ```
6. **Collect static files**:
   ```bash
   docker compose exec web python manage.py collectstatic --no-input
   ```
7. **Restart services**:
   ```bash
   docker compose restart web
   ```

### Emergency Procedures

**Database corruption:**
1. Stop application: `docker compose down`
2. Restore from last good backup
3. Verify data integrity
4. Restart application

**Application crash:**
1. Check logs: `docker compose logs web`
2. Check disk space: `df -h`
3. Check memory: `free -h`
4. Restart service: `docker compose restart web`

**Security breach:**
1. Take application offline immediately
2. Preserve logs for forensic analysis
3. Assess damage and data exposure
4. Notify stakeholders
5. Restore from clean backup
6. Change all credentials
7. Review and patch vulnerability

---

## Deployment Command Reference

```bash
# Initial production deployment
docker compose -f docker-compose.prod.yml up -d --build

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Run migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Collect static files
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input

# Backup database
docker compose -f docker-compose.prod.yml exec db pg_dump -U assetdb_user assetdb_prod > backup.sql

# Stop all services
docker compose -f docker-compose.prod.yml down

# Update application
git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

---

## Security Checklist

Before going live:

- [ ] SECRET_KEY is unique and stored securely
- [ ] DEBUG = False
- [ ] ALLOWED_HOSTS configured correctly
- [ ] Database credentials are strong and unique
- [ ] SSL/TLS certificates installed and valid
- [ ] HTTPS redirect enabled
- [ ] Security headers configured (HSTS, CSP, etc.)
- [ ] CSRF protection enabled
- [ ] Session cookies secure
- [ ] pgAdmin removed from production
- [ ] Default admin password changed
- [ ] File upload validation implemented
- [ ] Rate limiting configured
- [ ] Backup encryption enabled (if storing sensitive data)
- [ ] Firewall rules configured
- [ ] SSH key-based authentication only

---

## Support & Troubleshooting

### Common Issues

**Issue: Static files not loading**
- Solution: Run `collectstatic` and verify nginx volume mounts

**Issue: Database connection refused**
- Solution: Check DB_HOST, DB_PORT, and ensure db service is running

**Issue: 502 Bad Gateway**
- Solution: Check if Gunicorn is running: `docker compose logs web`

**Issue: Out of memory**
- Solution: Reduce Gunicorn worker count or increase server memory

### Getting Help

- Check logs: `docker compose logs`
- Review Django documentation: https://docs.djangoproject.com/
- Check project issues on GitHub
- Contact development team

---

**Last Updated:** 2024-01-XX  
**Version:** 1.0  
**Maintained By:** [Your Team Name]