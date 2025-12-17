# Photo Restoration Webpage

AI-powered web application for restoring old scanned photos using multiple AI providers (HuggingFace, Replicate). Built with FastAPI backend, React frontend, and deployed with Docker and nginx reverse proxy.

## Project Status

**Version:** 0.8.0
**Current Phase:** Phase 1 - MVP (In Progress)
**Completed:** Phase 1.1 ✅ | Phase 1.2 ✅ | Phase 1.3 ✅ | Phase 1.4 ✅ | Phase 1.5 ✅ | Phase 1.6 ✅ | Phase 1.7 ✅ | Phase 1.8 ✅

## Features

### Phase 1.1 - Infrastructure ✅ COMPLETE
- ✅ FastAPI backend with async support
- ✅ React + TypeScript frontend with Vite
- ✅ Docker deployment with nginx reverse proxy
- ✅ sqowe brand design system
- ✅ Health check endpoints

### Phase 1.2 - Authentication ✅ COMPLETE
- ✅ JWT token-based authentication
- ✅ Login system with sqowe branding
- ✅ Protected routes
- ✅ Auth state management (Zustand)
- ✅ Token persistence in localStorage
- ✅ Auto-logout on token expiration
- ✅ "Remember Me" functionality (7 days)

### Phase 1.3 - AI Models Configuration ✅ COMPLETE
- ✅ Models configuration API (`GET /api/v1/models`)
- ✅ Individual model details (`GET /api/v1/models/{id}`)
- ✅ Configurable authentication (MODELS_REQUIRE_AUTH)
- ✅ Smart caching for performance
- ✅ Model schema with tags and version support
- ✅ 17 comprehensive tests

### Phase 1.4 - HuggingFace Integration ✅ COMPLETE
- ✅ HFInferenceService for model processing
- ✅ Image validation and conversion utilities
- ✅ Comprehensive error handling (rate limits, timeouts, server errors)
- ✅ Custom exception classes (HFRateLimitError, HFTimeoutError, etc.)
- ✅ Model status checking
- ✅ Test data with mock HF API
- ✅ 60 comprehensive tests (23 HF service + 37 image utilities)

### Phase 1.5 - Session Management & History ✅ COMPLETE
- ✅ SQLAlchemy async database models (Session, ProcessedImage)
- ✅ SQLite database with WAL mode and async support
- ✅ SessionManager service (create, retrieve, cleanup)
- ✅ Session-based file storage (uploads, processed images)
- ✅ Automated session cleanup (24-hour inactivity)
- ✅ Session history with pagination
- ✅ Cascade delete (session + files)
- ✅ 59 comprehensive tests (11 models + 19 database + 29 session manager)

### Phase 1.6 - Image Restoration API ✅ COMPLETE
- ✅ Complete restoration workflow (`POST /api/v1/restore`)
  - ✅ Image validation (format, size, content)
  - ✅ HuggingFace model integration
  - ✅ File storage with UUID prefix + original filename
  - ✅ Database metadata storage
  - ✅ Concurrent upload limiting per session (configurable)
- ✅ History endpoints
  - ✅ `GET /api/v1/restore/history` - paginated session history
  - ✅ `GET /api/v1/restore/{image_id}` - get image details
  - ✅ `GET /api/v1/restore/{image_id}/download` - download processed image
  - ✅ `DELETE /api/v1/restore/{image_id}` - delete image and files
- ✅ Background cleanup service
  - ✅ APScheduler integration
  - ✅ Periodic session cleanup (configurable interval)
  - ✅ Run on startup + scheduled execution
- ✅ Comprehensive error handling
  - ✅ HF API errors mapped to HTTP codes (429→503, timeout→504, errors→502)
  - ✅ User-friendly error messages
- ✅ Session creation on login (new session per login)
- ✅ User isolation (cannot access other sessions' images)
- ✅ 61 comprehensive tests (11 validation + 13 models + 18 integration + 8 cleanup + 11 static)

### Phase 1.7 - Frontend Core Features ✅ COMPLETE
- ✅ Complete image restoration workflow with drag & drop upload
- ✅ Model selection with descriptions from API
- ✅ Real-time processing status with progress tracking
- ✅ Image comparison viewer with 3 modes (Original, Restored, Compare)
- ✅ Full restoration history with pagination
- ✅ Download and delete functionality
- ✅ Layout with header/footer (sqowe branding)
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Shared UI components (Button, Card, Loader, ErrorMessage)
- ✅ 115 comprehensive frontend tests (60 new tests for Phase 1.7)

### Phase 1.8 - UI/UX Implementation ✅ COMPLETE
- ✅ Input component with form validation and error handling
- ✅ Modal component with full accessibility support
- ✅ Mobile hamburger navigation menu
- ✅ Enhanced responsive design (mobile < 768px, tablet 768-1023px, desktop 1024px+)
- ✅ Touch-friendly targets (44x44px minimum)
- ✅ Form styles with focus states and validation
- ✅ 109+ comprehensive tests:
  - ✅ 82 component tests (Button, Card, Input, TextArea, Modal, Loader, ErrorMessage)
  - ✅ 12 layout tests (header, navigation, mobile menu, footer)
  - ✅ 15+ accessibility tests (ARIA, keyboard, contrast with axe-core)
- ✅ Accessibility compliance (WCAG AA standards)

### Phase 1.9+ - In Progress
- ⏳ Complete testing infrastructure and QA
- ⏳ Documentation and deployment

### Planned Features
- **Phase 2**: Model pipelines, batch processing, additional models
- **Phase 3**: OwnCloud integration, multi-user support, video frame restoration
- **Phase 4**: Production polish, monitoring, security hardening

See [ROADMAP.md](ROADMAP.md) for detailed development plan.

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

### 2. Configure environment variables

**Backend:**
```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set:
- `HF_API_KEY` - Your HuggingFace API key ([Get one here](https://huggingface.co/settings/tokens))
- `REPLICATE_API_TOKEN` - Your Replicate API token ([Get one here](https://replicate.com/account/api-tokens)) - **Optional**, only needed if using Replicate models
- `SECRET_KEY` - **CRITICAL**: Cryptographic secret for JWT token signing (minimum 32 characters)
  - Generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
  - **NEVER use the example value in production**
  - Must be unique and random for security
- `AUTH_USERNAME` - Admin username (default: `admin`)
- `AUTH_PASSWORD` - Admin password (**change from default!**)
- `CORS_ORIGINS` - **IMPORTANT**: Must be in JSON array format
  - Example: `CORS_ORIGINS=["http://localhost:3000","http://localhost"]`
  - For production: `CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]`
- `MODELS_CONFIG` - Configure which AI models to use (supports both HuggingFace and Replicate providers)
  - **IMPORTANT**: Must be on a **SINGLE LINE** for Docker compatibility (no line breaks)
  - The `.env.example` file provides the correct single-line format
  - See commented multi-line format in `.env.example` for reference only
  - Each model must specify a `provider` field: `"huggingface"` or `"replicate"`

**New in Phase 1.6:**
- `SESSION_CLEANUP_HOURS` - How old sessions to delete (default: 24)
- `SESSION_CLEANUP_INTERVAL_HOURS` - How often to run cleanup task (default: 6)
- `MAX_CONCURRENT_UPLOADS_PER_SESSION` - Concurrent processing limit per session (default: 3)

**Frontend:**
```bash
cp frontend/.env.example frontend/.env
```

(Default values should work for Docker setup)

### 3. Build and run with Docker Compose

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

### 4. Configure your external reverse proxy

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

### 5. Access the application

Once your reverse proxy is configured:

- **Frontend**: http://localhost (via your proxy)
- **Backend API**: http://localhost/api (via your proxy)
- **API Documentation**: http://localhost/api/docs (via your proxy)
- **Health Check**: http://localhost/health (via your proxy)

For direct container access (without proxy):
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000 (if exposed)

> **Note:** For production deployment with HTTPS, SSL/TLS configuration, multiple proxy examples, and advanced setup, see [docs/implementation.md](docs/implementation.md).

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

> **Advanced Usage:** For individual Docker run commands, custom nginx configurations, SSL setup, and production deployment guides, see [docs/implementation.md](docs/implementation.md).

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost/api/docs
- ReDoc: http://localhost/api/redoc

### Available Endpoints

**Authentication:**
- `POST /api/v1/auth/login` - User login, returns JWT token
- `POST /api/v1/auth/validate` - Validate token
- `GET /api/v1/auth/me` - Get current user info

**Models:**
- `GET /api/v1/models` - List available AI models
- `GET /api/v1/models/{id}` - Get model details

**Image Restoration:**
- `POST /api/v1/restore` - Upload and process image
- `GET /api/v1/restore/history` - Get session history (paginated)
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
