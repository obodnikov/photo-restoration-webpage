# Implementation Guide

This document provides detailed implementation instructions, configuration examples, and deployment options for the Photo Restoration web application.

---

## Table of Contents

1. [Docker Deployment](#docker-deployment)
2. [nginx Reverse Proxy Configuration](#nginx-reverse-proxy-configuration)
3. [Production Deployment](#production-deployment)
4. [Environment-Specific Configurations](#environment-specific-configurations)
5. [Monitoring and Logging](#monitoring-and-logging)

---

## Docker Deployment

### Building Docker Images

#### Prerequisites

The project uses exact version pinning for dependencies and requires specific build environments.

**Important:** The frontend requires a `package-lock.json` file for reproducible builds. If this file is missing, generate it using Docker to ensure compatibility with the exact Node.js version (22.12-alpine) used in the Dockerfile.

#### Generate package-lock.json (if missing)

Run this command on your build machine to generate the lockfile using the exact Node.js version:

```bash
cd ~/src/photo-restoration-webpage
docker run --rm -v "$PWD/frontend:/app" -w /app node:22.12-alpine npm install
```

**What this does:**
- Uses the exact same Node.js 22.12-alpine image as the Dockerfile
- Mounts your frontend directory to `/app` in the container
- Runs `npm install` to generate `package-lock.json` with exact dependency versions
- Automatically removes the container when done

**Verify the file was created:**
```bash
ls -lh frontend/package-lock.json
```

#### Build Individual Images

**Backend:**
```bash
docker build -t obodnikov/photo-restoration-backend:0.1.2 ./backend
```

**Frontend:**

The frontend supports build-time configuration via build arguments. Choose the appropriate build command based on your deployment scenario:

**Scenario 1: With nginx reverse proxy (default, recommended)**
```bash
docker build -t obodnikov/photo-restoration-frontend:0.1.2 ./frontend
```

**Scenario 2: Direct connection to backend container (Docker network)**
```bash
docker build \
  --build-arg VITE_API_BASE_URL=http://backend:8000/api/v1 \
  -t obodnikov/photo-restoration-frontend:0.1.2 \
  ./frontend
```

**Scenario 3: Direct connection to backend on external host**
```bash
# Replace with your backend server IP/hostname
docker build \
  --build-arg VITE_API_BASE_URL=http://192.168.1.10:8000/api/v1 \
  -t obodnikov/photo-restoration-frontend:0.1.2 \
  ./frontend
```

**All available build arguments:**
- `VITE_API_BASE_URL` - Backend API URL (default: `/api/v1`)
- `VITE_APP_NAME` - Application name (default: `"Photo Restoration"`)
- `VITE_APP_VERSION` - Application version (default: `"1.0.0"`)

**nginx:**
```bash
docker build -t obodnikov/photo-restoration-nginx:0.1.2 ./nginx
```

#### Python 3.13 Compatibility

The backend has been updated to use Python 3.13 with compatible dependency versions:
- FastAPI 0.115.7
- Pydantic 2.10.6
- Pillow 10.4.0
- All other dependencies updated for Python 3.13 compatibility

See [backend/requirements.txt](../backend/requirements.txt) for the complete list.

#### TypeScript Compilation Testing

**IMPORTANT: Definition of Done (DoD) for TypeScript code changes**

Before committing any TypeScript code changes, you MUST run the TypeScript compilation test to ensure there are no type errors.

**Run the test:**

```bash
# From the frontend directory
cd frontend
npm run test:typecheck

# Or use the typecheck command
npm run typecheck
```

**What this does:**
- Runs TypeScript compiler in check-only mode (`tsc --noEmit`)
- Validates all TypeScript files without generating output
- Reports any type errors or compilation issues
- Must pass with zero errors before code is committed

**Example output (success):**
```
> photo-restoration-frontend@1.0.0 test:typecheck
> tsc --noEmit && echo 'TypeScript compilation successful!'

TypeScript compilation successful!
```

**Example output (failure):**
```
src/services/apiClient.ts(67,5): error TS7053: Element implicitly has an 'any' type...
```

**When to run:**
- Before every commit
- After modifying any `.ts` or `.tsx` file
- As part of CI/CD pipeline
- Before creating a pull request

**Integration with Docker:**

The Docker build process already includes TypeScript compilation as part of `npm run build`. However, running the test locally before building saves time by catching errors early.

#### Environment Variable Format Requirements

**IMPORTANT:** The backend configuration requires JSON array format for list and set fields.

**Affected Variables:**
- `CORS_ORIGINS` - List of allowed CORS origins
- `ALLOWED_EXTENSIONS` - Set of allowed file extensions

**Required Format:**

```bash
# Correct (JSON array format)
CORS_ORIGINS=["http://localhost:3000","http://localhost"]
ALLOWED_EXTENSIONS=[".jpg",".jpeg",".png"]

# Incorrect (comma-separated - will fail)
CORS_ORIGINS=http://localhost:3000,http://localhost
ALLOWED_EXTENSIONS=.jpg,.jpeg,.png
```

**Why JSON Format?**

The backend uses `pydantic-settings` 2.7.1, which automatically parses list/set environment variables as JSON. This ensures:
- Type safety and validation
- Consistent parsing across all environments
- No ambiguity with commas in URLs or values
- Native Python data structures

**Migration from Older Versions:**

If you're upgrading from a version that used comma-separated format:

1. Update your `.env` file:
   ```bash
   # Old format
   CORS_ORIGINS=http://localhost:3000,http://localhost,http://example.com

   # New format
   CORS_ORIGINS=["http://localhost:3000","http://localhost","http://example.com"]
   ```

2. Rebuild your containers:
   ```bash
   docker-compose down
   docker-compose up --build
   ```

3. Verify the configuration:
   ```bash
   docker logs photo-restoration-backend | grep "CORS"
   ```

### Docker Compose (Recommended)

The application uses Docker Compose for orchestration. See [README.md](../README.md) for quick start.

**Production:**
```bash
docker-compose up -d --build
```

**Development:**
```bash
docker-compose -f docker-compose.dev.yml up --build
```

### Individual Docker Run Commands

If you prefer to run containers individually without Docker Compose, choose the deployment scenario that matches your setup:

**Quick Decision Guide:**
- **Scenario A (nginx)**: Production deployment, need SSL/TLS, caching, security headers → Use this
- **Scenario B (direct)**: Simple deployment, single server, development → Use this
- **Scenario C (external)**: Multi-server setup, backend on different machine → Use this

---

#### Deployment Scenario A: With nginx Reverse Proxy (Recommended)

This is the recommended production setup. nginx handles routing, SSL/TLS, caching, and security headers.

**1. Create Network**
```bash
docker network create photo-restoration-network
```

**2. Build Images**
```bash
# Backend
docker build -t photo-restoration-backend:latest ./backend

# Frontend (with default relative path for nginx)
docker build -t photo-restoration-frontend:latest ./frontend

# nginx
docker build -t photo-restoration-nginx:latest ./nginx
```

**3. Run Backend**
```bash
docker run -d \
  --name photo-restoration-backend \
  --network photo-restoration-network \
  -v photo-restoration-data:/data \
  -e HF_API_KEY=your_huggingface_api_key \
  -e SECRET_KEY=your_secret_key_min_32_chars \
  -e AUTH_USERNAME=admin \
  -e AUTH_PASSWORD=changeme \
  -e DEBUG=false \
  -e DATABASE_URL=sqlite+aiosqlite:///data/photo_restoration.db \
  --restart unless-stopped \
  photo-restoration-backend:latest
```

**4. Wait for Backend Health Check**
```bash
# Wait for backend to be healthy (may take 10-30 seconds)
until docker exec photo-restoration-backend python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5.0)" 2>/dev/null; do
  echo "Waiting for backend to be healthy..."
  sleep 2
done
echo "Backend is healthy!"
```

**5. Run Frontend**
```bash
docker run -d \
  --name photo-restoration-frontend \
  --network photo-restoration-network \
  --restart unless-stopped \
  photo-restoration-frontend:latest
```

**6. Run nginx Reverse Proxy**
```bash
docker run -d \
  --name photo-restoration-nginx \
  --network photo-restoration-network \
  -p 80:80 \
  -p 443:443 \
  --restart unless-stopped \
  photo-restoration-nginx:latest
```

**7. Verify Deployment**
```bash
# Check all containers are running
docker ps --filter "name=photo-restoration"

# Check nginx can reach backend
curl http://localhost/health

# Check logs if there are issues
docker logs photo-restoration-nginx
```

---

#### Deployment Scenario B: Direct Frontend-to-Backend (Without nginx)

In this setup, frontend connects directly to backend. Useful for development or simple deployments.

**1. Create Network**
```bash
docker network create photo-restoration-network
```

**2. Build Images**
```bash
# Backend
docker build -t photo-restoration-backend:latest ./backend

# Frontend (configured to connect directly to backend)
docker build \
  --build-arg VITE_API_BASE_URL=http://backend:8000/api/v1 \
  -t photo-restoration-frontend:latest \
  ./frontend
```

**3. Run Backend**
```bash
docker run -d \
  --name photo-restoration-backend \
  --network photo-restoration-network \
  -v photo-restoration-data:/data \
  -e HF_API_KEY=your_huggingface_api_key \
  -e SECRET_KEY=your_secret_key_min_32_chars \
  -e AUTH_USERNAME=admin \
  -e AUTH_PASSWORD=changeme \
  -e DEBUG=false \
  -e DATABASE_URL=sqlite+aiosqlite:///data/photo_restoration.db \
  -e CORS_ORIGINS='["http://localhost","http://localhost:3000"]' \
  -p 8000:8000 \
  --restart unless-stopped \
  photo-restoration-backend:latest
```

**Important:** When not using nginx, you must:
- Expose backend port (`-p 8000:8000`)
- Configure CORS to allow frontend origin in backend `.env`

**4. Run Frontend**
```bash
docker run -d \
  --name photo-restoration-frontend \
  --network photo-restoration-network \
  -p 80:80 \
  --restart unless-stopped \
  photo-restoration-frontend:latest
```

**5. Verify Deployment**
```bash
# Check containers
docker ps --filter "name=photo-restoration"

# Test backend directly
curl http://localhost:8000/health

# Test frontend
curl http://localhost/
```

---

#### Deployment Scenario C: External Backend Server

Frontend connects to backend on a different server/host.

**1. Build Frontend with External Backend URL**
```bash
# Replace with your actual backend server address
docker build \
  --build-arg VITE_API_BASE_URL=http://192.168.1.10:8000/api/v1 \
  -t photo-restoration-frontend:latest \
  ./frontend
```

**2. Run Frontend**
```bash
docker run -d \
  --name photo-restoration-frontend \
  -p 80:80 \
  --restart unless-stopped \
  photo-restoration-frontend:latest
```

**Note:** Backend must be configured with appropriate CORS settings to allow requests from the frontend's origin.

### Docker Run with Environment File

Create a `.env` file and use it with Docker:

```bash
docker run -d \
  --name photo-restoration-backend \
  --network photo-restoration-network \
  -v photo-restoration-data:/data \
  --env-file ./backend/.env \
  --restart unless-stopped \
  photo-restoration-backend:latest
```

### Useful Docker Commands

**View logs:**
```bash
docker logs -f photo-restoration-backend
docker logs -f photo-restoration-frontend
docker logs -f photo-restoration-nginx
```

**Stop containers:**
```bash
docker stop photo-restoration-backend photo-restoration-frontend photo-restoration-nginx
```

**Remove containers:**
```bash
docker rm photo-restoration-backend photo-restoration-frontend photo-restoration-nginx
```

**Clean up network:**
```bash
docker network rm photo-restoration-network
```

**Clean up volume:**
```bash
docker volume rm photo-restoration-data
```

---

## nginx Reverse Proxy Configuration

### Standalone nginx Configuration

If you're running the application with an external nginx server (not the containerized one), use this configuration:

#### Basic Configuration (HTTP Only)

**File:** `/etc/nginx/sites-available/photo-restoration`

```nginx
upstream backend {
    server localhost:8000;
    keepalive 32;
}

upstream frontend {
    server localhost:3000;
    keepalive 32;
}

server {
    listen 80;
    server_name photo-restoration.yourdomain.com;

    # Max upload size for images
    client_max_body_size 10M;

    # Logging
    access_log /var/log/nginx/photo-restoration-access.log;
    error_log /var/log/nginx/photo-restoration-error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/javascript application/xml+rss application/json
               image/svg+xml;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # API endpoints - proxy to backend
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Extended timeouts for AI processing
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
    }

    # Health check
    location /health {
        proxy_pass http://backend/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        access_log off;
    }

    # Uploaded images
    location /uploads {
        proxy_pass http://backend/uploads;
        proxy_http_version 1.1;
        proxy_set_header Host $host;

        # Cache uploaded images
        expires 1h;
        add_header Cache-Control "public";
    }

    # Processed images
    location /processed {
        proxy_pass http://backend/processed;
        proxy_http_version 1.1;
        proxy_set_header Host $host;

        # Cache processed images
        expires 1h;
        add_header Cache-Control "public";
    }

    # Frontend - everything else
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Error pages
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

**Enable the site:**
```bash
sudo ln -s /etc/nginx/sites-available/photo-restoration /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### HTTPS Configuration with SSL/TLS

**File:** `/etc/nginx/sites-available/photo-restoration-ssl`

```nginx
upstream backend {
    server localhost:8000;
    keepalive 32;
}

upstream frontend {
    server localhost:3000;
    keepalive 32;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name photo-restoration.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name photo-restoration.yourdomain.com;

    # SSL certificates (Let's Encrypt example)
    ssl_certificate /etc/letsencrypt/live/photo-restoration.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/photo-restoration.yourdomain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Max upload size
    client_max_body_size 10M;

    # Logging
    access_log /var/log/nginx/photo-restoration-access.log;
    error_log /var/log/nginx/photo-restoration-error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/javascript application/xml+rss application/json
               image/svg+xml;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob:;" always;

    # API endpoints
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;

        # Extended timeouts for AI processing
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
    }

    # Health check
    location /health {
        proxy_pass http://backend/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        access_log off;
    }

    # Uploaded images
    location /uploads {
        proxy_pass http://backend/uploads;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        expires 1h;
        add_header Cache-Control "public";
    }

    # Processed images
    location /processed {
        proxy_pass http://backend/processed;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        expires 1h;
        add_header Cache-Control "public";
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    # Error pages
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

#### Getting SSL Certificate with Let's Encrypt

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d photo-restoration.yourdomain.com

# Auto-renewal (certbot sets this up automatically)
sudo certbot renew --dry-run
```

### Docker nginx with Custom Configuration

If using Docker but want custom nginx config:

**docker-compose.override.yml:**
```yaml
version: '3.8'

services:
  nginx:
    volumes:
      - ./nginx/custom.conf:/etc/nginx/conf.d/default.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    ports:
      - "443:443"
```

---

## Production Deployment

### Pre-deployment Checklist

- [ ] Set strong `SECRET_KEY` (minimum 32 characters) - **CRITICAL for security**
- [ ] Set secure `AUTH_PASSWORD`
- [ ] Configure `HF_API_KEY`
- [ ] Set `DEBUG=false`
- [ ] Configure proper domain in nginx
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall (allow 80, 443)
- [ ] Set up log rotation
- [ ] Configure backup for SQLite database
- [ ] Test health endpoints
- [ ] Set up monitoring (optional)

### Understanding SECRET_KEY

**What is SECRET_KEY?**

The `SECRET_KEY` is a cryptographic secret used by the backend to sign and verify JWT (JSON Web Tokens) for user authentication. This key is **critical for security**.

**Why is it important?**

1. **Token Signing**: All JWT tokens issued by the application are signed with this key
2. **Token Verification**: When users make authenticated requests, the backend verifies tokens using this key
3. **Security**: If someone gains access to your SECRET_KEY, they can:
   - Create valid tokens for any user
   - Bypass authentication entirely
   - Impersonate users
   - Access protected resources

**Requirements:**

- **Minimum length**: 32 characters (recommended: 64+ characters)
- **Randomness**: Must be cryptographically random, not a password or phrase
- **Uniqueness**: Must be unique per environment (dev, staging, production)
- **Secrecy**: Never commit to version control, never share, never reuse

**Important Notes:**

⚠️ **Changing the SECRET_KEY will invalidate ALL existing user sessions/tokens**
- Users will be logged out
- All existing JWT tokens will become invalid
- This is a security feature, not a bug

⚠️ **NEVER use the default or example value in production**
- The default value in `.env.example` is for demonstration only
- Always generate a new, random key for each environment

⚠️ **Store securely**
- Use environment variables or secure secret management (e.g., AWS Secrets Manager, HashiCorp Vault)
- Restrict file permissions: `chmod 600 .env`
- Never log or print the SECRET_KEY value

### Environment Variables for Production

**backend/.env:**
```bash
# PRODUCTION SETTINGS
DEBUG=false
APP_NAME="Photo Restoration API"
APP_VERSION="1.0.0"

# Server
HOST=0.0.0.0
PORT=8000

# CORS - Update with your domain (JSON array format required)
# Example: CORS_ORIGINS=["https://photo-restoration.yourdomain.com","https://www.yourdomain.com"]
CORS_ORIGINS=["https://photo-restoration.yourdomain.com"]

# Security - CHANGE THESE!
SECRET_KEY=GENERATE_A_STRONG_RANDOM_KEY_AT_LEAST_32_CHARACTERS_LONG
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Auth
AUTH_USERNAME=admin
AUTH_PASSWORD=USE_A_STRONG_PASSWORD_HERE

# HuggingFace
HF_API_KEY=your_huggingface_api_key_here
HF_API_TIMEOUT=60

# Database
DATABASE_URL=sqlite+aiosqlite:///data/photo_restoration.db

# File Storage
UPLOAD_DIR=/data/uploads
PROCESSED_DIR=/data/processed
MAX_UPLOAD_SIZE=10485760
# Allowed file extensions (JSON array format required)
ALLOWED_EXTENSIONS=[".jpg",".jpeg",".png"]

# Session
SESSION_CLEANUP_HOURS=24
```

### Generate Secure SECRET_KEY

**Always generate a new, cryptographically random SECRET_KEY. Never reuse keys across environments.**

**Method 1: Python (Recommended - produces URL-safe string)**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Output example: xvKp3jZ8qR_yN2mL5wT9hF6dC4sA1bE0

# For extra security, use 64 characters:
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

**Method 2: OpenSSL**
```bash
openssl rand -base64 32
# Output example: 3kJ8mN2pQ5rT9vW1xZ4aC6bD8eF0gH2i

# For 64 characters:
openssl rand -base64 64
```

**Method 3: Node.js**
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
# Output example: 7uY9tR3eW6qP2mN8vC5xZ1aS4fG0hJ3k
```

**Method 4: Linux /dev/urandom**
```bash
head -c 32 /dev/urandom | base64
```

**After generation:**
1. Copy the output
2. Paste into your `.env` file: `SECRET_KEY=<generated_value>`
3. **Never commit this file to version control**
4. Ensure `.env` is in your `.gitignore`
5. Verify file permissions: `chmod 600 backend/.env`

**Testing your SECRET_KEY:**
```bash
# Check length (should be 32+ characters)
echo -n "your_secret_key_here" | wc -c

# Verify it's set correctly (backend must be running)
curl http://localhost:8000/health
```

### Database Backup

**Automated backup script:**

```bash
#!/bin/bash
# backup-db.sh

BACKUP_DIR="/backups/photo-restoration"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_PATH="/path/to/data/photo_restoration.db"

mkdir -p $BACKUP_DIR

# Backup database
sqlite3 $DB_PATH ".backup $BACKUP_DIR/photo_restoration_$TIMESTAMP.db"

# Keep only last 30 days
find $BACKUP_DIR -name "photo_restoration_*.db" -mtime +30 -delete

echo "Backup completed: photo_restoration_$TIMESTAMP.db"
```

**Add to crontab:**
```bash
# Daily backup at 2 AM
0 2 * * * /path/to/backup-db.sh
```

### Log Rotation

**File:** `/etc/logrotate.d/photo-restoration`

```
/var/log/nginx/photo-restoration-*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}

/path/to/data/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 nobody nogroup
}
```

---

## Environment-Specific Configurations

### Development

Use `docker-compose.dev.yml` with hot reload:

```bash
docker-compose -f docker-compose.dev.yml up --build
```

**Features:**
- Hot reload for backend (uvicorn --reload)
- Hot reload for frontend (Vite dev server)
- Mounted source code volumes
- Debug mode enabled
- Direct port exposure (8000, 3000)

### Staging

Similar to production but with:
- Separate database
- Test HuggingFace API key
- Relaxed security (for testing)
- Different domain

### Production

See [Production Deployment](#production-deployment) section above.

---

## Monitoring and Logging

### Health Check Endpoints

**Backend Health:**
```bash
curl http://localhost/health
```

**Response:**
```json
{
  "status": "healthy",
  "app": "Photo Restoration API",
  "version": "1.0.0"
}
```

### Docker Health Checks

All containers have health checks configured in docker-compose.yml:

```bash
# Check container health
docker ps

# View health check logs
docker inspect --format='{{json .State.Health}}' photo-restoration-backend | jq
```

### Application Logs

**Backend logs:**
```bash
docker logs -f photo-restoration-backend
```

**Frontend logs:**
```bash
docker logs -f photo-restoration-frontend
```

**nginx logs:**
```bash
docker logs -f photo-restoration-nginx

# Or system nginx
tail -f /var/log/nginx/photo-restoration-access.log
tail -f /var/log/nginx/photo-restoration-error.log
```

### Monitoring Metrics (Optional)

For production, consider:
- **Prometheus** + **Grafana** for metrics
- **Sentry** for error tracking
- **Uptime monitoring** (UptimeRobot, Pingdom)
- **Log aggregation** (ELK stack, Loki)

---

## Troubleshooting

### Common Issues

**1. Backend can't connect to database**
```bash
# Check data directory permissions
ls -la data/
chmod 755 data/

# Check database file
ls -la data/*.db*
```

**2. nginx can't reach backend/frontend**
```bash
# Check network
docker network inspect photo-restoration-network

# Check service names resolution
docker exec -it photo-restoration-nginx ping backend
docker exec -it photo-restoration-nginx ping frontend
```

**3. SSL certificate issues**
```bash
# Check certificate expiration
sudo certbot certificates

# Renew manually
sudo certbot renew
```

**4. Image upload fails**
```bash
# Check upload directory
ls -la data/uploads/
chmod 755 data/uploads/

# Check max upload size in nginx
grep client_max_body_size /etc/nginx/sites-available/photo-restoration
```

### Performance Tuning

**nginx worker processes:**
```nginx
# In nginx.conf
worker_processes auto;
worker_connections 1024;
```

**Backend workers (for production):**
```bash
# Run with multiple workers
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

**Database optimization:**
```sql
-- Run periodic VACUUM
sqlite3 data/photo_restoration.db "VACUUM;"

-- Analyze query performance
sqlite3 data/photo_restoration.db ".eqp on"
```

---

## Support

For issues:
1. Check this implementation guide
2. Review [README.md](../README.md) troubleshooting section
3. Check application logs
4. Review [ROADMAP.md](../ROADMAP.md) for known limitations

---

**Last Updated:** December 13, 2024
