# Photo Restoration API - Deployment Guide

**Version:** 1.8.2
**Last Updated:** December 18, 2024
**Phase:** 1.10 - Documentation & Deployment

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Options](#deployment-options)
4. [Docker Compose Deployment (Recommended)](#docker-compose-deployment-recommended)
5. [Environment Configuration](#environment-configuration)
6. [nginx Configuration](#nginx-configuration)
7. [SSL/HTTPS Setup](#sslhttps-setup)
8. [Configuration File Management](#configuration-file-management)
9. [Health Checks & Monitoring](#health-checks--monitoring)
10. [Troubleshooting](#troubleshooting)
11. [Security Best Practices](#security-best-practices)
12. [Scaling & Performance](#scaling--performance)

---

## Overview

This guide covers deploying the Photo Restoration API in production environments. The application consists of:

- **Backend**: FastAPI Python application with AI model integration
- **Frontend**: React TypeScript SPA
- **Database**: SQLite (included) or PostgreSQL (recommended for production)
- **File Storage**: Local filesystem or cloud storage (S3/GCS)
- **AI Providers**: HuggingFace Inference API and/or Replicate API

**Recommended Stack:**
- Docker + Docker Compose
- nginx as reverse proxy
- SSL/TLS certificates (Let's Encrypt)
- Systemd for process management (alternative to Docker)

---

## Prerequisites

### Server Requirements

**Minimum:**
- 2 CPU cores
- 4 GB RAM
- 20 GB disk space
- Ubuntu 20.04+ / Debian 11+ / Rocky Linux 8+

**Recommended:**
- 4 CPU cores
- 8 GB RAM
- 50 GB SSD
- Ubuntu 22.04 LTS

### Software Requirements

- Docker 24.0+ and Docker Compose 2.20+
- nginx 1.18+ (for reverse proxy)
- certbot (for SSL certificates)
- Git (for deployment)

### API Keys Required

- HuggingFace API Token (required): Get from https://huggingface.co/settings/tokens
- Replicate API Token (optional): Get from https://replicate.com/account/api-tokens

---

## Deployment Options

### Option 1: Docker Compose (Recommended) ⭐

**Pros:**
- Easiest deployment and updates
- Consistent environment
- Built-in orchestration
- Easy rollback

**Cons:**
- Requires Docker knowledge
- Additional resource overhead

### Option 2: Systemd Services

**Pros:**
- Direct control
- Lower resource usage
- No Docker dependency

**Cons:**
- More complex setup
- Manual dependency management

### Option 3: Kubernetes

**Pros:**
- Enterprise-grade orchestration
- Auto-scaling
- High availability

**Cons:**
- Complex setup
- Overkill for small deployments

**This guide focuses on Option 1 (Docker Compose).**

---

## Docker Compose Deployment (Recommended)

### Step 1: Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Verify installation
docker --version
docker compose version

# Add user to docker group (logout required)
sudo usermod -aG docker $USER
```

### Step 2: Clone Repository

```bash
# Create deployment directory
sudo mkdir -p /opt/photo-restoration
sudo chown $USER:$USER /opt/photo-restoration
cd /opt/photo-restoration

# Clone repository
git clone https://github.com/yourusername/photo-restoration-webpage.git .

# Or download specific release
wget https://github.com/yourusername/photo-restoration/archive/v1.8.2.tar.gz
tar -xzf v1.8.2.tar.gz
```

### Step 3: Configure Environment

```bash
# Copy example environment file
cp backend/.env.example backend/.env

# Edit configuration (see Environment Configuration section)
nano backend/.env
```

**Required environment variables:**
```bash
# Application
APP_ENV=production
DEBUG=false
SECRET_KEY=GENERATE_A_SECURE_RANDOM_STRING_AT_LEAST_32_CHARS

# Authentication
AUTH_USERNAME=admin
AUTH_PASSWORD=CHANGE_THIS_TO_A_SECURE_PASSWORD

# AI Provider APIs
HF_API_KEY=hf_your_huggingface_api_key_here
REPLICATE_API_TOKEN=r8_your_replicate_token_here_optional

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/photo_restoration.db

# CORS - Add your domain
CORS_ORIGINS=["https://yourdomain.com"]
```

### Step 4: Configure JSON Config Files

```bash
# Copy default configuration
cp backend/config/default.json backend/config/production.json

# Edit production config
nano backend/config/production.json
```

**production.json example:**
```json
{
  "application": {
    "name": "Photo Restoration API",
    "version": "1.8.2",
    "debug": false
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 4
  },
  "cors": {
    "origins": ["https://yourdomain.com", "https://www.yourdomain.com"]
  },
  "models": [
    {
      "id": "swin2sr-2x",
      "name": "Swin2SR 2x Upscale",
      "model": "caidas/swin2SR-classical-sr-x2-64",
      "provider": "huggingface",
      "category": "upscale",
      "description": "Fast 2x upscaling",
      "enabled": true,
      "parameters": {"scale": 2}
    }
  ]
}
```

### Step 5: Build and Start Services

```bash
# Build Docker images
docker compose build

# Start services
docker compose up -d

# View logs
docker compose logs -f

# Check status
docker compose ps
```

### Step 6: Verify Deployment

```bash
# Check backend health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","app":"Photo Restoration API","version":"1.8.2"}

# Check frontend
curl http://localhost:3000

# Test API docs
curl http://localhost:8000/api/docs
```

---

## Environment Configuration

### Backend Environment Variables

**File:** `backend/.env`

#### Required Variables

```bash
# Application Settings
APP_ENV=production              # Environment: development, staging, production
DEBUG=false                     # Debug mode (false in production)
SECRET_KEY=<64-char-random>     # JWT secret (generate with: openssl rand -hex 32)

# Authentication (MVP - Single User)
AUTH_USERNAME=admin             # Admin username
AUTH_PASSWORD=<secure-password> # Strong password (min 12 chars)

# AI Provider API Keys
HF_API_KEY=hf_<your-key>       # HuggingFace API token (required)
REPLICATE_API_TOKEN=r8_<key>   # Replicate API token (optional)

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/photo_restoration.db

# CORS Origins (JSON array)
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
```

#### Optional Variables

```bash
# Server
HOST=0.0.0.0
PORT=8000

# File Upload
MAX_UPLOAD_SIZE=10485760        # 10 MB in bytes
ALLOWED_EXTENSIONS=[".jpg",".jpeg",".png"]

# Session Management
SESSION_CLEANUP_HOURS=24        # Delete old sessions after 24 hours
SESSION_CLEANUP_INTERVAL_HOURS=6

# API Timeouts
HF_API_TIMEOUT=60               # HuggingFace timeout (seconds)
REPLICATE_API_TIMEOUT=120       # Replicate timeout (seconds)

# Processing Limits
MAX_CONCURRENT_UPLOADS_PER_SESSION=3
```

### Frontend Environment Variables

**File:** `frontend/.env.production`

```bash
# API URL (backend endpoint)
VITE_API_URL=https://api.yourdomain.com

# App Configuration
VITE_APP_NAME="Photo Restoration"
VITE_APP_VERSION=1.8.2
```

### Environment-Specific Configurations

Create separate config files for each environment:

- `backend/config/development.json` - Development overrides
- `backend/config/staging.json` - Staging overrides
- `backend/config/production.json` - Production overrides

Set `APP_ENV` to match the config file to load.

---

## nginx Configuration

### Basic Configuration

**File:** `/etc/nginx/sites-available/photo-restoration`

```nginx
# Frontend (React SPA)
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    root /opt/photo-restoration/frontend/dist;
    index index.html;

    # Frontend static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;

    client_max_body_size 11M;  # Slightly larger than MAX_UPLOAD_SIZE

    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running AI processing
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }

    # Uploaded/processed images
    location /uploads/ {
        proxy_pass http://localhost:8000/uploads/;
    }

    location /processed/ {
        proxy_pass http://localhost:8000/processed/;
    }
}
```

### Enable Site

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/photo-restoration /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

---

## SSL/HTTPS Setup

### Using Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificates
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Manual Certificate Configuration

If using custom certificates:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256...';
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Rest of configuration...
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Configuration File Management

### Development vs Production

**Development:** Use `.env` files and default.json
**Production:** Use environment-specific JSON files + `.env` for secrets

### Configuration Priority

1. **Environment Variables** (highest priority)
2. **JSON Config Files** (`config/production.json`)
3. **Default Values** (`config/default.json`)

### Managing Secrets

**DO NOT** commit secrets to Git:

```bash
# backend/.gitignore
.env
.env.production
.env.staging
*.pem
*.key
```

**DO** use environment variables for:
- `SECRET_KEY`
- `AUTH_PASSWORD`
- `HF_API_KEY`
- `REPLICATE_API_TOKEN`

**DO** use JSON config for:
- Application settings
- Model configurations
- CORS origins
- Feature flags

### Docker Secrets (Advanced)

For Docker Swarm:

```yaml
services:
  backend:
    secrets:
      - hf_api_key
      - secret_key

secrets:
  hf_api_key:
    external: true
  secret_key:
    external: true
```

---

## Health Checks & Monitoring

### Health Endpoints

```bash
# Backend health
curl https://api.yourdomain.com/health

# Expected: {"status":"healthy","app":"Photo Restoration API","version":"1.8.2"}

# API docs
curl https://api.yourdomain.com/api/docs
```

### Docker Health Checks

Add to `docker-compose.yml`:

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Monitoring with Prometheus (Optional)

```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

### Log Management

```bash
# View backend logs
docker compose logs -f backend

# View last 100 lines
docker compose logs --tail=100 backend

# Export logs
docker compose logs backend > backend.log
```

**Configure log rotation:**

```yaml
# docker-compose.yml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## Troubleshooting

### Common Issues

#### 1. Backend won't start

**Symptom:** Container exits immediately

**Solutions:**
```bash
# Check logs
docker compose logs backend

# Common causes:
# - Missing .env file → Copy from .env.example
# - Invalid JSON config → Validate with: python -m json.tool config/production.json
# - Database permission error → Check volume permissions
```

#### 2. Frontend can't connect to API

**Symptom:** Network errors in browser console

**Solutions:**
```bash
# Check CORS configuration
# backend/config/production.json
{
  "cors": {
    "origins": ["https://yourdomain.com"]  # Must match frontend URL
  }
}

# Verify nginx proxy
sudo nginx -t
sudo systemctl status nginx

# Check backend is running
curl http://localhost:8000/health
```

#### 3. Image upload fails

**Symptom:** 413 Request Entity Too Large

**Solutions:**
```nginx
# Increase nginx client_max_body_size
server {
    client_max_body_size 20M;  # Must be > MAX_UPLOAD_SIZE
}
```

```bash
# Restart nginx
sudo systemctl reload nginx
```

#### 4. AI processing timeout

**Symptom:** 504 Gateway Timeout

**Solutions:**
```nginx
# Increase proxy timeouts in nginx
location /api/ {
    proxy_read_timeout 600s;  # 10 minutes
    proxy_send_timeout 600s;
}
```

```bash
# Or increase backend timeout
# backend/.env
HF_API_TIMEOUT=300  # 5 minutes
```

#### 5. Models not loading

**Symptom:** Empty models list

**Solutions:**
```bash
# Check config file exists
ls -la backend/config/production.json

# Validate JSON
python3 -m json.tool backend/config/production.json

# Verify APP_ENV matches config file
grep APP_ENV backend/.env
# Should be: APP_ENV=production

# Check logs for config loading
docker compose logs backend | grep -i "config"
```

### Debug Mode

Enable for troubleshooting (temporarily):

```bash
# backend/.env
DEBUG=true
```

```bash
# Restart backend
docker compose restart backend

# View detailed logs
docker compose logs -f backend
```

**⚠️ IMPORTANT:** Disable DEBUG mode in production after troubleshooting.

---

## Security Best Practices

### 1. Secure Secrets

```bash
# Generate strong SECRET_KEY
openssl rand -hex 32

# Use strong passwords (min 16 characters)
openssl rand -base64 16

# Rotate secrets regularly (every 90 days)
```

### 2. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Block direct access to backend port
# Backend should only be accessible via nginx
```

### 3. Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker compose pull
docker compose up -d

# Update application
cd /opt/photo-restoration
git pull origin main
docker compose build
docker compose up -d
```

### 4. Backup Strategy

```bash
# Backup script (example)
#!/bin/bash
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/backups/photo-restoration"

# Backup database
cp /opt/photo-restoration/backend/data/photo_restoration.db \
   $BACKUP_DIR/db-$DATE.db

# Backup uploaded images
tar -czf $BACKUP_DIR/uploads-$DATE.tar.gz \
   /opt/photo-restoration/backend/data/uploads

# Backup config
cp -r /opt/photo-restoration/backend/config \
   $BACKUP_DIR/config-$DATE/

# Clean old backups (keep last 30 days)
find $BACKUP_DIR -type f -mtime +30 -delete
```

```bash
# Add to crontab (daily at 2 AM)
0 2 * * * /opt/scripts/backup-photo-restoration.sh
```

### 5. Rate Limiting

Add to nginx:

```nginx
# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    # ... rest of config
}
```

---

## Scaling & Performance

### Horizontal Scaling

**Multiple Backend Instances:**

```yaml
services:
  backend:
    deploy:
      replicas: 3
```

**Load Balancing with nginx:**

```nginx
upstream backend {
    least_conn;  # Load balancing method
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    location /api/ {
        proxy_pass http://backend;
    }
}
```

### Database Optimization

**Migrate to PostgreSQL for production:**

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE photo_restoration;
CREATE USER photoapp WITH ENCRYPTED PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE photo_restoration TO photoapp;
```

```bash
# Update backend/.env
DATABASE_URL=postgresql+asyncpg://photoapp:password@localhost/photo_restoration
```

### Caching Strategy

**Redis for session storage:**

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### CDN Integration

Use CDN for static assets:

- Uploaded images → S3 + CloudFront
- Frontend assets → CloudFlare CDN

---

## Maintenance

### Updates

```bash
# Pull latest changes
cd /opt/photo-restoration
git fetch --tags
git checkout v1.8.3  # New version

# Rebuild and restart
docker compose build
docker compose up -d

# Verify
curl http://localhost:8000/health
```

### Rollback

```bash
# If update fails, rollback
git checkout v1.8.2
docker compose build
docker compose up -d
```

### Database Migrations

```bash
# When database schema changes
docker compose exec backend alembic upgrade head
```

---

## Support & Resources

- **Documentation:** `/docs` directory
- **API Docs:** `https://api.yourdomain.com/api/docs`
- **Issues:** GitHub Issues
- **Configuration Reference:** [docs/configuration.md](./configuration.md)
- **DEBUG Logging:** [docs/DEBUG_LOGGING.md](./DEBUG_LOGGING.md)

---

**Document Version:** 1.0
**Phase:** 1.10 - Documentation & Deployment ✅
**Last Updated:** December 18, 2024
