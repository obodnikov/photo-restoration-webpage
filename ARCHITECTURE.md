# Architecture Overview

**Version:** 1.0.0
**Status:** Production-Ready (Phase 1 Complete, Phase 2.5 Complete)
**Last Updated:** 2025-12-31

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
- **Evolution:** Incremental phased development (Phase 2.5 complete)
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
├── backend/
│   ├── app/
│   │   ├── api/v1/            # Routes: auth, models, restore, admin, users
│   │   ├── core/              # Config (with versioning), security, deps
│   │   │   ├── config_migrations.py  # Migration framework
│   │   │   └── config_backup.py      # Backup/restore utilities
│   │   ├── db/                # SQLAlchemy models
│   │   ├── services/          # HuggingFace, Replicate, session manager
│   │   └── utils/             # Image processing, file handling
│   ├── config/                # JSON configs + backups/
│   ├── docs/                  # CONFIG_VERSIONING_TEST_COVERAGE.md, PERFORMANCE.md
│   ├── scripts/               # migrate_config.py, backup_config.py, restore_config.py
│   ├── tests/                 # 338 tests (99% coverage)
│   └── alembic/               # Database migrations
├── frontend/
│   ├── src/
│   │   ├── app/               # App shell, routing, layout
│   │   ├── features/          # Auth, restoration, history, admin, profile
│   │   ├── components/        # Shared UI (sqowe brand)
│   │   └── services/          # API client, auth store (Zustand)
│   └── __tests__/             # 224 tests (Vitest + RTL)
├── docs/chats/                # 47 implementation conversations
├── AI*.md                     # 9 AI coding rule files
├── ROADMAP.md, TECHNICAL_DEBTS.md, CLAUDE.md
└── docker-compose.yml
```

**Critical Paths:**
- Backend: `backend/app/main.py`, `backend/config/default.json` (v1.0.0 required)
- Frontend: `frontend/src/main.tsx`
- Config versioning: `backend/app/core/config_migrations.py`

---

## 4. Core Components

### 4.1 Frontend (Stable ✅)

**Tech:** Vite + React 18 + TypeScript (strict) + Zustand + CSS Modules

**Features:**
- **Auth** - Login, JWT management
- **Restoration** - Upload, AI processing, before/after viewer, custom model parameters UI
- **History** - Paginated image history
- **Admin** - User management, model configuration
- **Profile** - Password change, session management

**Routing:** `/` (login), `/restoration`, `/history`, `/admin`, `/profile`

### 4.2 Backend (Stable ✅)

**Tech:** FastAPI + SQLAlchemy (async) + SQLite + JWT

**Components:**
- **API Routes** - `/api/v1/{auth,models,restore,admin,users}`
- **Authentication** - JWT + bcrypt + multi-session
- **Configuration** - Hierarchical JSON loader with versioning system
- **Config Versioning** - Auto-migration, backup/restore (`config_migrations.py`, `config_backup.py`)
- **AI Providers** - HuggingFace + Replicate async clients
- **Database** - SQLAlchemy models (User, Session, RestorationImage)
- **Session Manager** - Background cleanup

### 4.3 External Integrations

**AI Providers:** HuggingFace Inference API (HF_API_KEY), Replicate API (REPLICATE_API_TOKEN)
**Reverse Proxy:** User-provided (nginx/Apache/Traefik/Caddy) - routes `/api`, `/uploads` → backend; `/` → frontend

### 4.4 Data Storage

**Database (Semi-Stable ⚠️):** SQLite (`/data/photo_restoration.db`), PostgreSQL migration planned
**File Storage (Stable ✅):** `/data/uploads/`, `/data/processed/`, auto-cleanup via session manager

---

## 5. Data Flow & Runtime Model

### Authentication Flow
```
Login → Verify credentials (bcrypt) → Create Session → Generate JWT → Store in localStorage
All requests → Authorization: Bearer {JWT} → Verify JWT → Execute
```

### Image Restoration Flow
```
1. Upload → POST /api/v1/restore
2. Validate → Size, format, dimensions
3. Save → /data/uploads/{session_id}/{uuid}_original.ext
4. AI Call → HuggingFace or Replicate API
5. Save → /data/processed/{session_id}/{uuid}_processed.ext
6. Response → Return URLs + metadata
```

### Configuration Loading with Versioning
```
1. Load → default.json, {env}.json, local.json
2. Detect Version → Check config_version (default: "0.9.0")
3. Validate → Ensure consistency across files
4. Backup → Auto-backup before migration (CONFIG_AUTO_MIGRATE=true)
5. Migrate → Apply migrations if version < 1.0.0
6. Merge → Deep merge: default → env → local
7. Validate → Pydantic schema validation
```

**Migration:** Legacy (0.9.0) → 1.0.0, auto-backup, rollback support

---

## 6. Configuration & Environment Assumptions

### Environment Variables (`.env`)

**Required:** `HF_API_KEY`, `SECRET_KEY`, `AUTH_USERNAME`, `AUTH_PASSWORD`
**Optional:** `REPLICATE_API_TOKEN`, `APP_ENV` (production/development/staging), `CONFIG_AUTO_MIGRATE` (default: true)

### JSON Configuration

**Files:** `default.json` (required, v1.0.0), `{env}.json` (optional), `local.json` (models only, gitignored)

**Versioning:**
- All configs include `config_version` (semver: "major.minor.patch")
- Auto-migration on startup (configurable)
- Auto-backups in `config/backups/`
- Version compatibility: rejects future versions, supports legacy 0.9.0 → 1.x
- Current version: 1.0.0

**Sections:** `config_version`, `application`, `server`, `cors`, `models`, `database`, `file_storage`, `session`, `processing`

**See:** `docs/configuration.md`, `docs/CONFIG_VERSIONING_PERFORMANCE.md`

### Deployment

**Docker:** Backend:8000 (internal), Frontend:3000 (exposed)
**Dev:** Python 3.13+ (`/opt/homebrew/bin/python3.13`), Node 22.12 (`docker run node:22.12-alpine`)

---

## 7. Stability Zones

### ✅ Stable (Production-Ready)

**Backend:**
- FastAPI app structure, authentication (JWT, bcrypt, multi-session)
- Configuration loader with versioning (`config.py`, `config_migrations.py`, `config_backup.py`)
- AI provider clients, file storage, session manager

**Frontend:**
- App shell, routing, feature modules, auth store (Zustand)

**Deployment:**
- Docker Compose, external proxy architecture

### 🔄 Semi-Stable (May Evolve)

- Admin UI for model config (in progress)
- `local.json` priority system, flexible `replicate_schema`
- Custom Model Parameters UI (7 input types, auto-detection, may expand)

### ⚠️ Experimental (May Be Replaced)

- SQLite → PostgreSQL migration planned
- Session management (may move to separate worker)

### 🔮 Planned (Not Implemented)

- Phase 2: Model pipelines, batch processing, rate limiting
- Phase 3: OwnCloud integration, video frame restoration
- Phase 4: Production hardening, monitoring

**See:** `ROADMAP.md`

---

## 8. AI Coding Rules and Behavioral Contracts

**⚠️ CRITICAL: This document does NOT define coding rules.**

### Authoritative AI Rule Files

**Backend:** `AI.md`, `AI_FastAPI.md`, `AI-PYTHON-REST-API.md`, `AI_SQLite.md`
**Frontend:** `AI_FRONTEND.md`, `AI_WEB_COMMON.md`, `tmp/AI_WEB_DESIGN_SQOWE.md`
**Provider:** `AI_replicate_provider.md`
**Workflow:** `CLAUDE.md` - Propose before implementing, check `docs/chats/`

**Reference:** `ROADMAP.md`, `TECHNICAL_DEBTS.md`, `tmp/Brand-Guidelines.pdf`

### Rule Precedence
1. Explicit user instructions
2. Stack-specific `AI_*.md` files
3. Global `AI.md`
4. This ARCHITECTURE.md (constraints only)
5. Implicit conventions

### Key Architectural Decisions

1. **External Reverse Proxy** - Frontend static-only, user provides proxy
2. **JSON Configuration with Versioning** - `default.json` required (v1.0.0), hierarchical overrides, auto-migration
3. **Async-First Backend** - All I/O uses async/await
4. **JWT + DB Sessions** - Stateless JWT with database session records
5. **Feature-Oriented Frontend** - Code by features, not layers
6. **SQLite for MVP** - PostgreSQL migration planned

**Rationale:** See `docs/chats/` for decision discussions

---

## 9. Quick Start for AI Assistants

**Before ANY changes:**
1. Read `CLAUDE.md` (workflow)
2. Read relevant `AI_*.md` for your stack
3. Check `docs/chats/` for similar implementations
4. Understand stability zone (Section 7)
5. Propose approach BEFORE implementing

**New features:** Check `ROADMAP.md`, `TECHNICAL_DEBTS.md`, review `docs/chats/`
**Bug fixes:** Check `TECHNICAL_DEBTS.md`, review related tests
**Architecture questions:** This doc, `docs/implementation.md`, `docs/configuration.md`

---

**End of ARCHITECTURE.md**
