# Architecture Overview

**Version:** 1.0.0
**Status:** Production-Ready (Phase 1 Complete, Phase 2.4 Complete)
**Last Updated:** 2025-12-28

---

## 1. Purpose of This Document

This document provides the architectural foundation for AI-assisted development.

**What this document DOES:**
- Define system structure and component boundaries
- Explain key architectural decisions and their rationale
- Map stability zones to help AI avoid breaking stable code
- Describe runtime model and data flows
- Point to authoritative sources for detailed information

**What this document DOES NOT DO:**
- Duplicate coding rules (see [Section 8: AI Coding Rules](#8-ai-coding-rules-and-behavioral-contracts))
- Provide implementation details (see `docs/implementation.md`)
- Replace existing documentation (see `README.md`, `ROADMAP.md`)

---

## 2. High-Level System Overview

Photo Restoration Webpage is an AI-powered web application for restoring old photos using multiple AI providers (HuggingFace, Replicate).

**Key Characteristics:**
- **Type:** Long-living personal PET project
- **Evolution:** Incremental phased development (currently Phase 2.4)
- **Stack:** FastAPI (async Python 3.13) + React 18 + TypeScript (strict)
- **Deployment:** Docker Compose + user-provided external reverse proxy
- **Database:** SQLite (MVP) with planned PostgreSQL migration
- **Authentication:** JWT with database-backed multi-session support
- **AI Providers:** HuggingFace Inference API + Replicate API

**Architecture Pattern:**
```
External Proxy (user-provided)
    ↓
┌─────────────────────┬─────────────────────┐
│   Frontend          │   Backend           │
│   (serve + React)   │   (FastAPI)         │
│   Port 3000         │   Port 8000         │
│   Static files only │   REST API + AI     │
└─────────────────────┴──────────┬──────────┘
                                 ↓
                    ┌────────────────────────┐
                    │ SQLite DB + File Store │
                    │ /data/                 │
                    └────────────────────────┘
```

---

## 3. Repository Structure

```
photo-restoration-webpage/
├── backend/                    # FastAPI async application
│   ├── app/
│   │   ├── api/v1/            # Routes: auth, models, restore, admin, users
│   │   ├── core/              # Config, security, deps, providers
│   │   ├── db/                # SQLAlchemy models (User, Session, RestorationImage)
│   │   ├── services/          # HuggingFace, Replicate, session manager
│   │   └── utils/             # Image processing, file handling
│   ├── alembic/               # Database migrations (Alembic)
│   ├── config/                # JSON config files (default, production, local)
│   ├── tests/                 # 279 tests (99% coverage)
│   └── requirements.txt
│
├── frontend/                   # Vite + React + TypeScript
│   ├── src/
│   │   ├── app/               # App shell, routing, layout
│   │   ├── features/          # Auth, restoration, history, admin, profile
│   │   ├── components/        # Shared UI (sqowe brand, Material-inspired)
│   │   ├── services/          # API client, auth store (Zustand)
│   │   └── styles/            # CSS Modules + design tokens
│   ├── __tests__/             # 224 tests (Vitest + RTL)
│   └── package.json
│
├── docs/                       # Documentation
│   ├── chats/                 # 45+ previous implementation conversations
│   ├── implementation.md      # Deployment, proxy config, troubleshooting
│   ├── configuration.md       # Auto-generated config reference
│   └── [phase-specific docs]
│
├── tmp/                        # Brand assets, temporary files
│   ├── 02. logotype/          # sqowe logos (SVG, PNG)
│   ├── Brand-Guidelines.pdf   # Official sqowe brand guidelines
│   └── AI_WEB_DESIGN_SQOWE.md # sqowe design rules for AI
│
├── AI*.md                      # 9 AI coding rule files (see Section 8)
├── CLAUDE.md                   # Project workflow (propose before implementing)
├── README.md                   # User-facing documentation
├── ROADMAP.md                  # Development phases (1.1-2.4 complete)
├── TECHNICAL_DEBTS.md         # Known issues and future improvements
├── docker-compose.yml         # Production deployment
└── docker-compose.dev.yml     # Development with hot reload
```

**Critical Paths:**
- Backend entry: `backend/app/main.py`
- Frontend entry: `frontend/src/main.tsx`
- Config: `backend/config/default.json` (REQUIRED base)
- Tests: `backend/tests/`, `frontend/src/__tests__/`

---

## 4. Core Components

### 4.1 Frontend (Stable ✅)

**Tech:** Vite + React 18 + TypeScript (strict) + Zustand + CSS Modules

**Key Components:**
- **App Shell** (`src/app/`) - Routing, layout, auth guards
- **Features** (`src/features/`) - Feature-oriented modules:
  - `auth/` - Login, JWT management
  - `restoration/` - Image upload, AI processing, before/after viewer
  - `history/` - Paginated image history
  - `admin/` - User management (admin-only)
  - `profile/` - User profile, password change, session management
- **Shared Components** (`src/components/`) - sqowe-branded UI components
- **Auth Store** (`src/services/authStore.ts`) - Global Zustand store for auth state

**Routing:**
- `/` → Login (if not authenticated)
- `/restoration` → Photo restoration (protected)
- `/history` → History (protected)
- `/admin` → Admin panel (admin-only)
- `/profile` → User profile (protected)

### 4.2 Backend (Stable ✅)

**Tech:** FastAPI + SQLAlchemy (async) + SQLite + JWT

**Key Components:**
- **API Routes** (`app/api/v1/routes/`) - RESTful endpoints
- **Authentication** (`app/core/security.py`) - JWT + bcrypt + multi-session
- **Configuration** (`app/core/config.py`) - Hierarchical JSON loader
- **AI Providers** (`app/services/`) - HuggingFace + Replicate async clients
- **Database** (`app/db/`) - SQLAlchemy models (User, Session, RestorationImage)
- **Session Manager** (`app/services/session_manager.py`) - Background cleanup

**API Endpoints:**
- `/api/v1/auth/*` - Login, validate, me
- `/api/v1/models` - List AI models
- `/api/v1/restore` - Upload, process, history
- `/api/v1/admin/*` - User CRUD (admin-only)
- `/api/v1/users/me/*` - Profile, sessions, password

### 4.3 External Integrations

**AI Providers (External APIs):**
- **HuggingFace Inference API** - Upscaling, enhancement (HF_API_KEY)
- **Replicate API** - Advanced restoration (REPLICATE_API_TOKEN, optional)

**Reverse Proxy (User-Provided):**
- **Required:** nginx, Apache, Traefik, Caddy, or equivalent
- **Purpose:** Route `/api`, `/uploads`, `/processed` → backend; `/` → frontend
- **Config Examples:** See `docs/implementation.md`

### 4.4 Data Storage

**Database (Semi-Stable ⚠️):**
- **Current:** SQLite (file-based, `/data/photo_restoration.db`)
- **Future:** PostgreSQL migration planned for production scale
- **Migrations:** Alembic (first migration has known blocking issue)

**File Storage (Stable ✅):**
- **Uploads:** `/data/uploads/{session_id}/{uuid}_original.ext`
- **Processed:** `/data/processed/{session_id}/{uuid}_processed.ext`
- **Cleanup:** Automatic via session manager (configurable TTL)

---

## 5. Data Flow & Runtime Model

### Authentication Flow

```
User → Login Form → POST /api/v1/auth/login
                    ↓
        Backend: Verify credentials (bcrypt)
                 Create Session record
                 Generate JWT (7d or 24h)
                    ↓
        Frontend: Store JWT in localStorage
                    ↓
All requests → Authorization: Bearer {JWT}
                    ↓
        Backend: Verify JWT signature
                 Check expiration
                 Execute request
```

### Image Restoration Flow

```
1. Upload    → POST /api/v1/restore (multipart/form-data)
2. Validate  → Size, format, dimensions
3. Save      → /data/uploads/{session_id}/{uuid}_original.ext
4. DB Record → Create RestorationImage entry
5. AI Call   → HuggingFace or Replicate API (async)
6. Save      → /data/processed/{session_id}/{uuid}_processed.ext
7. DB Update → Update RestorationImage with URLs
8. Response  → Return original_url, processed_url, metadata
9. Display   → Frontend shows before/after comparison
```

### Configuration Loading (Hierarchical)

```
Priority (Highest → Lowest):
1. Environment variables (.env) → Override specific values for all settings
2. config/local.json            → Model configurations ONLY (gitignored)
3. config/{APP_ENV}.json        → Environment-specific overrides (production/dev/staging)
4. config/default.json          → Base config (REQUIRED)
```

**Critical:** `default.json` MUST exist or app falls back to deprecated `.env`-only mode.

**Important - `local.json` behavior:**
- `local.json` is **exclusively for model configuration overrides**
- Only the `models` array from `local.json` is merged (by model ID)
- **All other configuration keys in `local.json` are ignored** (application, database, server, cors, etc.)
- For non-model configuration overrides, use environment-specific files (`development.json`, `production.json`) or environment variables (.env)

---

## 6. Configuration & Environment Assumptions

### Environment Variables (Secrets in `.env`)

**Required:**
- `HF_API_KEY` - HuggingFace API key
- `SECRET_KEY` - JWT signing key (min 32 chars, generate with `secrets.token_urlsafe(32)`)
- `AUTH_USERNAME` / `AUTH_PASSWORD` - Initial admin credentials

**Optional:**
- `REPLICATE_API_TOKEN` - Replicate API token (only if using Replicate models)
- `APP_ENV` - Environment selection: `production` (default), `development`, `staging`

### JSON Configuration Files

**Required Files:**
- `backend/config/default.json` - Base configuration (committed to git)

**Optional Files:**
- `backend/config/production.json` - Production overrides (all settings)
- `backend/config/development.json` - Development overrides (all settings)
- `backend/config/local.json` - **Model configuration ONLY** (gitignored, non-model keys ignored)

**Configuration Sections:**
- `application` - App name, version, debug, log level
- `server` - Host, port, workers
- `cors` - CORS origins (JSON array)
- `models` - AI model definitions with flexible `replicate_schema`
- `database`, `file_storage`, `session`, `processing`

**See:** `docs/configuration.md` for complete reference

### Deployment Assumptions

**Docker:**
- Backend container: Port 8000 (internal network only)
- Frontend container: Port 3000 (exposed to host)
- External reverse proxy: User-provided (nginx, Apache, Traefik, Caddy)

**Development:**
- Python 3.13+ (`/opt/homebrew/bin/python3.13`)
- Node.js 22.12 (use Docker: `node:22.12-alpine`)
- Docker commands via CLAUDE.md rules

---

## 7. Stability Zones

### ✅ Stable (Production-Ready, Low Risk)

**Do NOT restructure without explicit user approval:**

- **Backend:**
  - FastAPI app structure (`app/main.py`, `app/api/v1/`)
  - Authentication system (JWT, bcrypt, multi-session)
  - Configuration loader (JSON hierarchy)
  - AI provider clients (HuggingFace, Replicate)
  - File storage system
  - Session manager

- **Frontend:**
  - App shell and routing (`app/App.tsx`, `app/Layout.tsx`)
  - Feature modules (`features/auth`, `features/restoration`, `features/history`, `features/admin`, `features/profile`)
  - Shared components (sqowe brand)
  - Auth store (Zustand)

- **Deployment:**
  - Docker Compose setup
  - External proxy architecture

### 🔄 Semi-Stable (Functional, May Evolve)

**Changes require planning and testing:**

- **Configuration:**
  - Admin UI for model config (in progress)
  - `local.json` priority system (recently added)
  - Flexible `replicate_schema` (may expand)

- **AI Providers:**
  - New models can be added via config
  - Provider-specific schemas

- **Testing:**
  - Edge case coverage expansion
  - Performance testing

### ⚠️ Experimental (Working, May Be Replaced)

**Expect changes, document assumptions:**

- **Database:**
  - SQLite → PostgreSQL migration planned
  - Alembic migrations (first migration blocking fresh installs - known issue in TECHNICAL_DEBTS.md)

- **Session Management:**
  - Background cleanup may move to separate worker/scheduler

### 🔮 Planned (Not Yet Implemented)

**Do NOT implement unless explicitly requested:**

- Phase 2: Model pipelines, batch processing, rate limiting
- Phase 3: OwnCloud integration, video frame restoration
- Phase 4: Production hardening, monitoring, security audit

**See:** `ROADMAP.md` for full timeline

---

## 8. AI Coding Rules and Behavioral Contracts

**⚠️ CRITICAL: This document (ARCHITECTURE.md) does NOT define coding rules.**

All AI assistants MUST locate and follow the authoritative AI rule files BEFORE making any changes.

### Authoritative AI Rule Files

**Backend Rules:**
- `AI.md` - General Python rules (PEP8, type hints, structure, environment variables)
- `AI_FastAPI.md` - FastAPI-specific patterns
- `AI-PYTHON-REST-API.md` - REST API conventions
- `AI_SQLite.md` - Database patterns with SQLAlchemy
- `AI_FLASK.md` - (Legacy, not used in current architecture)

**Frontend Rules:**
- `AI_FRONTEND.md` - Vite + React + TypeScript standards (strict mode, hooks, feature structure)
- `AI_WEB_COMMON.md` - General web development rules
- `tmp/AI_WEB_DESIGN_SQOWE.md` - sqowe brand design system (Material-inspired)

**Provider-Specific Rules:**
- `AI_replicate_provider.md` - Replicate API integration patterns

**Project Workflow:**
- `CLAUDE.md` - **CRITICAL:** Always propose before implementing, never auto-commit, check docs/chats/
  - Use `/opt/homebrew/bin/python3.13` for Python
  - Use Docker for Node.js: `docker run --rm -v "$(pwd)/frontend":/app -w /app node:22.12-alpine <cmd>`
  - Use `backend/venv` for tests and apps

**Reference Documentation:**
- `ROADMAP.md` - Development phases, feature timeline, test coverage
- `TECHNICAL_DEBTS.md` - Known issues, future improvements
- `docs/chats/` - 45+ previous implementation conversations (check before implementing similar features)
- `tmp/Brand-Guidelines.pdf` - Official sqowe brand guidelines

### Rule Precedence (Highest → Lowest)

1. **Explicit user instructions** in the current task
2. **Stack-specific `AI_*.md`** (e.g., `AI_FRONTEND.md` for frontend work)
3. **Global `AI.md`** (general Python rules)
4. **This ARCHITECTURE.md** (architecture constraints only)
5. **Implicit conventions** inferred from codebase

### Conflict Resolution

**If any rule conflicts or ambiguity is detected:**
1. **STOP** - Do not proceed with implementation
2. **ASK** - Present the conflict and request clarification
3. **DOCUMENT** - Once resolved, suggest updating the relevant AI*.md file

**Conservative Approach:**
- When in doubt, prefer existing patterns over new approaches
- Favor stability over cleverness
- Propose changes before implementing (see `CLAUDE.md`)

### Key Architectural Decisions (Do Not Violate)

1. **External Reverse Proxy** - Frontend is static-only (serve npm package), user provides proxy
2. **JSON Configuration** - `default.json` is REQUIRED, hierarchical overrides
3. **Async-First Backend** - All I/O operations use async/await
4. **JWT + DB Sessions** - Stateless JWT with database-backed session records for multi-device support
5. **Feature-Oriented Frontend** - Code organized by features, not layers
6. **SQLite for MVP** - Current DB, PostgreSQL migration planned

**Rationale:** See `docs/chats/` for detailed decision discussions

---

## 9. Quick Start for AI Assistants

**Before making ANY changes:**

1. Read `CLAUDE.md` (project workflow)
2. Read relevant `AI_*.md` files for the stack you're working on
3. Check `docs/chats/` for similar previous implementations
4. Understand which stability zone your changes affect (Section 7)
5. Propose your approach BEFORE implementing

**For new features:**
- Check `ROADMAP.md` to ensure alignment with project phases
- Check `TECHNICAL_DEBTS.md` for related known issues
- Review similar features in `docs/chats/`

**For bug fixes:**
- Check `TECHNICAL_DEBTS.md` first (may already be documented)
- Review related tests in `backend/tests/` or `frontend/src/__tests__/`

**For architecture questions:**
- This document (high-level structure)
- `docs/implementation.md` (deployment details)
- `docs/configuration.md` (config reference)

---

**End of ARCHITECTURE.md**
