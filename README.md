# Photo Restoration Webpage

AI-powered web application for restoring old scanned photos using multiple AI providers (HuggingFace, Replicate). Built with FastAPI backend, React frontend, and deployed with Docker and nginx reverse proxy.

## Project Status

**Version:** 1.0.0
**Current Phase:** Phase 2 - Enhanced Features
**Latest:** Phase 2.4 Complete ✅ (Enhanced Authentication with Admin Panel + Profile Management)
**Phase 1 Complete:** All 8 phases ✅ (Infrastructure, Auth, Models, HF Integration, Session Management, Restoration API, Frontend Features, UI/UX)

## Features

### Core Functionality ✅
- **Image Restoration** - AI-powered photo restoration with drag-and-drop upload
- **Multiple AI Providers** - HuggingFace + Replicate integration
- **Model Selection** - Choose from various upscaling and enhancement models
- **Before/After Comparison** - Interactive image viewer with 3 display modes
- **History Management** - View, download, and manage all processed images
- **Session Management** - Automatic cleanup and file organization

### Authentication & User Management ✅
- **JWT Authentication** - Secure token-based auth with Remember Me (7 days)
- **Database-Backed Users** - SQLite user management with role-based access
- **Admin Panel** - User CRUD operations, role management, password reset
- **Profile Management** - View profile, change password, manage active sessions
- **Multi-Device Support** - Multiple sessions per user with remote logout
- **Password Security** - Complexity requirements, bcrypt hashing, force change on first login

### Technical Features ✅
- **Async Architecture** - FastAPI + SQLAlchemy async for high performance
- **Multi-Provider Support** - Configurable HuggingFace + Replicate models
- **Custom Model Parameters UI** - Dynamic parameter controls with 8 UI types, auto-detection, and custom overrides
  - 📖 See [Custom Model Parameters Guide](docs/CUSTOM_MODEL_PARAMETERS_GUIDE.md) for detailed documentation
- **File Storage** - Session-based organization with UUID prefixes
- **Background Cleanup** - Automated removal of old sessions and files
- **Responsive Design** - Mobile-first with sqowe brand styling
- **Accessibility** - WCAG AA compliance with comprehensive testing
- **Comprehensive Tests** - 224 frontend + 279 backend tests (99% coverage)

### Configuration & Deployment ✅
- **JSON Configuration** - Structured config files with Pydantic validation
- **Environment Support** - Dev, staging, production configs
- **Docker Deployment** - Multi-stage builds with nginx reverse proxy
- **Health Checks** - Backend API and database monitoring
- **Debug Logging** - Detailed logging with DEBUG environment variable

### In Progress & Planned
- ⏳ **Testing & QA** - Unit/integration tests for Phase 2.4 features
- **Phase 2 Next** - Model pipelines, batch processing, rate limiting
- **Phase 3 Planned** - OwnCloud integration, video frame restoration
- **Phase 4 Planned** - Production polish, monitoring, security hardening

📖 **Documentation:**
- [ROADMAP.md](ROADMAP.md) - Current and future development plans
- [DONE_TASKS.md](DONE_TASKS.md) - Complete history of implemented features
- [TECHNICAL_DEBTS.md](TECHNICAL_DEBTS.md) - Non-blocking improvements and enhancements
- [Custom Model Parameters Guide](docs/CUSTOM_MODEL_PARAMETERS_GUIDE.md) - Configure model parameters UI (v1.9.0+)

## Tech Stack

**Backend:**
- Python 3.13+ (latest stable)
- FastAPI (async REST API)
- SQLAlchemy (async ORM)
- SQLite (database)
- **AI Providers:**
  - HuggingFace Inference API (upscaling, enhancement)
  - Replicate API (advanced restoration models)
- JWT authentication

**Frontend:**
- React 18
- TypeScript (strict mode)
- Vite (build tool)
- Zustand (state management)
- sqowe brand design system

**Deployment:**
- Docker & Docker Compose
- External reverse proxy (nginx, Apache, Traefik, Caddy, etc.)
- Multi-stage builds
- Simple static file server (serve npm package) for frontend

## Prerequisites

- Docker & Docker Compose
- **AI Provider API Keys:**
  - HuggingFace API key ([Get one here](https://huggingface.co/settings/tokens))
  - Replicate API token ([Get one here](https://replicate.com/account/api-tokens)) - **Optional**, only needed if using Replicate models

**For local development:**
- Python 3.13+ (recommended for best performance)
- Node.js 22+ (LTS, minimum: 22.12)
- npm or yarn

## Quick Start (Docker)

### 1. Clone the repository

```bash
git clone <repository-url>
cd photo-restoration-webpage
```

### 2. Configure application (Phase 1.8.2+)

**NEW Configuration System:**
As of Phase 1.8.2, configuration is split between `.env` (secrets) and `config/*.json` files (settings).

**Step 2a: Set up secrets (`.env` file)**
```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set **secrets only**:
- `HF_API_KEY` - Your HuggingFace API key ([Get one here](https://huggingface.co/settings/tokens))
- `REPLICATE_API_TOKEN` - Your Replicate API token ([Get one here](https://replicate.com/account/api-tokens)) - **Optional**
- `SECRET_KEY` - **CRITICAL**: JWT signing key (minimum 32 characters)
  - Generate: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
  - **NEVER use default in production**
- `AUTH_USERNAME` - Admin username (default: `admin`)
- `AUTH_PASSWORD` - Admin password (**change from default!**)
- `APP_ENV` - Environment selection: `production`, `development`, `staging` (default: `production`)

**Step 2b: Set up configuration (`config/*.json` files)**

⚠️ **IMPORTANT**: The configuration system requires TWO files:
1. `default.json` - Base configuration with all defaults (**REQUIRED**)
2. `{environment}.json` - Environment-specific overrides (optional but recommended)

```bash
# REQUIRED: Copy the base default configuration
# This file is committed to git and contains all default settings
cp backend/config/default.json /path/to/your/config/default.json

# RECOMMENDED: Copy and customize environment-specific config
# For production:
cp backend/config/production.json.example backend/config/production.json

# OR for development:
cp backend/config/development.json.example backend/config/development.json
```

**For Docker deployments with volume mounts:**
```bash
# Both files must be in the mounted config directory
# Example: -v /opt/retro/config:/app/config
sudo cp backend/config/default.json /opt/retro/config/
sudo cp backend/config/production.json.example /opt/retro/config/production.json
```

Edit `backend/config/production.json` (or `development.json`) for your environment:
- `application` - App name, version, debug mode, log level
- `server` - Host, port, workers
- `cors.origins` - **IMPORTANT**: Allowed CORS origins (JSON array, human-readable!)
  - Example: `["https://yourdomain.com", "https://www.yourdomain.com"]`
- `models` - **NEW FORMAT**: Multi-line JSON for easy editing!
  - No more single-line escaping issues
  - Each model needs: `id`, `name`, `model`, `provider`, `category`, `description`
- `database`, `file_storage`, `session`, `processing` - All other settings

**Configuration Loading Priority:**

The system loads configuration in this order (each level overrides the previous):
1. `config/default.json` - **REQUIRED** base configuration (**MUST EXIST**)
2. `config/{APP_ENV}.json` - Environment-specific overrides (e.g., `production.json`)
3. `config/local.json` - **MODEL CONFIGURATIONS ONLY** (optional, gitignored)
4. Environment variables (`.env`) - **HIGHEST PRIORITY** overrides

**⚠️ Important - `local.json` behavior:**
- `local.json` is **exclusively for model configuration overrides**
- Only the `models` array from `local.json` is processed
- **All other configuration keys are ignored** (application, server, database, cors, etc.)
- For non-model overrides, use environment-specific files or environment variables
- See [docs/configuration.md](docs/configuration.md#localjson-configuration) for details

**What happens if `default.json` is missing?**
- The system will fall back to deprecated `.env`-only mode
- You'll only get 1 hardcoded model instead of your full model configuration
- Logs will show: `⚠ Using .env-only configuration (DEPRECATED)`

**Troubleshooting:**
```bash
# Check if default.json exists in your config directory
ls -la /opt/retro/config/  # For Docker volume mounts
ls -la backend/config/     # For local development

# You should see both files:
# - default.json (required)
# - production.json (or development.json)

# Check startup logs to verify config loaded correctly
docker logs retro-backend 2>&1 | grep "Configuration source"
# Should show: "Configuration source: JSON config files"
# If it shows: "Configuration source: .env only (DEPRECATED)" - default.json is missing!
```

**Validate your configuration:**
```bash
cd backend
python scripts/validate_config.py --env production
```

**Migration from old .env format:**
If you have an existing `.env` with `MODELS_CONFIG`, migrate it:
```bash
cd backend
python scripts/migrate_env_to_config.py --env-file .env --output config/production.json --update-env
```

**For detailed configuration reference:**
- See [backend/config/README.md](backend/config/README.md)
- Generate docs: `python backend/scripts/generate_config_docs.py`

**Frontend:**
```bash
cp frontend/.env.example frontend/.env
```

(Default values should work for Docker setup)

### 3. Optional: Enable IP Geolocation

The application can display approximate geographic locations for user sessions based on IP addresses. This feature is **optional** and requires the GeoLite2-City database from MaxMind.

**Quick Setup:**
```bash
# Download GeoLite2-City database (requires free MaxMind account)
# See detailed instructions: docs/GEOIP_SETUP.md

# For Docker: Place the database file and uncomment volume mount in docker-compose.yml
# - /path/to/GeoLite2-City.mmdb:/app/GeoLite2-City.mmdb:ro
```

**Without this setup:** Sessions will show "📍Unknown location" but all other features work normally.

**For detailed instructions:** See [docs/GEOIP_SETUP.md](docs/GEOIP_SETUP.md)

### 4. Build and run with Docker Compose

**IMPORTANT:** The application now requires an external reverse proxy. The docker-compose.yml no longer includes nginx. You must configure your own reverse proxy (nginx, Apache, Traefik, Caddy, etc.) to route requests.

**Production mode:**
```bash
docker-compose up --build
```

This starts:
- Backend on port 8000 (not exposed to host - access via proxy)
- Frontend on port 3000 (exposed to host)

**Development mode (with hot reload):**
```bash
docker-compose -f docker-compose.dev.yml up --build
```

This starts:
- Backend-dev on port 8000 (exposed for direct access)
- Frontend-dev on port 3000 (Vite dev server with hot reload)

**Alternative: Individual Docker run commands**

See [docs/implementation.md](docs/implementation.md#individual-docker-run-commands) for manual Docker run commands.

### 5. Configure your external reverse proxy

You must set up a reverse proxy to route requests. Example nginx configuration:

```nginx
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name localhost;

    location /api {
        proxy_pass http://backend;
    }

    location /uploads {
        proxy_pass http://backend;
    }

    location /processed {
        proxy_pass http://backend;
    }

    location /health {
        proxy_pass http://backend/health;
    }

    location / {
        proxy_pass http://frontend;
    }
}
```

See [docs/implementation.md](docs/implementation.md#external-reverse-proxy-configuration) for complete nginx, Apache, Traefik, and Caddy examples.

### 6. Access the application

Once your reverse proxy is configured:

- **Frontend**: http://localhost (via your proxy)
- **Backend API**: http://localhost/api (via your proxy)
- **API Documentation**: http://localhost/api/docs (via your proxy)
- **Health Check**: http://localhost/health (via your proxy)

For direct container access (without proxy):
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000 (if exposed)

> **Note:** For production deployment with HTTPS, SSL/TLS configuration, multiple proxy examples, and advanced setup, see [docs/implementation.md](docs/implementation.md).

## ⚠️ Breaking Changes & Migration

### Custom Model Parameters UI (v1.9.0+)

**What Changed:**
The application now includes a Custom Model Parameters UI feature that allows users to customize model parameters through the web interface. This feature requires model configurations to include `ui_hidden` flags on parameters.

**Who Is Affected:**
- Users upgrading from versions prior to v1.9.0
- Users with Replicate models in their configuration files
- Production deployments with custom model configurations

**Migration Required:**
If you have Replicate models configured in your `backend/config/*.json` files, you **MUST** run the migration script before upgrading:

```bash
# Navigate to project root
cd photo-restoration-webpage

# Run migration script (interactive mode)
python backend/scripts/migrate_ui_parameters.py --config backend/config/production.json --interactive

# Or use automated migration (auto-hide internal parameters)
python backend/scripts/migrate_ui_parameters.py --config backend/config/production.json

# For dry-run (see what would change without modifying files)
python backend/scripts/migrate_ui_parameters.py --config backend/config/production.json --dry-run
```

**Migration Script Options:**
- `--config PATH` - Config file to migrate (default: backend/config/production.json)
- `--interactive` - Ask questions to configure custom UI controls (recommended for production)
- `--no-backup` - Skip creating backup file (not recommended)
- `--output PATH` - Output file path (default: creates backend/config/local.json)
- `--dry-run` - Show what would change without modifying files

**What The Migration Does:**
1. **Scans** your model configurations for Replicate models with parameters
2. **Adds** `ui_hidden` flags to all parameters:
   - `ui_hidden: true` for internal params (seed, safety_tolerance, webhook, etc.)
   - `ui_hidden: false` for user-visible params (output_format, quality, etc.)
3. **Optionally** creates custom UI controls (sliders, radio buttons, dropdowns)
4. **Creates** a backup of your original config file

**After Migration:**
- Your application will show parameter controls for visible parameters
- Users can customize model behavior through the UI
- Hidden parameters remain accessible via API but not shown in the UI
- Auto-detection provides sensible defaults (sliders for ranges, radio for 2-3 options, etc.)

**Warning Indicators:**
If migration is needed, you will see:
1. **Backend startup warning** - Console logs showing models that need migration
2. **Frontend banner** - Yellow warning banner on the homepage with migration instructions
3. **API endpoint** - `/api/v1/models/migration/status` returns migration status

**Example Migration Output:**
```
🔄 Loading configuration from: backend/config/production.json
📋 Found 1 models

************************************************************
Model: Replicate Photo Restore (replicate-restore)
Parameters: 3
************************************************************

⚠️  Parameter 'output_format' missing ui_hidden flag
   → Auto-visible (will use auto-detection)

=============================================================
MIGRATION SUMMARY
=============================================================
  - replicate-restore: Added ui_hidden to 'output_format'

Total models migrated: 1/1

💾 Save changes to backend/config/local.json? [Y/n]:
```

**Reference Documentation:**
- Full implementation details: [docs/chats/custom-model-parameters-ui-implementation-2025-12-28.md](docs/chats/custom-model-parameters-ui-implementation-2025-12-28.md)
- Example configurations: [backend/config/local.json.example](backend/config/local.json.example)
- Architecture details: [ARCHITECTURE.md](ARCHITECTURE.md) - Search for "Custom Model Parameters"

**For Help:**
- Run migration in dry-run mode first: `--dry-run`
- Check example configs: `backend/config/*.json.example`
- Review logs during startup for migration warnings
- See migration status: `curl http://localhost:8000/api/v1/models/migration/status`

---

## Local Development (Without Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env

# Run development server
npm run dev
```

Frontend will be available at http://localhost:3000

## Project Structure

```
photo-restoration-webpage/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/v1/            # API routes and schemas
│   │   ├── core/              # Configuration and security
│   │   ├── services/          # Business logic
│   │   ├── db/                # Database models
│   │   ├── utils/             # Utilities
│   │   └── main.py            # FastAPI app entry point
│   ├── tests/                 # Backend tests
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                   # React + TypeScript application
│   ├── src/
│   │   ├── app/               # App shell and routing
│   │   ├── features/          # Feature modules
│   │   ├── components/        # Shared UI components
│   │   ├── services/          # API clients and services
│   │   ├── hooks/             # Custom React hooks
│   │   ├── types/             # TypeScript types
│   │   ├── styles/            # Global styles and themes
│   │   └── config/            # Frontend configuration
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── .env.example
│
├── docs/                       # Documentation
│   └── chats/                 # Technical discussions
│
├── tmp/                        # Brand assets and design
│   ├── 02. logotype/          # sqowe logos
│   ├── Brand-Guidelines.pdf
│   └── AI_WEB_DESIGN_SQOWE.md
│
├── docker-compose.yml          # Production compose
├── docker-compose.dev.yml      # Development compose
├── ROADMAP.md                  # Development roadmap
└── README.md                   # This file
```

## Configuration

### Backend Environment Variables

See [`backend/.env.example`](backend/.env.example) for all available options.

Key variables:
- `HF_API_KEY` - HuggingFace API key (required)
- `SECRET_KEY` - **JWT secret key (REQUIRED)** - Cryptographic key for signing authentication tokens
  - **Purpose**: Signs and verifies JWT tokens for user authentication
  - **Security**: If compromised, attackers can bypass authentication entirely
  - **Minimum**: 32 characters (recommended: 64+ characters)
  - **Generation**: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
  - **Important**: NEVER use default value in production, must be unique per environment
  - **Note**: Changing this key will log out all users
  - See [docs/implementation.md](docs/implementation.md#understanding-secret_key) for detailed explanation
- `AUTH_USERNAME` / `AUTH_PASSWORD` - Admin credentials (change from defaults!)
- `CORS_ORIGINS` - **IMPORTANT**: Must be in JSON array format
  - Example: `CORS_ORIGINS=["http://localhost:3000","http://localhost"]`
  - Production: `CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]`
- `ALLOWED_EXTENSIONS` - Allowed file extensions (JSON array format)
  - Default: `ALLOWED_EXTENSIONS=[".jpg",".jpeg",".png"]`
- `MODELS_CONFIG` - JSON configuration of available AI models
- `DATABASE_URL` - SQLite database path
- `MAX_UPLOAD_SIZE` - Maximum file upload size (default: 10MB)

### Frontend Environment Variables

See [`frontend/.env.example`](frontend/.env.example) for all available options.

Key variables:
- `VITE_API_BASE_URL` - API base URL (default: `/api/v1`)

### Available AI Models (MVP)

Configured in `MODELS_CONFIG` environment variable:

1. **Swin2SR 2x Upscale** - Fast 2x upscaling
2. **Swin2SR 4x Upscale** - Fast 4x upscaling
3. **Qwen Image Enhance** - AI-powered enhancement and restoration

You can add more models by editing the `MODELS_CONFIG` JSON in `.env`.

## Development Guidelines

This project follows strict coding standards:

- **Backend**: [AI.md](AI.md), [AI_FastAPI.md](AI_FastAPI.md), [AI_SQLite.md](AI_SQLite.md)
- **Frontend**: [AI_FRONTEND.md](AI_FRONTEND.md), [AI_WEB_COMMON.md](AI_WEB_COMMON.md)
- **Design**: [tmp/AI_WEB_DESIGN_SQOWE.md](tmp/AI_WEB_DESIGN_SQOWE.md) (sqowe brand)
- **General**: [CLAUDE.md](CLAUDE.md) - Always propose before implementing

Key principles:
- Type hints (Python) and TypeScript (strict mode)
- Files ≤ 800 lines
- Comprehensive error handling
- Security-first approach
- Material-inspired UI with sqowe branding

## Testing

**Backend: 218 tests ✅**
```bash
cd backend
source venv/bin/activate
pytest

# With coverage
pytest --cov=app --cov-report=html
```

Test Summary:
- Config tests: 21 tests ✅
- Health & startup tests: 21 tests ✅
- Auth tests: 24 tests ✅
- Security tests: 29 tests ✅
- Models API tests: 17 tests ✅
- HF Inference service tests: 23 tests ✅
- Image utilities tests: 37 tests ✅
- Database model tests: 11 tests ✅
- Database setup tests: 19 tests ✅
- Session manager tests: 29 tests ✅

**Frontend: 224 tests ✅**
```bash
cd frontend
npm test

# With coverage
npm run test:coverage
```

Test Summary:
- Auth tests: 55 tests ✅ (from phases 1.1-1.2)
- Restoration feature tests: 40 tests ✅ (from phase 1.7)
- History feature tests: 20 tests ✅ (from phase 1.7)
- Shared component tests: 82 tests ✅ (phase 1.8)
- Layout tests: 12 tests ✅ (phase 1.8)
- Accessibility tests: 15 tests ✅ (phase 1.8)

## Docker Commands

**Build and start:**
```bash
docker-compose up --build
```

**Start in background:**
```bash
docker-compose up -d
```

**Stop:**
```bash
docker-compose down
```

**View logs:**
```bash
docker-compose logs -f
```

**Rebuild specific service:**
```bash
docker-compose up --build backend
```

**Clean everything (including volumes):**
```bash
docker-compose down -v
```

**Run utility scripts inside container:**
```bash
# Example: Run config migration script
docker exec photo-restoration-backend python /app/scripts/migrate_config.py /app/config/default.json

# Example: Validate configuration
docker exec photo-restoration-backend python /app/scripts/validate_config.py --env production

# Example: Backup configuration
docker exec photo-restoration-backend python /app/scripts/backup_config.py /app/config/default.json

# Example: Restore configuration from backup
docker exec photo-restoration-backend python /app/scripts/restore_config.py /app/config/backups/default_20250101_120000.json

# Available scripts in /app/scripts/:
# - migrate_config.py - Migrate configuration files between versions
# - backup_config.py - Backup configuration files
# - restore_config.py - Restore configuration from backups
# - validate_config.py - Validate configuration files
# - generate_config_docs.py - Generate configuration documentation
# - migrate_ui_parameters.py - Migrate UI parameter configurations
# - migrate_env_to_config.py - Migrate from .env to JSON config
# - fetch_replicate_schema.py - Fetch schema from Replicate API
# - format_models_config.py - Format model configuration
```

> **Advanced Usage:** For individual Docker run commands, custom nginx configurations, SSL setup, and production deployment guides, see [docs/implementation.md](docs/implementation.md).

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost/api/docs
- ReDoc: http://localhost/api/redoc

📖 **Detailed API Documentation:** For comprehensive API documentation including Phase 2.4 endpoints (User Management, Admin Panel), see [docs/API_PHASE_2.4.md](docs/API_PHASE_2.4.md).

### Available Endpoints

**Authentication:**
- `POST /api/v1/auth/login` - User login, returns JWT token
- `POST /api/v1/auth/validate` - Validate token
- `GET /api/v1/auth/me` - Get current user info

**User Management (Phase 2.4):**
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me/password` - Change password
- `GET /api/v1/users/me/sessions` - List active sessions
- `DELETE /api/v1/users/me/sessions/{id}` - Remote logout

**Admin Endpoints (Phase 2.4, Admin role required):**
- `GET /api/v1/admin/users` - List users with pagination and filtering
- `POST /api/v1/admin/users` - Create new user
- `GET /api/v1/admin/users/{user_id}` - Get user details
- `PUT /api/v1/admin/users/{user_id}` - Update user
- `DELETE /api/v1/admin/users/{user_id}` - Delete user
- `PUT /api/v1/admin/users/{user_id}/reset-password` - Reset user password

**Models:**
- `GET /api/v1/models` - List available AI models
- `GET /api/v1/models/{id}` - Get model details

**Image Restoration:**
- `POST /api/v1/restore` - Upload and process image
- `GET /api/v1/restore/history` - Get session history (paginated, cross-session)
- `GET /api/v1/restore/{image_id}` - Get image details
- `GET /api/v1/restore/{image_id}/download` - Download processed image
- `DELETE /api/v1/restore/{image_id}` - Delete image and files

**Static Files:**
- `GET /uploads/{path}` - Serve uploaded images
- `GET /processed/{path}` - Serve processed images

**Health:**
- `GET /health` - API health check

## Troubleshooting

### Backend won't start
- Check that `HF_API_KEY` is set in `backend/.env`
- Ensure `SECRET_KEY` is at least 32 characters
- Check logs: `docker-compose logs backend`

### Frontend can't connect to backend
- Verify your external reverse proxy is running and configured correctly
- Check proxy logs for routing errors
- Ensure `VITE_API_BASE_URL=/api/v1` in `frontend/.env` (for proxy-based routing)
- Verify frontend and backend containers are running: `docker-compose ps`
- Test direct access: `curl http://localhost:3000/` and `curl http://localhost:8000/health`

### Database errors
- SQLite WAL files may cause issues. Stop containers and delete `data/*.db-*` files
- Check permissions on `data/` directory

### Port conflicts
- Default container ports: 8000 (backend), 3000 (frontend)
- Change ports in `docker-compose.yml` if needed
- Your external proxy will use port 80/443 for HTTP/HTTPS

> **Detailed Troubleshooting:** See [docs/implementation.md](docs/implementation.md#troubleshooting) for comprehensive troubleshooting guide, nginx configuration examples, SSL setup, and production deployment instructions.

## Contributing

See [ROADMAP.md](ROADMAP.md) for planned features and development phases.

Before contributing:
1. Read coding guidelines in `AI*.md` files
2. Follow the sqowe brand design system
3. Write tests for new features
4. Ensure code passes linting

## License

[Add your license here]

## Acknowledgments

- sqowe brand guidelines and assets
- HuggingFace for AI model inference
- FastAPI, React, and all open-source dependencies

---

**Current Phase:** Phase 1 - MVP (In Progress)

**Completed Phases:**
- Phase 1.1 - Infrastructure ✅
- Phase 1.2 - Authentication ✅
- Phase 1.3 - AI Models Configuration ✅
- Phase 1.4 - HuggingFace Integration ✅
- Phase 1.5 - Session Management & History ✅
- Phase 1.6 - Image Restoration API ✅
- Phase 1.7 - Frontend Core Features ✅
- Phase 1.8 - UI/UX Implementation ✅

**Next Steps:** Phase 1.9 - Testing & Quality Assurance, Phase 1.10 - Documentation & Deployment

**Test Coverage:**
- Backend: 279 tests passing ✅ (218 from phases 1.1-1.5 + 61 from phase 1.6)
- Frontend: 224 tests passing ✅ (55 auth + 60 restoration/history + 109 UI/accessibility from phase 1.8)
- Total: 503 tests ✅

See [ROADMAP.md](ROADMAP.md) for detailed implementation plan.
