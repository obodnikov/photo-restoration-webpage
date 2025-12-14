# Photo Restoration Webpage

AI-powered web application for restoring old scanned photos using HuggingFace models. Built with FastAPI backend, React frontend, and deployed with Docker and nginx reverse proxy.

## Project Status

**Version:** 0.2.0
**Current Phase:** Phase 1 - MVP (In Progress)
**Completed:** Phase 1.1 ✅ | Phase 1.2 ✅

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

### Phase 1.3+ - In Progress
- ⏳ AI Models configuration
- ⏳ HuggingFace Inference integration
- ⏳ Image upload and processing
- ⏳ Before/After comparison
- ⏳ Session-based history

### Planned Features
- **Phase 2**: Model pipelines, batch processing, additional models
- **Phase 3**: OwnCloud integration, multi-user support, video frame restoration
- **Phase 4**: Production polish, monitoring, security hardening

See [ROADMAP.md](ROADMAP.md) for detailed development plan.

## Tech Stack

**Backend:**
- Python 3.11+
- FastAPI (async REST API)
- SQLAlchemy (async ORM)
- SQLite (database)
- HuggingFace Inference API
- JWT authentication

**Frontend:**
- React 18
- TypeScript (strict mode)
- Vite (build tool)
- Zustand (state management)
- sqowe brand design system

**Deployment:**
- Docker & Docker Compose
- nginx reverse proxy
- Multi-stage builds

## Prerequisites

- Docker & Docker Compose
- HuggingFace API key ([Get one here](https://huggingface.co/settings/tokens))

**For local development:**
- Python 3.11+
- Node.js 20+
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
- `SECRET_KEY` - **CRITICAL**: Cryptographic secret for JWT token signing (minimum 32 characters)
  - Generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
  - **NEVER use the example value in production**
  - Must be unique and random for security
- `AUTH_USERNAME` - Admin username (default: `admin`)
- `AUTH_PASSWORD` - Admin password (**change from default!**)

**Frontend:**
```bash
cp frontend/.env.example frontend/.env
```

(Default values should work for Docker setup)

### 3. Build and run with Docker Compose

**Production mode:**
```bash
docker-compose up --build
```

**Development mode (with hot reload):**
```bash
docker-compose -f docker-compose.dev.yml up --build
```

**Alternative: Individual Docker run commands**

See [docs/implementation.md](docs/implementation.md#individual-docker-run-commands) for manual Docker run commands.

### 4. Access the application

- **Frontend**: http://localhost
- **Backend API**: http://localhost/api
- **API Documentation**: http://localhost/api/docs
- **Health Check**: http://localhost/health

> **Note:** For production deployment with HTTPS, nginx configuration examples, and advanced setup, see [docs/implementation.md](docs/implementation.md).

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
├── nginx/                      # nginx reverse proxy
│   ├── nginx.conf
│   └── Dockerfile
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

**Backend:**
```bash
cd backend
pytest
```

**Frontend:**
```bash
cd frontend
npm test
```

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

## Troubleshooting

### Backend won't start
- Check that `HF_API_KEY` is set in `backend/.env`
- Ensure `SECRET_KEY` is at least 32 characters
- Check logs: `docker-compose logs backend`

### Frontend can't connect to backend
- Verify nginx is running: `docker-compose ps`
- Check nginx logs: `docker-compose logs nginx`
- Ensure `VITE_API_BASE_URL=/api/v1` in `frontend/.env`

### Database errors
- SQLite WAL files may cause issues. Stop containers and delete `data/*.db-*` files
- Check permissions on `data/` directory

### Port conflicts
- Default ports: 80 (nginx), 8000 (backend), 3000 (frontend dev)
- Change ports in `docker-compose.yml` if needed

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

**Current Phase:** Phase 1.1 - Project Setup ✅ Complete

**Next Steps:** Phase 1.2 - Authentication System

See [ROADMAP.md](ROADMAP.md) for detailed implementation plan.
