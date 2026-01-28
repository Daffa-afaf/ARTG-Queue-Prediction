# 🚀 Deployment Guide

Panduan lengkap untuk deploy ARTG Queue Prediction System ke production environment.

---

## 📋 Pre-Deployment Checklist

- [ ] Model files sudah di-train dan di-test
- [ ] All tests passing (backend & frontend)
- [ ] Environment variables configured
- [ ] Production URLs updated
- [ ] Database backup (jika ada)
- [ ] SSL certificates ready
- [ ] Firewall rules configured

---

## 🖥️ Server Requirements

### Minimum Specifications

**Backend Server:**
- OS: Ubuntu 20.04 LTS / Windows Server 2019+
- CPU: 4 cores
- RAM: 8GB
- Storage: 20GB SSD
- Python: 3.8+

**Frontend Server (optional - bisa digabung):**
- Node.js: 16+
- Nginx/Apache untuk static files

**Network:**
- Port 5000: Flask Backend (internal)
- Port 3000: React Frontend (development)
- Port 80/443: Web server (production)
- WebSocket support required

---

## 🔧 Production Setup

### Option 1: Linux Server (Ubuntu)

#### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.8+
sudo apt install python3.8 python3.8-venv python3-pip -y

# Install Node.js 16+
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install nodejs -y

# Install Nginx
sudo apt install nginx -y

# Install supervisor (untuk background process)
sudo apt install supervisor -y
```

#### 2. Clone & Setup Project

```bash
# Create application directory
sudo mkdir -p /opt/artg-queue-prediction
cd /opt/artg-queue-prediction

# Clone repository
git clone <your-repo-url> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Download model files (jika belum ada)
# wget <model-files-url>
# unzip models.zip -d models/
```

#### 3. Configure Environment

```bash
# Create .env file
cat > .env << 'EOF'
FLASK_ENV=production
FLASK_PORT=5000
WEBSOCKET_EXTERNAL_URL=http://10.130.0.176
BACKEND_URL=http://10.5.11.242:5000
SECRET_KEY=<generate-random-secret>
EOF

# Set permissions
chmod 600 .env
```

#### 4. Setup Supervisor (Auto-restart)

```bash
# Create supervisor config
sudo nano /etc/supervisor/conf.d/artg-backend.conf
```

Add this configuration:
```ini
[program:artg-backend]
directory=/opt/artg-queue-prediction
command=/opt/artg-queue-prediction/venv/bin/python App.py
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/artg-backend.err.log
stdout_logfile=/var/log/artg-backend.out.log
environment=FLASK_ENV="production"
```

```bash
# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start artg-backend

# Check status
sudo supervisorctl status artg-backend
```

#### 5. Build Frontend

```bash
cd /opt/artg-queue-prediction/artg-dashboard

# Install dependencies
npm install

# Update production URLs in src/services/websocketService.js
nano src/services/websocketService.js
# Change localhost to production IP

# Build for production
npm run build

# Copy build to nginx
sudo cp -r build /var/www/artg-dashboard
```

#### 6. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/artg-queue-prediction
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name 10.5.11.242;  # Your server IP or domain

    # Frontend (React build)
    location / {
        root /var/www/artg-dashboard;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /socket.io/ {
        proxy_pass http://localhost:5000/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_buffering off;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/artg-queue-prediction /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

#### 7. Setup Firewall

```bash
# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS (if using SSL)
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

---

### Option 2: Windows Server

#### 1. Install Prerequisites

- Download & install Python 3.8+ from python.org
- Download & install Node.js 16+ from nodejs.org
- Download & install Git

#### 2. Clone Repository

```powershell
# Create directory
cd C:\
mkdir inetpub\artg-queue-prediction
cd C:\inetpub\artg-queue-prediction

# Clone
git clone <your-repo-url> .
```

#### 3. Setup Python Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

#### 4. Create Windows Service (NSSM)

Download NSSM (Non-Sucking Service Manager):
```powershell
# Download NSSM
Invoke-WebRequest -Uri https://nssm.cc/release/nssm-2.24.zip -OutFile nssm.zip
Expand-Archive nssm.zip
cd nssm\win64

# Install service
.\nssm.exe install ARTGBackend "C:\inetpub\artg-queue-prediction\venv\Scripts\python.exe" "C:\inetpub\artg-queue-prediction\App.py"

# Start service
.\nssm.exe start ARTGBackend
```

#### 5. Build Frontend

```powershell
cd C:\inetpub\artg-queue-prediction\artg-dashboard

# Install & build
npm install
npm run build
```

#### 6. Configure IIS (Internet Information Services)

1. Open IIS Manager
2. Add New Website:
   - Name: ARTG-Dashboard
   - Physical path: `C:\inetpub\artg-queue-prediction\artg-dashboard\build`
   - Port: 80
3. Add URL Rewrite rules for React Router
4. Add Reverse Proxy for `/api/` → `http://localhost:5000/`

---

## 🔒 Security Hardening

### 1. Change Default Ports (Optional)

```python
# In App.py
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080)  # Change from 5000
```

### 2. Enable HTTPS (SSL/TLS)

```bash
# Install certbot (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 3. Restrict API Access

Add to App.py:
```python
from flask import request
from functools import wraps

ALLOWED_IPS = ['10.5.11.0/24', '127.0.0.1']

def ip_whitelist(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.remote_addr not in ALLOWED_IPS:
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/blocks', methods=['GET'])
@ip_whitelist
def get_blocks():
    # ...
```

### 4. Environment Variables

Never commit sensitive data. Use environment variables:

```python
# App.py
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-key')
DEBUG = os.getenv('FLASK_ENV') != 'production'
```

---

## 📊 Monitoring & Logging

### 1. Setup Logging

```python
# App.py
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler(
        'logs/artg.log',
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('ARTG Backend startup')
```

### 2. Log Rotation

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/artg
```

```
/var/log/artg-backend.*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

### 3. Health Check Endpoint

Already exists at `GET /` - monitor this endpoint:

```bash
# Create monitoring script
cat > /opt/artg-queue-prediction/healthcheck.sh << 'EOF'
#!/bin/bash
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/)
if [ $RESPONSE -ne 200 ]; then
    echo "Backend unhealthy! HTTP $RESPONSE"
    sudo supervisorctl restart artg-backend
fi
EOF

chmod +x /opt/artg-queue-prediction/healthcheck.sh

# Add to crontab
crontab -e
# Add: */5 * * * * /opt/artg-queue-prediction/healthcheck.sh
```

---

## 🔄 Update Deployment

### Rolling Update Process

```bash
# 1. Pull latest code
cd /opt/artg-queue-prediction
git pull origin main

# 2. Activate virtual environment
source venv/bin/activate

# 3. Update dependencies (if changed)
pip install -r requirements.txt --upgrade

# 4. Regenerate lookup tables (if data changed)
python generate_lookups.py

# 5. Rebuild frontend (if changed)
cd artg-dashboard
npm install
npm run build
sudo cp -r build/* /var/www/artg-dashboard/

# 6. Restart backend
sudo supervisorctl restart artg-backend

# 7. Reload nginx (if config changed)
sudo nginx -t && sudo systemctl reload nginx

# 8. Verify deployment
curl http://localhost:5000/
```

---

## 🐳 Docker Deployment (Alternative)

### Dockerfile (Backend)

```dockerfile
FROM python:3.8-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "App.py"]
```

### Dockerfile (Frontend)

```dockerfile
FROM node:16-alpine AS build

WORKDIR /app
COPY artg-dashboard/package*.json ./
RUN npm install
COPY artg-dashboard/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./models:/app/models:ro
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

```bash
# Deploy with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Restart services
docker-compose restart
```

---

## 🧪 Post-Deployment Testing

### 1. Smoke Tests

```bash
# Health check
curl http://your-server-ip/

# API test
curl http://your-server-ip/blocks

# WebSocket test (use browser console)
# Open http://your-server-ip and check console
```

### 2. Load Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils -y

# Test API endpoint
ab -n 1000 -c 10 http://your-server-ip/blocks

# Expected: >100 requests/second
```

### 3. Monitoring Dashboard

Use tools like:
- **Grafana** + **Prometheus** for metrics
- **ELK Stack** for log analysis
- **PM2** for Node.js process monitoring
- **Supervisord** web interface

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue: Backend not starting**
```bash
# Check logs
sudo tail -f /var/log/artg-backend.err.log

# Common causes:
# - Port 5000 already in use
# - Model files missing
# - Permission issues
```

**Issue: Frontend shows blank page**
```bash
# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Check build output
ls -la /var/www/artg-dashboard/

# Common causes:
# - Wrong base path in React
# - Nginx config incorrect
# - CORS issues
```

**Issue: WebSocket not connecting**
```bash
# Check nginx config supports WebSocket
# Ensure proxy_set_header Upgrade and Connection set correctly

# Test WebSocket directly
wscat -c ws://your-server-ip:5000/socket.io/
```

---

## 📋 Rollback Plan

```bash
# 1. Checkout previous version
git log --oneline
git checkout <previous-commit-hash>

# 2. Reinstall old dependencies
pip install -r requirements.txt

# 3. Rebuild frontend
cd artg-dashboard && npm run build

# 4. Restart services
sudo supervisorctl restart artg-backend
sudo systemctl reload nginx
```

---

## 📝 Deployment Checklist

- [ ] Server meets minimum requirements
- [ ] Python virtual environment created
- [ ] Dependencies installed
- [ ] Model files downloaded and extracted
- [ ] Environment variables configured
- [ ] Backend running and accessible
- [ ] Frontend built and deployed
- [ ] Nginx/Web server configured
- [ ] SSL certificate installed (production)
- [ ] Firewall rules configured
- [ ] Logging configured
- [ ] Monitoring setup
- [ ] Health checks passing
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] Team trained on deployment

---

**Deployment Version:** 2.0  
**Last Updated:** 2026-01-28  
**Maintained By:** [Nama Mahasiswa Magang]

For production support: [email support]
