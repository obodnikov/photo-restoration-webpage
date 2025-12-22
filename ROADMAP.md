# Photo Restoration Webpage - Development Roadmap

## Project Overview

A web application for restoring old scanned photos using multiple AI providers (HuggingFace, Replicate) with a clean, sqowe-branded interface.

**Tech Stack:**
- **Backend:** FastAPI (Python 3.13+)
- **Frontend:** Vite + React + TypeScript
- **Deployment:** Docker + Docker Compose + nginx reverse proxy
- **AI Providers:** HuggingFace Inference API, Replicate API
- **Design:** sqowe brand guidelines (Material-inspired)

---

## Phase 1: MVP (Minimum Viable Product)

### 1.1 Project Setup & Infrastructure ✅ **COMPLETE**

**Backend Setup:**
- [x] Initialize FastAPI project structure (follow AI_FastAPI.md)
  - [x] Create `backend/app/` directory structure
  - [x] Setup `app/main.py` with basic FastAPI app
  - [x] Configure `app/core/config.py` with pydantic BaseSettings
  - [x] Create `.env.example` with all required variables
  - [x] Setup `requirements.txt` with dependencies:
    - fastapi
    - uvicorn[standard]
    - pydantic[dotenv]
    - httpx (for async HF API calls)
    - python-multipart (file uploads)
    - pillow (image processing)
    - python-jose[cryptography] (JWT tokens)
    - passlib[bcrypt] (password hashing)
    - sqlalchemy (async)
    - aiosqlite

**Frontend Setup:**
- [x] Initialize Vite + React + TypeScript project (follow AI_FRONTEND.md)
  - [x] Create `frontend/` with project structure
  - [x] Configure TypeScript with strict mode
  - [x] Setup project structure (src/app, src/features, src/components)
  - [x] Install dependencies:
    - react, react-dom
    - react-router-dom
    - zustand (lightweight state management)
  - [x] Setup CSS architecture following AI_WEB_DESIGN_SQOWE.md
  - [x] sqowe logos available in `tmp/02. logotype/`
  - [x] Create design token CSS variables (colors, typography)

**Docker & DevOps:**
- [x] Create `backend/Dockerfile` (Python 3.13-slim)
- [x] Create `frontend/Dockerfile` (multi-stage: build + nginx serve)
- [x] Create `nginx/nginx.conf` for reverse proxy
- [x] Create `docker-compose.yml` with services:
  - [x] backend (FastAPI on port 8000)
  - [x] frontend (nginx on port 3000)
  - [x] nginx reverse proxy (port 80)
  - [x] volumes for SQLite data persistence
- [x] Create `.dockerignore` files
- [x] Create `docker-compose.dev.yml` for development with hot reload

**Documentation:**
- [x] Update README.md with project description and setup instructions
- [x] Document environment variables in `.env.example`
- [x] Add development setup guide (Docker + local)

**Completed:** December 13, 2024

---

### 1.2 Authentication System ✅ **COMPLETE**

**Backend:**
- [x] Implement token-based authentication in `app/core/security.py`
  - [x] JWT token generation and validation
  - [x] Password hashing utilities
  - [x] Token dependency for protected routes
- [x] Create auth schemas in `app/api/v1/schemas/auth.py`
  - [x] LoginRequest (username, password, remember_me)
  - [x] TokenResponse (access_token, token_type, expires_in)
  - [x] UserResponse
  - [x] TokenValidateResponse
- [x] Create auth routes in `app/api/v1/routes/auth.py`
  - [x] POST `/api/v1/auth/login` - authenticate and get token
  - [x] POST `/api/v1/auth/validate` - validate token
  - [x] GET `/api/v1/auth/me` - get current user
- [x] Configure simple user storage (hardcoded from .env for MVP)
- [x] Add "Remember Me" functionality (7 days token expiration)
- [x] Integrate auth routes into main.py

**Frontend:**
- [x] Create auth feature in `src/features/auth/`
  - [x] `components/LoginForm.tsx` - login UI component with sqowe branding
  - [x] `hooks/useAuth.ts` - authentication logic hook
  - [x] `services/authService.ts` - API calls for auth
  - [x] `types.ts` - auth-related TypeScript types
  - [x] `pages/LoginPage.tsx` - full login page
- [x] Create auth store in `src/services/authStore.ts` (Zustand)
  - [x] Store token in localStorage
  - [x] Provide auth state globally
  - [x] Auto-logout on token expiration
  - [x] Token expiry checking (every minute)
  - [x] Initialize from localStorage on app start
- [x] Implement protected route wrapper (`ProtectedRoute.tsx`)
- [x] Create login page with sqowe branding
- [x] Add token to all API requests (Authorization header via `apiClient.ts`)
- [x] Create API client with auto-injection of JWT token
- [x] Handle 401 responses (auto-redirect to login)
- [x] Add "Remember Me" checkbox (7 days vs 24 hours)
- [x] Update App.tsx with routing (BrowserRouter, Routes)

**Completed:** December 14, 2024

**Tests for Phase 1.2:**
- [x] Backend: Basic config tests (`backend/tests/test_config.py`) - 21 tests ✅
- [x] Backend: Health check tests (`backend/tests/test_health.py`) - 21 tests ✅
  - [x] `/health` returns 200 with correct JSON
  - [x] Root endpoint returns API info
  - [x] App startup validation (HF_API_KEY, SECRET_KEY, directories)
  - [x] MODELS_CONFIG parsing tests (valid/invalid JSON, get by ID)
  - [x] Security configuration tests (SECRET_KEY validation, debug mode)
- [x] Backend: Auth tests (`backend/tests/api/v1/test_auth.py`) - 24 tests ✅
  - [x] POST `/api/v1/auth/login` with valid credentials → 200 + token
  - [x] POST `/api/v1/auth/login` with invalid username → 401
  - [x] POST `/api/v1/auth/login` with invalid password → 401
  - [x] POST `/api/v1/auth/login` with remember_me=True → 7 days expiration
  - [x] POST `/api/v1/auth/login` with remember_me=False → 24h expiration
  - [x] POST `/api/v1/auth/login` with missing/empty credentials → 422/401
  - [x] POST `/api/v1/auth/validate` with valid token → 200
  - [x] POST `/api/v1/auth/validate` with expired token → 401
  - [x] POST `/api/v1/auth/validate` with malformed token → 401
  - [x] POST `/api/v1/auth/validate` without token → 403
  - [x] GET `/api/v1/auth/me` with valid token → returns username
  - [x] GET `/api/v1/auth/me` without token → 403
  - [x] GET `/api/v1/auth/me` with expired/invalid token → 401
  - [x] Full authentication flows (login → validate → get_me)
  - [x] Multiple logins generate different tokens
  - [x] Security tests (no user existence leakage, password not logged, token forgery)
- [x] Backend: Security utilities tests (`backend/tests/services/test_security.py`) - 29 tests ✅
  - [x] `verify_password()` with matching password → True
  - [x] `verify_password()` with wrong password → False
  - [x] `verify_password()` case sensitivity and empty password handling
  - [x] `get_password_hash()` creates valid bcrypt hash
  - [x] `get_password_hash()` different salts each time
  - [x] `create_access_token()` with custom expires_delta
  - [x] `create_access_token()` with default expiration
  - [x] `create_access_token()` preserves additional data and is deterministic in tests
  - [x] `verify_token()` with valid token → returns payload
  - [x] `verify_token()` with expired token → None
  - [x] `verify_token()` with invalid signature/malformed/wrong algorithm → None
  - [x] `authenticate_user()` with valid credentials → user dict
  - [x] `authenticate_user()` with invalid username/password → None
  - [x] `authenticate_user()` case sensitivity and empty credentials
  - [x] Edge cases: special characters, long passwords (bcrypt 72-byte limit), token subjects
- [x] Backend: Test infrastructure ✅
  - [x] Create `backend/tests/conftest.py` with 12 shared fixtures
  - [x] Create `backend/conftest.py` for environment loading and module reloading
  - [x] Create `backend/.env.test` for test environment (committed to git)
  - [x] Add `pytest.ini` configuration with markers and settings
  - [x] Add `pytest-cov` for coverage reporting (99% coverage achieved)
  - [x] Fix bcrypt compatibility (pin bcrypt<5.0.0 for passlib 1.7.4)

**Backend Test Summary:** 82 tests, 100% passing, 99% code coverage ✅

- [x] Frontend: Test configuration ✅
  - [x] Create `frontend/vitest.config.ts`
  - [x] Create `frontend/src/__tests__/setup.ts`
  - [x] Add test utilities in `frontend/src/test-utils/`
  - [x] Install test dependencies (@testing-library/react, @testing-library/jest-dom, @testing-library/user-event, jsdom)
- [x] Frontend: Auth store tests (`frontend/src/__tests__/authStore.test.ts`) - 18 tests ✅
  - [x] `setAuth()` updates state and localStorage
  - [x] `setAuth()` calculates correct expiration time
  - [x] `clearAuth()` removes token from state and localStorage
  - [x] Token persists after page reload (via initializeAuthStore)
  - [x] Expired tokens are not restored on init
  - [x] Incomplete localStorage data is cleared on init
  - [x] Remember Me sets 24-hour expiration (regular login)
  - [x] Remember Me sets 7-day expiration (remember_me=true)
  - [x] `checkTokenExpiry()` returns false for valid token
  - [x] `checkTokenExpiry()` clears auth for expired token
  - [x] `isTokenExpired()` correctly identifies expired tokens
  - [x] Auto-logout on token expiration (periodic check with setInterval)
- [x] Frontend: Auth component tests (`frontend/src/__tests__/auth.test.tsx`) - 17 tests ✅
  - [x] LoginForm renders with username/password fields
  - [x] LoginForm renders "Remember Me" checkbox
  - [x] LoginForm disables submit button when fields are empty
  - [x] LoginForm enables submit button when fields are filled
  - [x] LoginForm submits valid credentials → stores token
  - [x] LoginForm shows error on invalid credentials
  - [x] LoginForm shows loading state during login
  - [x] LoginForm redirects to home after successful login
  - [x] LoginForm sends remember_me=true when checkbox is checked
  - [x] LoginForm sends remember_me=false when checkbox is not checked
  - [x] useAuth hook: isAuthenticated reflects token state
  - [x] useAuth hook: login() stores token and updates state
  - [x] useAuth hook: logout() clears token
  - [x] useAuth hook: logout() navigates to login page
  - [x] useAuth hook: shows error when login fails
  - [x] useAuth hook: shows loading state during login
- [x] Frontend: API client tests (`frontend/src/__tests__/apiClient.test.ts`) - 20 tests ✅
  - [x] Auto-injects Authorization header when token exists
  - [x] Redirects to login when no token exists for protected endpoint
  - [x] Allows requests without token when requiresAuth=false
  - [x] Redirects to login when token is expired
  - [x] Handles 401 responses (clears auth and redirects to login)
  - [x] Returns typed responses from GET/POST/PUT/DELETE requests
  - [x] Makes correct HTTP method calls (GET, POST, PUT, DELETE)
  - [x] POST/PUT requests include JSON body
  - [x] Throws ApiError for HTTP errors with correct status codes
  - [x] Extracts error messages from response body
  - [x] Handles network errors gracefully
  - [x] Includes Content-Type header
  - [x] Merges custom headers with default headers
  - [x] Constructs correct URLs with base path

**Frontend Test Summary:** 55 tests, 100% passing ✅

---

### 1.3 AI Models Configuration ✅ **COMPLETE**

**Backend:**
- [x] Models configuration loaded from `MODELS_CONFIG` environment variable
  - [x] Model registry with ID, name, HF model path, category, description, parameters, tags, version
  - [x] Default models for MVP:
    - Swin2SR 2x (`caidas/swin2SR-classical-sr-x2-64`)
    - Swin2SR 4x (`caidas/swin2SR-classical-sr-x4-64`)
    - Qwen Image Edit (`Qwen/Qwen-Image-Edit-2509`)
- [x] Create model schemas in `app/api/v1/schemas/model.py`
  - [x] ModelParameters - model-specific parameters
  - [x] ModelInfo - complete model information with tags and version
  - [x] ModelListResponse - list response with total count
- [x] Create model routes in `app/api/v1/routes/models.py`
  - [x] GET `/api/v1/models` - list available models
  - [x] GET `/api/v1/models/{model_id}` - get model details
  - [x] Configurable authentication via `MODELS_REQUIRE_AUTH` setting (default: public)
  - [x] Models caching for performance
- [x] Add model configuration to `.env.example`
  - [x] `MODELS_CONFIG` with schema documentation (id, name, model, category, description, parameters, tags, version)
  - [x] `MODELS_REQUIRE_AUTH` configuration option

**Tests for Phase 1.3:**
- [x] Backend: Model configuration tests (integrated in `backend/tests/test_config.py`) ✅
  - [x] Load model definitions from MODELS_CONFIG env var ✅
  - [x] Validate model schema JSON ✅
  - [x] Get model by ID returns correct model ✅
  - [x] Invalid MODELS_CONFIG JSON raises ValidationError ✅
- [x] Backend: Model routes tests (`backend/tests/api/v1/test_models.py`) - 17 tests ✅
  - [x] GET `/api/v1/models` returns all models with correct schema ✅
  - [x] GET `/api/v1/models/{model_id}` returns model details ✅
  - [x] GET `/api/v1/models/invalid-id` returns 404 ✅
  - [x] Response includes all required fields (id, name, description, category, parameters, tags, version) ✅
  - [x] Public access works when `MODELS_REQUIRE_AUTH=false` ✅
  - [x] Authentication required when `MODELS_REQUIRE_AUTH=true` ✅
  - [x] Valid token grants access to protected endpoints ✅
  - [x] Invalid/missing tokens are rejected ✅
  - [x] Models caching works correctly ✅

**Completed:** December 15, 2024

**Environment Variables:**
```
# HuggingFace API
HF_API_KEY=your_hf_api_key_here
HF_API_TIMEOUT=60

# Available Models (JSON format)
MODELS_CONFIG=[
  {
    "id": "swin2sr-2x",
    "name": "Swin2SR 2x Upscale",
    "model": "caidas/swin2SR-classical-sr-x2-64",
    "category": "upscale",
    "description": "Fast 2x upscaling"
  },
  {
    "id": "swin2sr-4x",
    "name": "Swin2SR 4x Upscale",
    "model": "caidas/swin2SR-classical-sr-x4-64",
    "category": "upscale",
    "description": "Fast 4x upscaling"
  },
  {
    "id": "qwen-edit",
    "name": "Qwen Image Enhance",
    "model": "Qwen/Qwen-Image-Edit-2509",
    "category": "enhance",
    "description": "AI-powered enhancement"
  }
]
```

---

### 1.4 HuggingFace Integration Service ✅ **COMPLETE**

**Backend:**
- [x] Create HF Inference service in `app/services/hf_inference.py` ✅
  - [x] `HFInferenceService` class with async methods ✅
  - [x] `async def process_image(model_id, image_bytes)` - main processing method ✅
  - [x] Error handling for HF API failures (custom exception classes) ✅
  - [x] Timeout handling (60s default, configurable) ✅
  - [x] Response validation (content-type checking) ✅
  - [x] `check_model_status()` method for model availability ✅
- [x] Create image utilities in `app/utils/image_processing.py` ✅
  - [x] Image validation (format, size limits) ✅
  - [x] Image conversion (PIL Image ↔ bytes) ✅
  - [x] Image preprocessing for HF API ✅
  - [x] Image postprocessing from HF API ✅
  - [x] Upload file validation and reading ✅
  - [x] Image info extraction ✅
- [x] Add comprehensive error handling ✅
  - [x] HF API rate limits (HFRateLimitError) ✅
  - [x] Invalid image formats (ImageFormatError) ✅
  - [x] Model unavailable errors (HFModelError) ✅
  - [x] Timeout errors (HFTimeoutError) ✅
  - [x] Connection errors ✅
- [x] Add service tests with mocked HF API ✅

**Tests for Phase 1.4:**
- [x] Backend: Test data setup ✅
  - [x] Create `backend/tests/data/` directory ✅
  - [x] Add `old_photo_small.jpg` (13.35 KB test image) ✅
  - [x] Add `old_photo_large.jpg` (383 KB test image) ✅
  - [x] Add `test_image.png` (PNG format test) ✅
  - [x] Add `invalid_file.txt` (non-image file) ✅
  - [x] Add `corrupted_image.jpg` (truncated/invalid JPEG) ✅
- [x] Backend: Mock HF API service (`backend/tests/mocks/hf_api.py`) ✅
  - [x] Mock successful image processing (returns test image bytes) ✅
  - [x] Mock HF rate limit response (429) ✅
  - [x] Mock HF server error (5xx) ✅
  - [x] Mock timeout scenarios ✅
  - [x] Mock malformed response ✅
  - [x] Mock model loading (503) ✅
  - [x] Mock model not found (404) ✅
- [x] Backend: HF Inference service tests (`backend/tests/services/test_hf_inference.py`) - 23 tests ✅
  - [x] `process_image()` with valid model and image → returns processed image ✅
  - [x] `process_image()` with invalid model_id → raises error ✅
  - [x] `process_image()` handles HF 429 rate limit → raises HFRateLimitError ✅
  - [x] `process_image()` handles HF 5xx error → raises HFInferenceError ✅
  - [x] `process_image()` handles timeout → raises HFTimeoutError ✅
  - [x] `process_image()` validates response is valid image ✅
  - [x] `process_image()` with custom parameters ✅
  - [x] `check_model_status()` tests (ready, loading, error) ✅
  - [x] Content-type validation tests ✅
- [x] Backend: Image utilities tests (`backend/tests/utils/test_image_processing.py`) - 37 tests ✅
  - [x] Validate image format (JPEG, PNG accepted) ✅
  - [x] Validate image format (BMP, TXT, GIF rejected) ✅
  - [x] Validate image size (within MAX_UPLOAD_SIZE) ✅
  - [x] Validate image size (exceeds limit → error) ✅
  - [x] Image conversion: PIL Image to bytes (PNG, JPEG) ✅
  - [x] Image conversion: bytes to PIL Image ✅
  - [x] Handle corrupted image data → clear error message ✅
  - [x] PIL image validation (modes, dimensions) ✅
  - [x] Upload file validation tests ✅
  - [x] Image info extraction tests ✅
  - [x] Integration tests (full conversion cycles) ✅

**Completed:** December 15, 2024

---

### 1.5 Session Management & History ✅ **COMPLETE**

**Backend:**
- [x] Create database models in `app/db/models.py` ✅
  - [x] Session model (session_id, created_at, last_accessed) ✅
  - [x] ProcessedImage model (id, session_id, original_filename, model_id, created_at, original_path, processed_path) ✅
  - [x] Cascade delete relationship (deleting session removes images) ✅
  - [x] to_dict() serialization methods ✅
- [x] Setup SQLite database in `app/db/database.py` ✅
  - [x] Async SQLAlchemy engine (aiosqlite) ✅
  - [x] Session factory (async_sessionmaker) ✅
  - [x] Database initialization (init_db, close_db) ✅
  - [x] Follow AI_SQLite.md (WAL mode, proper configuration) ✅
  - [x] FastAPI dependency injection (get_db) ✅
- [x] Create session manager in `app/services/session_manager.py` ✅
  - [x] Create session (UUID-based session_id) ✅
  - [x] Get session (with last_accessed update) ✅
  - [x] Get session history (with pagination) ✅
  - [x] Save processed image metadata ✅
  - [x] Cleanup old sessions (delete sessions + files) ✅
  - [x] Delete specific session (with files) ✅
  - [x] Custom exceptions (SessionManagerError, SessionNotFoundError) ✅
- [x] Add file storage utilities ✅
  - [x] Temporary storage for uploaded images (data/uploads/) ✅
  - [x] Storage for processed images (data/processed/) ✅
  - [x] Session-based directory structure ✅
  - [x] Cleanup task for old files ✅

**Tests for Phase 1.5:**
- [x] Backend: Database model tests (`backend/tests/db/test_models.py`) - 11 tests ✅
  - [x] Session model creates valid session ✅
  - [x] Session model tracks created_at and last_accessed ✅
  - [x] Session model to_dict() method ✅
  - [x] ProcessedImage model stores all required fields ✅
  - [x] ProcessedImage model links to session correctly ✅
  - [x] ProcessedImage to_dict() method ✅
  - [x] Database constraints work (unique session_id, foreign keys) ✅
  - [x] Session with multiple images ✅
  - [x] Cascade delete works (session deletion removes images) ✅
- [x] Backend: Session manager tests (`backend/tests/services/test_session_manager.py`) - 29 tests ✅
  - [x] SessionManager initialization (with/without settings) ✅
  - [x] `create_session()` creates new session in database ✅
  - [x] `create_session()` generates unique UUIDs ✅
  - [x] `get_session()` returns existing session ✅
  - [x] `get_session()` updates last_accessed timestamp ✅
  - [x] `get_session_history()` returns user's processed images ✅
  - [x] `get_session_history()` with pagination (limit/offset) ✅
  - [x] `get_session_history()` ordered by created_at DESC ✅
  - [x] `save_processed_image()` stores metadata correctly ✅
  - [x] `save_processed_image()` with model parameters (JSON) ✅
  - [x] `cleanup_old_sessions()` deletes sessions older than cutoff ✅
  - [x] `cleanup_old_sessions()` deletes associated files ✅
  - [x] `cleanup_old_sessions()` handles missing files gracefully ✅
  - [x] `delete_session()` deletes specific session + files ✅
  - [x] Storage path management (get_storage_path_for_session) ✅
  - [x] Error handling (SessionNotFoundError, database errors) ✅
- [x] Backend: Database setup tests (`backend/tests/db/test_database.py`) - 19 tests ✅
  - [x] Database initialization creates tables ✅
  - [x] SQLite WAL mode configuration (or MEMORY for in-memory) ✅
  - [x] SQLite foreign keys enabled ✅
  - [x] SQLite synchronous and busy_timeout configured ✅
  - [x] Async SQLAlchemy engine creation ✅
  - [x] Session factory creates valid sessions ✅
  - [x] get_db() dependency yields and commits/rollbacks ✅
  - [x] close_db() disposes engine ✅

**Completed:** December 15, 2024

---

### 1.6 Image Restoration API ✅ **COMPLETE**

**Backend:**
- [x] Create restoration schemas in `app/api/v1/schemas/restoration.py`
  - [x] RestoreResponse (id, original_url, processed_url, model_id, timestamp, session_id)
  - [x] HistoryItemResponse, HistoryResponse (paginated list)
  - [x] ImageDetailResponse, DeleteResponse
- [x] Create restoration routes in `app/api/v1/routes/restoration.py`
  - [x] POST `/api/v1/restore` - upload and process image
    - [x] Validate authentication token (JWT with session_id)
    - [x] Validate image file (format, size, content)
    - [x] Get session from token
    - [x] Enforce concurrent upload limit per session (configurable)
    - [x] Call HF Inference service
    - [x] Save original and processed images (UUID prefix + original filename)
    - [x] Store metadata in database
    - [x] Return processed image info
  - [x] GET `/api/v1/restore/history` - get session history (paginated)
  - [x] GET `/api/v1/restore/{image_id}` - get specific processed image
  - [x] GET `/api/v1/restore/{image_id}/download` - download processed image
  - [x] DELETE `/api/v1/restore/{image_id}` - delete processed image
- [x] Add background cleanup service with APScheduler
  - [x] Periodic scheduled cleanup (configurable interval)
  - [x] Delete sessions older than threshold (configurable hours)
  - [x] Delete associated files from filesystem
  - [x] Run on startup and periodically
- [x] Add comprehensive error handling and logging
  - [x] Map HF errors to HTTP status codes (429→503, timeout→504, errors→502)
  - [x] User-friendly error messages
- [x] Update auth routes to create session on login
- [x] Add configuration variables (cleanup interval, concurrent limits)
- [x] Add API tests for all endpoints

**Static File Serving:**
- [x] Configure FastAPI to serve uploaded/processed images (already configured in Phase 1.1)
- [x] Setup proper CORS headers (via CORS middleware)
- [x] Session-based directory isolation

**Tests for Phase 1.6:**
- [x] Backend: Restoration validation tests (`backend/tests/api/v1/test_restore_validation.py`) - 11 tests ✅
  - [x] Upload valid JPEG within size limit → 200 + job info
  - [x] Upload valid PNG within size limit → 200 + job info
  - [x] Upload unsupported format (BMP, TXT) → 400 with error
  - [x] Upload exceeds MAX_UPLOAD_SIZE → 413 or 400 with clear error
  - [x] Upload corrupted image → 400 with "Invalid image data"
  - [x] Upload without authentication → 401
  - [x] Upload with expired token → 401
  - [x] Empty file, no model_id, no file validation
- [x] Backend: Restoration model tests (`backend/tests/api/v1/test_restore_models.py`) - 13 tests ✅
  - [x] Request with valid model_id → calls correct HF model
  - [x] Unknown model_id → 400 "Unknown model"
  - [x] HF returns binary image → response is valid image
  - [x] HF returns 429 rate limit → backend returns 503 with retry-after
  - [x] HF network error → backend returns 502 "Model service unavailable"
  - [x] Request timeout → backend returns 504 timeout error
  - [x] HF model loading (503) → appropriate error
  - [x] Response includes all required fields
  - [x] Concurrent upload limit enforcement
- [x] Backend: Restoration API integration tests (`backend/tests/api/v1/test_restore_integration.py`) - 18 tests ✅
  - [x] Full restore flow: upload → process → save → return URLs
  - [x] Original image saved to UPLOAD_DIR
  - [x] Processed image saved to PROCESSED_DIR
  - [x] Metadata stored in database
  - [x] GET `/api/v1/restore/history` returns user's processed images
  - [x] GET `/api/v1/restore/history` pagination works
  - [x] GET `/api/v1/restore/{image_id}` returns specific image
  - [x] GET `/api/v1/restore/{image_id}/download` downloads processed image
  - [x] DELETE `/api/v1/restore/{image_id}` deletes image and files
  - [x] User isolation (cannot access other sessions' images)
  - [x] Filename preserved with UUID prefix
  - [x] History ordered by created_at DESC
- [x] Backend: Background cleanup tests (`backend/tests/services/test_cleanup.py`) - 8 tests ✅
  - [x] Cleanup task deletes sessions older than SESSION_CLEANUP_HOURS
  - [x] Cleanup task deletes associated files from filesystem
  - [x] Cleanup task preserves recent sessions
  - [x] Cleanup task handles missing files gracefully
  - [x] Multiple old sessions cleanup
  - [x] Custom hours threshold
  - [x] Empty database handling
- [x] Backend: Static file serving tests (`backend/tests/test_static_files.py`) - 11 tests ✅
  - [x] GET `/uploads/{filename}` serves uploaded image
  - [x] GET `/processed/{filename}` serves processed image
  - [x] Nonexistent files return 404
  - [x] CORS headers present
  - [x] Security headers present
  - [x] Direct file access without auth works (static files are public)
  - [x] Path traversal protection
  - [x] Session isolation in file paths

**Backend Test Summary for Phase 1.6:** 61 new tests ✅
**Total Backend Tests:** 279 tests (218 from phases 1.1-1.5 + 61 from phase 1.6) ✅

**Completed:** December 15, 2024

---

### 1.7 Frontend - Core Features ✅ **COMPLETE**

**Image Upload Feature:**
- [x] Create restoration feature in `src/features/restoration/`
  - [x] `components/ImageUploader.tsx` - drag & drop upload component
  - [x] `components/ModelSelector.tsx` - model selection dropdown
  - [x] `components/ImageComparison.tsx` - before/after slider
  - [x] `components/ProcessingStatus.tsx` - loading state, progress
  - [x] `hooks/useImageRestore.ts` - restoration logic
  - [x] `services/restorationService.ts` - API calls
  - [x] `types.ts` - restoration-related types
- [x] Implement file validation on frontend
  - [x] File type validation (jpg, png)
  - [x] File size validation (max 10MB)
  - [x] User-friendly error messages

**History Feature:**
- [x] Create history feature in `src/features/history/`
  - [x] `components/HistoryList.tsx` - list of processed images
  - [x] `components/HistoryCard.tsx` - individual history item
  - [x] `hooks/useHistory.ts` - fetch and manage history
  - [x] `services/historyService.ts` - API calls
  - [x] `types.ts` - history-related types
- [x] Implement history UI
  - [x] Thumbnail grid view
  - [x] Click to view/compare
  - [x] Download button
  - [x] Delete button

**API Client:**
- [x] Create API client in `src/services/apiClient.ts`
  - [x] Typed HTTP methods (GET, POST, DELETE)
  - [x] Auto-inject auth token from store
  - [x] Error handling and user-friendly messages
  - [x] File upload support with progress
- [x] Configure base URL from environment
  - [x] `VITE_API_BASE_URL=/api/v1`

**Tests for Phase 1.7:**
- [x] Frontend: Test utilities setup
  - [x] Create `frontend/src/test-utils/mockApiClient.ts` for mocked API calls
  - [x] Create `frontend/src/test-utils/testData.ts` for test fixtures
  - [x] Add mock file upload utilities
- [x] Frontend: Image upload tests (`frontend/src/__tests__/imageUploader.test.tsx`)
  - [x] ImageUploader renders drag & drop area
  - [x] ImageUploader accepts file via file picker
  - [x] ImageUploader accepts file via drag & drop
  - [x] ImageUploader shows preview after file selection
  - [x] ImageUploader rejects non-image files (shows error)
  - [x] ImageUploader rejects files exceeding size limit
  - [x] ImageUploader clears selection on cancel
- [x] Frontend: Model selector tests (`frontend/src/__tests__/modelSelector.test.tsx`)
  - [x] ModelSelector fetches and renders model list
  - [x] ModelSelector displays model names and descriptions
  - [x] ModelSelector allows model selection
  - [x] ModelSelector highlights selected model
  - [x] ModelSelector handles API error gracefully
- [x] Frontend: Image restoration hook tests (`frontend/src/__tests__/useImageRestore.test.tsx`)
  - [x] `uploadAndRestore()` uploads image and calls API
  - [x] `uploadAndRestore()` shows loading state during processing
  - [x] `uploadAndRestore()` returns processed image URL on success
  - [x] `uploadAndRestore()` shows error on validation failure
  - [x] `uploadAndRestore()` shows error on network failure
  - [x] `uploadAndRestore()` handles HF service unavailable (503)
- [x] Frontend: Restoration service tests (`frontend/src/__tests__/restorationService.test.tsx`)
  - [x] `restoreImage()` sends multipart form data
  - [x] `restoreImage()` includes model_id in request
  - [x] `restoreImage()` includes auth token
  - [x] `restoreImage()` handles 401 (redirects to login)
  - [x] `restoreImage()` handles 400 (validation error)
  - [x] `restoreImage()` handles 503 (service unavailable)
- [x] Frontend: History tests (`frontend/src/__tests__/history.test.tsx`)
  - [x] HistoryList fetches and displays processed images
  - [x] HistoryCard shows thumbnail and metadata
  - [x] HistoryCard allows clicking to view full image
  - [x] HistoryCard has download button
  - [x] HistoryCard has delete button
  - [x] Delete removes item from list after confirmation
  - [x] History handles empty state (no images processed)

**Completed:** December 15, 2024

**Frontend Test Summary:** 115 tests passing ✅
- Shared components: 43 tests
- Restoration feature: 40 tests
- History feature: 32 tests
- Total new tests for Phase 1.7: 60 tests

**Features Delivered:**
- Complete image restoration workflow with drag & drop upload
- Model selection with 3 view modes (Original, Restored, Compare)
- Real-time processing status with progress tracking
- Image comparison viewer with side-by-side layout
- Full restoration history with pagination
- Download and delete functionality
- Layout with header/footer visible on all pages
- Responsive design (mobile, tablet, desktop)
- sqowe brand styling throughout
- Comprehensive error handling

---

### 1.8 Frontend - UI/UX Implementation ✅ **COMPLETE**

**Layout & Navigation:**
- [x] Create app shell in `src/app/`
  - [x] `App.tsx` - main app component with router (completed in Phase 1.7)
  - [x] `Layout.tsx` - main layout with header/footer (enhanced with mobile menu)
  - [x] `ProtectedRoute.tsx` - route guard component (completed in Phase 1.7)
- [x] Create navigation component
  - [x] Header with sqowe logo
  - [x] Navigation menu with mobile hamburger menu
  - [x] Logout button
  - [x] Follow AI_WEB_DESIGN_SQOWE.md for styling

**Shared Components (sqowe branded):**
- [x] Create shared components in `src/components/`
  - [x] `Button.tsx` - primary, secondary, gradient variants (completed in Phase 1.7)
  - [x] `Card.tsx` - light and dark variants (completed in Phase 1.7)
  - [x] `Input.tsx` - form input component with validation
  - [x] `Loader.tsx` - loading spinner (completed in Phase 1.7)
  - [x] `ErrorMessage.tsx` - error display component (completed in Phase 1.7)
  - [x] `Modal.tsx` - modal dialog component with accessibility
- [x] All components follow sqowe design system:
  - [x] Colors: #222222, #8E88A3, #5B5377, #B2B3B2
  - [x] Typography: Montserrat font family
  - [x] Spacing: 8px grid system
  - [x] Border radius, shadows as per brand guide

**Styling Setup:**
- [x] Create global styles in `src/styles/`
  - [x] `base.css` - CSS variables, resets, tokens (completed in Phase 1.7)
  - [x] `layout.css` - grid, containers, responsive utilities (completed in Phase 1.7)
  - [x] `components/` - component-specific styles (enhanced with form/modal styles)
  - [x] `themes/` - sqowe brand theme
- [x] Import Montserrat from Google Fonts (completed in Phase 1.7)
- [x] Setup responsive breakpoints (mobile 768px, tablet 1024px)
- [x] Follow AI_WEB_COMMON.md (no inline styles, separation of concerns)

**Main Pages:**
- [x] Login page (`/login`) - completed in Phase 1.7
  - [x] sqowe branded login form
  - [x] Token authentication
  - [x] Error handling
- [x] Restoration page (`/`) - main application page - completed in Phase 1.7
  - [x] Model selector
  - [x] Image uploader (drag & drop)
  - [x] Processing status
  - [x] Before/After comparison slider
  - [x] Download button
- [x] History page (`/history`) - completed in Phase 1.7
  - [x] Grid of processed images
  - [x] Pagination
  - [x] View, download, delete actions

**Responsive Design:**
- [x] Mobile-first approach
- [x] Mobile hamburger menu (< 768px)
- [x] Tablet breakpoint (768px - 1023px)
- [x] Desktop breakpoint (1024px+)
- [x] Touch-friendly targets (44x44px minimum)

**Tests for Phase 1.8:**
- [x] Frontend: Shared component tests (`frontend/src/__tests__/components/`) - 6 test files ✅
  - [x] Button component tests (17 tests) - variants, sizes, events, loading, disabled
  - [x] Card component tests (9 tests) - variants, props, hover, clickable
  - [x] Input component tests (14 tests + 9 TextArea tests) - validation, error states, accessibility
  - [x] Loader component tests (7 tests) - sizes, fullscreen, text
  - [x] ErrorMessage component tests (8 tests) - messages, title, close functionality
  - [x] Modal component tests (18 tests) - open/close, overlay, escape key, accessibility
- [x] Frontend: Layout tests (`frontend/src/__tests__/layout.test.tsx`) - 1 test file ✅
  - [x] Header renders with sqowe logo
  - [x] Navigation menu renders correctly
  - [x] Mobile hamburger menu toggle
  - [x] Logout button triggers logout
  - [x] Footer renders with correct content
  - [x] Responsive layout works at all breakpoints
- [x] Frontend: Page integration tests - completed in Phase 1.7 ✅
  - [x] RestorationPage renders all components correctly
  - [x] RestorationPage: upload → select model → restore flow works
  - [x] RestorationPage shows loading state during processing
  - [x] RestorationPage shows before/after comparison on success
  - [x] RestorationPage shows error message on failure
  - [x] HistoryPage renders history list
  - [x] HistoryPage allows viewing, downloading, deleting images
- [x] Frontend: Accessibility tests (`frontend/src/__tests__/accessibility.test.tsx`) - 1 test file ✅
  - [x] All interactive elements are keyboard accessible
  - [x] ARIA labels are present on important elements (buttons, inputs, modals)
  - [x] Color contrast meets WCAG AA standards (tested with axe-core)
  - [x] Focus indicators are visible
  - [x] Proper semantic HTML and landmarks (nav, main)
  - [x] Modal focus management and aria attributes

**Completed:** December 16, 2024

**Test Summary for Phase 1.8:**
- New component tests: 82 tests ✅
- Layout tests: 12 tests ✅
- Accessibility tests: 15+ tests ✅
- Total new tests: 109+ tests
- Coverage: All UI components, layout, and accessibility standards

**Components Delivered:**
- Input component with validation and error handling
- Modal component with full accessibility support
- Mobile hamburger navigation menu
- Enhanced responsive design across all breakpoints
- Comprehensive test coverage for all UI components
- Accessibility testing with jest-axe

---

### 1.8.1 Multi-Provider Support (Replicate) ✅ **COMPLETE**

**Backend:**
- [x] Add Replicate API integration (`app/services/replicate_inference.py`)
  - [x] ReplicateInferenceService class with async methods
  - [x] Image processing via Replicate API
  - [x] Support for multiple output formats (URLs, data URIs, bytes, FileOutput)
  - [x] FileOutput handling with async `.aread()` method
  - [x] Comprehensive error handling (rate limits, timeouts, model errors)
  - [x] Custom exception classes (ReplicateRateLimitError, ReplicateTimeoutError, etc.)
- [x] Add `provider` field to model configuration schema
  - [x] Update ModelInfo schema with provider field (Literal["huggingface", "replicate"])
  - [x] Validate provider in config validation
  - [x] Default to "huggingface" for backward compatibility
- [x] Update restoration route with provider routing
  - [x] Detect provider from model configuration
  - [x] Route to appropriate inference service (HF or Replicate)
  - [x] Unified error handling for both providers
- [x] Configuration updates
  - [x] Add `REPLICATE_API_TOKEN` to settings
  - [x] Format `MODELS_CONFIG` as multi-line in `.env.example`
  - [x] Add detailed schema documentation with provider field
  - [x] Add example Replicate model (flux-kontext-apps/restore-image)
- [x] Dependencies
  - [x] Add `replicate==1.0.7` to requirements.txt

**Initial Replicate Model:**
- [x] flux-kontext-apps/restore-image
  - Category: restore
  - Advanced photo restoration using Replicate AI
  - Supports old photo restoration with artifact removal

**Documentation:**
- [x] Update README.md with Replicate provider information
  - [x] Add Replicate API token to prerequisites
  - [x] Update tech stack section
  - [x] Add MODELS_CONFIG configuration instructions
- [x] Update ROADMAP.md with Phase 1.8.1

**Tests:**
- [x] Create requirements.txt validation tests (`backend/tests/test_requirements.py`) - 14 tests ✅
  - [x] Validate all package versions are correct
  - [x] Verify replicate package is present with correct stable version (1.0.7)
  - [x] Ensure no duplicate packages
  - [x] Verify bcrypt version constraint for passlib compatibility
  - [x] Test all critical packages are present
  - [x] Validate version specifiers use valid operators
  - [x] Test package importability (replicate, huggingface-hub, fastapi)

**Completed:** December 17, 2024

**Implementation Issues and Fixes:**
1. **Replicate version error** (Fixed)
   - Error: `replicate==1.7.0` version not found during Docker build
   - Fix: Corrected to stable version `replicate==1.0.7`

2. **Docker multi-line environment variable** (Fixed)
   - Error: `docker: invalid env file: variable contains whitespaces`
   - Fix: Converted MODELS_CONFIG to single-line JSON format for Docker compatibility
   - Created helper script `format_models_config.py` for format conversions

3. **Replicate input parameter name** (Fixed)
   - Error: `ReplicateError: input_image is required` (API 422 validation error)
   - Fix: Added configurable `input_param_name` field to model config
   - Updated replicate_inference.py to use `model_config.get("input_param_name", "image")`

4. **FileOutput type handling** (Fixed)
   - Error: `Unexpected output type: <class 'replicate.helpers.FileOutput'>`
   - Fix: Added FileOutput handling with async `.aread()` method
   - FileOutput is a special object that streams file data from Replicate API

**Benefits:**
- Multi-provider architecture allows using best models from different platforms
- Easy to add more providers in the future (OpenAI, Stability AI, etc.)
- Maintains backward compatibility with existing HuggingFace models
- Flexible model configuration with per-model input parameter names
- Comprehensive error handling for both providers
- Docker-compatible single-line JSON format with helper conversion script

---

### 1.8.2 Configuration System Refactoring ✅ **COMPLETE**

**Goal:** Move backend configuration from `.env` file to structured JSON files for better maintainability, easier Docker deployment, and improved configuration management.

**Backend:**
- [x] Create config directory structure (`backend/config/`)
  - [x] `default.json` - Base configuration with all defaults
  - [x] `development.json.example` - Development environment example
  - [x] `production.json.example` - Production environment example
  - [x] `staging.json.example` - Staging environment example
  - [x] `testing.json` - Test configuration (committed to git)
  - [x] `README.md` - Config directory documentation
- [x] Create Pydantic configuration schemas (`app/core/config_schema.py`)
  - [x] ApplicationConfig, ServerConfig, CorsConfig
  - [x] SecurityConfig, ApiProvidersConfig (HuggingFace, Replicate)
  - [x] ModelConfig with full validation
  - [x] DatabaseConfig, FileStorageConfig, SessionConfig, ProcessingConfig
  - [x] ConfigFile - Complete configuration schema
- [x] Update configuration loader (`app/core/config.py`)
  - [x] JSON config file loading with deep merge
  - [x] Environment-specific config support (dev, prod, staging, testing)
  - [x] Backward compatibility with .env-only approach
  - [x] Deprecation warnings for old format
  - [x] Environment variable overrides (highest priority)
  - [x] `is_using_json_config()` method
- [x] Create utility scripts (`backend/scripts/`)
  - [x] `migrate_env_to_config.py` - Migrate .env to JSON config
  - [x] `validate_config.py` - Validate config files against schemas
  - [x] `generate_config_docs.py` - Auto-generate documentation
- [x] Update Docker configuration
  - [x] Dockerfile - Copy config files to container
  - [x] docker-compose.yml - Mount config directory as volume (read-only)
- [x] Update environment files
  - [x] `.env.example` - Simplified to secrets only
  - [x] `.gitignore` - Ignore runtime config files (not examples)
- [x] Create comprehensive tests
  - [x] `test_config_loading.py` - Config loading, merging, fallback (25+ tests)
  - [x] `test_config_schema.py` - Schema validation (25+ tests)

**Configuration Split:**
- **Secrets (in `.env`)**: HF_API_KEY, REPLICATE_API_TOKEN, SECRET_KEY, AUTH_USERNAME, AUTH_PASSWORD, APP_ENV
- **Configuration (in `config/*.json`)**: All application, server, CORS, models, database, file storage, session, and processing settings

**Loading Priority:**
1. Environment variables (`.env` file) - HIGHEST
2. Environment-specific config (`config/{APP_ENV}.json`)
3. Default config (`config/default.json`) - LOWEST

**Benefits:**
- No more single-line JSON escaping issues for MODELS_CONFIG
- Human-readable multi-line JSON format
- Docker persistence - update config without rebuilding containers
- Environment-specific configurations (dev/prod/staging)
- Backward compatible - .env-only still works (with deprecation warning)
- Comprehensive validation with Pydantic schemas
- Migration and validation scripts for safety
- Auto-generated documentation

**Documentation:**
- Config directory README with usage instructions
- Auto-generated configuration reference (via script)
- Migration guide from .env to JSON config

**Completed:** December 17, 2024

**Future Enhancements (Phase 5):**
- Configuration UI for web-based management
- Config hot reload API endpoint
- Config versioning system
- Full deprecation of .env-only approach

---

### 1.9 Testing & Quality Assurance ✅ **COMPLETE**

**Note:** Most backend tests are already complete from phases 1.1-1.8.1. This phase focuses on any remaining test coverage gaps and frontend test infrastructure.

**Backend Test Status:**
- [x] 279 tests passing (from phases 1.1-1.8.1) ✅
- [x] Configuration tests - 21 tests ✅
- [x] Health & startup tests - 21 tests ✅
- [x] Auth tests - 24 tests ✅
- [x] Security tests - 29 tests ✅
- [x] Models API tests - 17 tests ✅
- [x] HF Inference service tests - 23 tests ✅
- [x] Image utilities tests - 37 tests ✅
- [x] Database model tests - 11 tests ✅
- [x] Database setup tests - 19 tests ✅
- [x] Session manager tests - 29 tests ✅
- [x] Restoration API tests - 61 tests ✅
- [x] Requirements validation tests - 14 tests ✅
- [x] New config system tests - 50+ tests ✅ (Phase 1.8.2)

**Backend Test Infrastructure:**
- [x] pytest configuration complete ✅
- [x] Test fixtures and utilities (`conftest.py`) ✅
- [x] Test environment (`.env.test`) ✅
- [x] Test data and mocks ✅
- [x] Coverage reporting (99% coverage) ✅

**Backend - Completed in Phase 1.9:**
- [x] Update existing tests for new config system compatibility ✅
  - Updated `config/testing.json` to work with new system
  - Verified 234+ tests passing
- [x] Comprehensive DEBUG logging implemented ✅
  - Controlled by DEBUG environment variable
  - Detailed logging in all services and routes
  - Documentation: `docs/DEBUG_LOGGING.md`
- [ ] Add integration tests for config migration scripts (Deferred to Phase 2+)
- [ ] Test config hot reload functionality (when implemented in Phase 5)

**Frontend Test Status:**
- [x] 224 tests passing ✅
- [x] Auth tests - 55 tests ✅
- [x] Restoration feature tests - 40 tests ✅
- [x] History feature tests - 20 tests ✅
- [x] Shared component tests - 82 tests ✅
- [x] Layout tests - 12 tests ✅
- [x] Accessibility tests - 15 tests ✅

**Frontend Test Infrastructure:**
- [x] Vitest configuration ✅
- [x] Test setup and utilities ✅
- [x] Mock API client ✅
- [x] Test data fixtures ✅

**Frontend - Remaining Tasks:**
- [ ] Add tests for any new features in Phase 2+
- [ ] Maintain test coverage as new components are added

**Test Coverage Goals:**
- [x] Backend: ≥70% code coverage ✅ (Currently 99%)
- [x] Frontend: ≥60% code coverage ✅
- [x] All auth flows tested ✅
- [x] All API endpoints tested ✅
- [x] All error scenarios tested ✅

**Test Automation:**
- [x] npm script: `"test:coverage": "vitest run --coverage"` ✅
- [x] npm script: `"test:watch": "vitest"` ✅
- [x] Backend script: `pytest --cov=app --cov-report=html` ✅
- [ ] Setup CI/CD pipeline (GitHub Actions)
  - [ ] Run backend tests on PR
  - [ ] Run frontend tests on PR
  - [ ] Report coverage
  - [ ] Fail PR if tests fail

---

### 1.10 Documentation & Deployment ✅ **COMPLETE**

**Note:** Most documentation is complete from phases 1.1-1.8.2. This phase focuses on final polish and deployment guides.

**Documentation Status:**
- [x] README.md with project description ✅
- [x] Features list ✅
- [x] Tech stack details ✅
- [x] Setup instructions (Docker & local dev) ✅
- [x] Environment variables documentation ✅
- [x] ROADMAP.md with detailed development plan ✅
- [x] Configuration documentation (Phase 1.8.2) ✅
  - [x] Config directory README
  - [x] Migration guide (.env to JSON)
  - [x] Auto-generated config reference (script available)

**Documentation - Completed in Phase 1.10:**
- [x] Generate complete configuration reference ✅
  - [x] Generated: `docs/configuration.md` (auto-generated from schema)
- [x] Create API documentation ✅
  - [x] Enhanced FastAPI auto-generated docs (`/api/docs`)
  - [x] Added detailed descriptions to all endpoints
  - [x] Added request/response examples
  - [x] Added error response documentation
- [x] Create deployment guide ✅
  - [x] Comprehensive deployment guide: `docs/DEPLOYMENT_GUIDE.md`
  - [x] Docker Compose deployment steps
  - [x] nginx configuration details
  - [x] SSL/HTTPS setup guide (Let's Encrypt)
  - [x] Environment variable configuration
  - [x] Configuration file management in Docker
  - [x] Multi-environment deployment (dev/staging/prod)
  - [x] Troubleshooting section
  - [x] Security best practices
  - [x] Scaling & performance guidance
- [x] DEBUG logging documentation ✅
  - [x] Created: `docs/DEBUG_LOGGING.md`
  - [x] Usage examples and security notes

**Docker Deployment:**
- [x] Docker Compose stack works ✅
- [x] nginx reverse proxy routing ✅
- [x] Backend API through proxy ✅
- [x] Frontend static serving ✅
- [x] File upload/download through proxy ✅
- [x] Database persistence (volume mounts) ✅
- [x] Config persistence (volume mounts) ✅ (Phase 1.8.2)
- [x] Docker images optimized (multi-stage builds) ✅
- [x] Health check endpoints ✅
  - [x] Backend: GET `/health` ✅
  - [x] Frontend: nginx status ✅

**Production Readiness:**
- [x] Logging configuration ✅
  - [x] Backend: structured JSON logs
  - [x] Frontend: error tracking
- [ ] Add monitoring hooks
  - [x] Health endpoints ✅
  - [ ] Metrics endpoints (optional)
- [x] Security hardening ✅
  - [x] CORS configuration ✅
  - [ ] Rate limiting (planned for Phase 2.2)
  - [x] Input sanitization ✅
  - [x] File upload size limits ✅
- [ ] Performance optimization
  - [x] Image compression ✅
  - [ ] Response caching headers
  - [ ] Gzip compression in nginx


---

## Phase 2: Pipeline Processing & Enhanced Features

### 2.1 Model Pipeline System

**Backend:**
- [ ] Design pipeline architecture
  - [ ] Define pipeline configuration format (JSON/YAML)
  - [ ] Pipeline execution engine
  - [ ] Step-by-step processing with intermediate results
- [ ] Create pipeline service
  - [ ] Sequential model application
  - [ ] Save intermediate results
  - [ ] Progress tracking for each step
- [ ] Add pipeline routes
  - [ ] POST `/api/v1/restore/pipeline` - execute pipeline
  - [ ] GET `/api/v1/pipelines` - list predefined pipelines
  - [ ] GET `/api/v1/restore/pipeline/{job_id}/progress` - get progress
- [ ] Predefined pipelines
  - [ ] "Quick Restore": Qwen cleanup → Swin2SR 2x
  - [ ] "High Quality": Qwen cleanup → Swin2SR 4x → SDXL Refiner (if added)
  - [ ] Custom pipeline builder

**Frontend:**
- [ ] Pipeline builder UI
  - [ ] Drag-and-drop pipeline creator
  - [ ] Model step selector
  - [ ] Pipeline preview
  - [ ] Save custom pipelines
- [ ] Pipeline execution UI
  - [ ] Step-by-step progress visualization
  - [ ] Intermediate result preview
  - [ ] Pause/resume functionality
  - [ ] View all pipeline outputs

---

### 2.2 Rate Limiting & API Protection

**Note:** Basic concurrent upload limiting per session was implemented in Phase 1.6 (MAX_CONCURRENT_UPLOADS_PER_SESSION). This phase will add comprehensive rate limiting across all endpoints.

**Backend:**
- [ ] Implement rate limiting middleware
  - [ ] Per-IP rate limits for public endpoints
  - [ ] Per-user rate limits for authenticated endpoints
  - [ ] Configurable limits via environment variables
  - [ ] Different limits for different endpoint categories:
    - [ ] Models list/details: Higher limits (e.g., 100/minute)
    - [ ] Image restoration: Lower limits (e.g., 10/minute)
    - [ ] Authentication: Strict limits (e.g., 5/minute for login)
- [ ] Add rate limit headers to responses
  - [ ] `X-RateLimit-Limit`: Maximum requests allowed
  - [ ] `X-RateLimit-Remaining`: Requests remaining in window
  - [ ] `X-RateLimit-Reset`: Time when limit resets
  - [ ] `Retry-After`: Seconds to wait when rate limited
- [ ] Implement rate limit storage
  - [ ] Redis backend for distributed rate limiting (production)
  - [ ] In-memory fallback for single-instance deployments
- [ ] Custom rate limit responses
  - [ ] HTTP 429 (Too Many Requests) with clear message
  - [ ] Include information about limits and reset time

**Tests:**
- [ ] Rate limiting tests (`backend/tests/middleware/test_rate_limiting.py`)
  - [ ] Test rate limit enforcement
  - [ ] Test rate limit headers are present
  - [ ] Test per-IP and per-user limits
  - [ ] Test different limits for different endpoints
  - [ ] Test rate limit reset behavior

**Configuration:**
```env
# Rate Limiting (requests per time window)
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MODELS=100/minute
RATE_LIMIT_RESTORE=10/minute
RATE_LIMIT_AUTH=5/minute
RATE_LIMIT_STORAGE=redis  # redis or memory
REDIS_URL=redis://localhost:6379/0
```

---

### 2.3 Batch Processing

**Backend:**
- [ ] Implement batch processing service
  - [ ] Queue system (Celery or simple async queue)
  - [ ] Batch job management
  - [ ] Progress tracking per image
  - [ ] Background processing
- [ ] Add batch routes
  - [ ] POST `/api/v1/restore/batch` - upload multiple images
  - [ ] GET `/api/v1/restore/batch/{batch_id}` - get batch status
  - [ ] GET `/api/v1/restore/batch/{batch_id}/download` - download all as zip

**Frontend:**
- [ ] Batch upload UI
  - [ ] Multi-file selector
  - [ ] Bulk progress display
  - [ ] Individual image status
  - [ ] Batch download (zip)
- [ ] Queue management UI
  - [ ] View queued jobs
  - [ ] Cancel jobs
  - [ ] Reorder queue

---

### 2.4 Enhanced Authentication Features ✅ **COMPLETE**

**Completed:** December 22, 2024

**Backend:** ✅ **COMPLETE** (December 21, 2024)
**Frontend:** ✅ **COMPLETE** (December 22, 2024)
- [x] Database-backed user management (replace hardcoded credentials)
  - [x] User table in SQLite with full authentication fields
    - [x] username, email, full_name, hashed_password
    - [x] role (admin/user), is_active, password_must_change
    - [x] created_at, last_login timestamps
  - [x] Session table updated with user_id foreign key (CASCADE delete)
  - [x] CRUD operations for users (admin-only)
  - [x] Admin user management endpoints (`/api/v1/admin/*`)
    - [x] POST `/admin/users` - Create new user
    - [x] GET `/admin/users` - List users with pagination & filters
    - [x] GET `/admin/users/{id}` - Get user details
    - [x] PUT `/admin/users/{id}` - Update user
    - [x] DELETE `/admin/users/{id}` - Delete user
    - [x] PUT `/admin/users/{id}/reset-password` - Reset password
- [x] Enhanced password security
  - [x] Password complexity requirements (min 8 chars, uppercase, lowercase, digit)
  - [x] Password validation utilities (`app/utils/password_validator.py`)
  - [x] Bcrypt password hashing (existing, now with DB storage)
  - [x] Password change functionality (`PUT /api/v1/users/me/password`)
  - [x] Force password change on first login (`password_must_change` flag)
- [x] Session management improvements
  - [x] Multiple device support (multiple sessions per user)
  - [x] Active session viewing (`GET /api/v1/users/me/sessions`)
  - [x] Remote logout capability (`DELETE /api/v1/users/me/sessions/{id}`)
  - [x] Sessions linked to users (not anonymous)
  - [x] Cross-session history access (users see ALL their images)
- [x] Role-based authorization
  - [x] Admin role (can manage users)
  - [x] User role (can only use the app)
  - [x] Authorization middleware (`require_admin`)
- [x] Database seeding
  - [x] Auto-create admin user from environment variables
  - [x] Case-insensitive username lookup (idempotent seeding)
  - [x] Credentials normalization (lowercase usernames/emails)
- [x] User profile endpoints (`/api/v1/users/*`)
  - [x] GET `/users/me` - Get current user profile
  - [x] PUT `/users/me/password` - Change own password
  - [x] GET `/users/me/sessions` - List active sessions
  - [x] DELETE `/users/me/sessions/{id}` - Delete session
- [x] Updated authentication flow
  - [x] JWT tokens include user_id, role, password_must_change
  - [x] Login creates new session linked to user
  - [x] Last login timestamp tracking
  - [x] Remember Me functionality (7 days vs 24 hours)

**Frontend:** ✅ **COMPLETE**
- [x] Admin panel page (`/admin/users`)
  - [x] User list with pagination (20 users per page)
  - [x] Filters: Role (All/Admin/User), Status (All/Active/Inactive)
  - [x] Create user dialog with password generation
  - [x] Edit user dialog (email, full_name, role, is_active)
  - [x] Delete user confirmation modal
  - [x] Reset password dialog with password generation
  - [x] Role assignment dropdown
  - [x] Activate/deactivate user toggle
  - [x] AdminRoute wrapper (role-based access control)
  - [x] Admin nav link (only visible to admins)
  - [x] Responsive design for mobile/tablet
  - [x] Prevents admin from deleting self
- [x] Profile management page (`/profile`)
  - [x] View user profile information
  - [x] Change password form with validation
  - [x] Active sessions viewer with device info
  - [x] Remote logout functionality (delete other sessions)
  - [x] Profile information display (username, email, full name, role)
  - [x] Responsive design
- [x] Updated history page
  - [x] Show ALL user images across sessions
  - [x] Session filter dropdown (All Sessions / specific session)
  - [x] Maintain existing pagination
  - [x] Updated UI with session metadata

**Breaking Changes:**
- Database schema changed (User table added, Session table updated)
- Must delete old database: `rm backend/data/photo_restoration.db*`
- New environment variables required:
  - `AUTH_EMAIL` - Admin user email
  - `AUTH_FULL_NAME` - Admin user full name
- Sessions now require user authentication (no more anonymous sessions)

**Migration Guide:**
1. Update `.env` file with new admin credentials (AUTH_EMAIL, AUTH_FULL_NAME)
2. Delete old database: `rm -f backend/data/photo_restoration.db*`
3. Start backend - admin user will be auto-created
4. Login with admin credentials from `.env`
5. Create additional users via admin panel (once frontend is implemented)

**Files Created (Backend):**
- `backend/app/db/seed.py` - Database seeding utilities
- `backend/app/utils/password_validator.py` - Password validation
- `backend/app/core/authorization.py` - Role-based authorization
- `backend/app/api/v1/schemas/user.py` - User schemas
- `backend/app/api/v1/routes/admin.py` - Admin user management
- `backend/app/api/v1/routes/users.py` - User profile management

**Files Modified (Backend):**
- `backend/app/db/models.py` - Added User model, updated Session
- `backend/app/db/database.py` - Added seeding on init
- `backend/app/core/config.py` - Added AUTH_EMAIL, AUTH_FULL_NAME
- `backend/app/core/security.py` - Database-backed authentication
- `backend/app/api/v1/routes/auth.py` - Updated login flow
- `backend/app/api/v1/routes/restoration.py` - User-based history
- `backend/app/services/session_manager.py` - Accept user_id parameter
- `backend/app/main.py` - Registered new routes
- `backend/.env.example` - Added new environment variables

**Files Created (Frontend):**
- `frontend/src/features/admin/types.ts` - Admin types
- `frontend/src/features/admin/services/adminService.ts` - Admin API service
- `frontend/src/features/admin/hooks/useAdminUsers.ts` - Admin users hook
- `frontend/src/features/admin/components/UserList.tsx` - User list table
- `frontend/src/features/admin/components/CreateUserDialog.tsx` - Create user dialog
- `frontend/src/features/admin/components/EditUserDialog.tsx` - Edit user dialog
- `frontend/src/features/admin/components/DeleteUserDialog.tsx` - Delete confirmation
- `frontend/src/features/admin/components/ResetPasswordDialog.tsx` - Reset password dialog
- `frontend/src/features/admin/pages/AdminUsersPage.tsx` - Admin page
- `frontend/src/features/profile/types.ts` - Profile types
- `frontend/src/features/profile/services/profileService.ts` - Profile API service
- `frontend/src/features/profile/hooks/useProfile.ts` - Profile hook
- `frontend/src/features/profile/components/ProfileView.tsx` - Profile view
- `frontend/src/features/profile/components/ChangePasswordForm.tsx` - Password form
- `frontend/src/features/profile/components/SessionsList.tsx` - Sessions list
- `frontend/src/features/profile/pages/ProfilePage.tsx` - Profile page
- `frontend/src/components/AdminRoute.tsx` - Admin route wrapper
- `frontend/src/styles/components/admin.css` - Admin panel styling
- `frontend/src/styles/components/profile.css` - Profile page styling

**Files Modified (Frontend):**
- `frontend/src/features/auth/types.ts` - Added role to User interface
- `frontend/src/features/auth/hooks/useAuth.ts` - Added JWT token decoder
- `frontend/src/features/history/pages/HistoryPage.tsx` - Added session filter
- `frontend/src/features/history/hooks/useHistory.ts` - Updated for cross-session history
- `frontend/src/components/Button.tsx` - Added danger variant
- `frontend/src/components/Layout.tsx` - Added Admin/Profile nav links
- `frontend/src/app/App.tsx` - Added admin/profile routes

**Code Review Fixes (December 22, 2024):**
- ✅ [HIGH] Fixed insecure password generation (crypto.getRandomValues)
- ✅ [MEDIUM] Fixed pagination bug after user deletion
- ✅ [LOW] Fixed sensitive data leak in dialog forms
- ✅ Type safety improvements (replaced `any` with proper types)

**Testing Status:**
- ✅ Code review passed (all issues resolved)
- ✅ Frontend build successful (no TypeScript errors)
- ⏳ Unit tests for new features pending (added to TECHNICAL_DEBTS.md)
- ⏳ Integration tests pending
- ⏳ End-to-end tests pending

**Documentation:**
- ✅ ROADMAP.md updated
- ✅ TECHNICAL_DEBTS.md updated with Phase 2.4 completion
- ⏳ API documentation pending
- ⏳ Frontend component documentation pending

---

### 2.5 Additional Models

**Add More Models:**
- [ ] Stable Diffusion X4 Upscaler (`stabilityai/stable-diffusion-x4-upscaler`)
- [ ] Instruct-Pix2Pix (`timbrooks/instruct-pix2pix`)
- [ ] PMRF Face Restoration (`ohayonguy/PMRF_blind_face_image_restoration`)
- [ ] ControlNet Tile models
- [ ] SDXL Refiner (`stabilityai/stable-diffusion-xl-refiner-1.0`)

**Model Categories:**
- [ ] Upscaling models
- [ ] Enhancement models
- [ ] Face restoration models
- [ ] Specialized models (watermark removal, etc.)

---

### 2.6 Advanced Image Controls

**Backend:**
- [ ] Add preprocessing options
  - [ ] Crop/rotate before processing
  - [ ] Color correction
  - [ ] Brightness/contrast adjustment
- [ ] Add model parameters configuration
  - [ ] Custom prompts for Qwen/Instruct-Pix2Pix
  - [ ] Guidance scale
  - [ ] Number of inference steps
  - [ ] Custom parameters per model

**Frontend:**
- [ ] Image editor component
  - [ ] Crop tool
  - [ ] Rotate/flip
  - [ ] Basic adjustments
- [ ] Advanced model parameters UI
  - [ ] Prompt input for prompt-based models
  - [ ] Slider controls for numeric parameters
  - [ ] Presets for common use cases

---

### 2.7 Performance & Optimization

**Backend:**
- [ ] Implement result caching
  - [ ] Cache processed images by hash
  - [ ] Avoid reprocessing identical images
- [ ] Add image optimization
  - [ ] Compress uploads before sending to HF
  - [ ] Optimize processed images for web
  - [ ] Multiple quality/size options
- [ ] Database optimization
  - [ ] Add indexes for common queries
  - [ ] Implement pagination for history
  - [ ] Archive old sessions

**Frontend:**
- [ ] Lazy loading for history
- [ ] Image lazy loading
- [ ] Virtual scrolling for long lists
- [ ] Code splitting by route
- [ ] Asset optimization (image formats, compression)

---

## Phase 3: OwnCloud Integration & Advanced Features

### 3.1 OwnCloud WebDAV Integration

**Backend:**
- [ ] Add WebDAV client service
  - [ ] Connect to OwnCloud via WebDAV
  - [ ] Authenticate with user credentials
  - [ ] List files/folders
  - [ ] Download files
  - [ ] Upload files
- [ ] OwnCloud configuration
  - [ ] User provides OwnCloud URL
  - [ ] User provides credentials (encrypted storage)
  - [ ] Test connection endpoint
- [ ] Add OwnCloud routes
  - [ ] POST `/api/v1/owncloud/connect` - connect to OwnCloud
  - [ ] GET `/api/v1/owncloud/browse` - browse folders
  - [ ] POST `/api/v1/owncloud/import` - import image from OwnCloud
  - [ ] POST `/api/v1/owncloud/export` - export processed image to OwnCloud

**Frontend:**
- [ ] OwnCloud connection UI
  - [ ] Connection form (URL, credentials)
  - [ ] Test connection button
  - [ ] Save connection in session
- [ ] OwnCloud file browser
  - [ ] Folder tree navigation
  - [ ] File selection
  - [ ] Import to restoration tool
- [ ] Export functionality
  - [ ] Select destination folder
  - [ ] Export processed images
  - [ ] Batch export support

**Security:**
- [ ] Encrypt OwnCloud credentials
- [ ] Session-based credential storage
- [ ] OAuth2 support (if available)

---

### 3.2 User Management & Multi-User Support

**Backend:**
- [ ] Full user registration system
  - [ ] User signup endpoint
  - [ ] Email verification (optional)
  - [ ] Password reset flow
- [ ] User profile management
  - [ ] Update profile
  - [ ] Change password
  - [ ] API key management
- [ ] User-specific data isolation
  - [ ] Separate sessions per user
  - [ ] User quotas (storage, API calls)
  - [ ] Usage statistics

**Frontend:**
- [ ] Registration page
- [ ] Profile page
- [ ] User settings
- [ ] Usage dashboard

---

### 3.3 Advanced Features

**Animations/Video Frame Restoration:**
- [ ] Video upload support
- [ ] Frame extraction
- [ ] Batch frame processing
- [ ] Frame reassembly with ffmpeg
- [ ] Video export

**AI-Powered Suggestions:**
- [ ] Analyze image and suggest best model
- [ ] Auto-detect degradation type
- [ ] Recommend pipeline based on image type

**Collaboration Features:**
- [ ] Share processed images (public links)
- [ ] Create albums/collections
- [ ] Export albums as gallery

**Preset Workflows:**
- [ ] One-click restoration profiles
  - [ ] "Old Family Photo"
  - [ ] "Scanned Document"
  - [ ] "Portrait Enhancement"
  - [ ] "Landscape Photo"
- [ ] Custom preset creation
- [ ] Community presets (share/import)

---

## Phase 5: Advanced Configuration Management 🔮 **PLANNED**

### 5.1 Configuration UI & Hot Reload

**Goal:** Provide web-based configuration management with live updates

**Backend:**
- [ ] Configuration management API endpoints
  - [ ] GET `/admin/config` - Get current configuration
  - [ ] POST `/admin/config/reload` - Manually trigger config reload
  - [ ] POST `/admin/config/validate` - Validate config before applying
  - [ ] GET `/admin/config/history` - View config change history
- [ ] Config hot reload implementation
  - [ ] File watcher for config file changes
  - [ ] Safe reload with validation
  - [ ] Rollback on validation failure
  - [ ] Graceful handling of reload failures
  - [ ] Reload only safe-to-reload values (exclude DB URL, server port, etc.)
- [ ] Config change notifications
  - [ ] WebSocket notifications for config changes
  - [ ] Audit log for config modifications
  - [ ] Admin alerts on config errors

**Frontend:**
- [ ] Configuration management UI
  - [ ] Web-based config editor with JSON/form view
  - [ ] Real-time validation as you edit
  - [ ] Preview changes before applying
  - [ ] Rollback to previous versions
  - [ ] Config diff viewer
- [ ] Admin dashboard
  - [ ] Current configuration display
  - [ ] Reload config button
  - [ ] Config validation status
  - [ ] Change history timeline

**Tests:**
- [ ] Config hot reload tests
  - [ ] Test file watcher triggers reload
  - [ ] Test validation before reload
  - [ ] Test rollback on failure
  - [ ] Test safe vs unsafe config changes
- [ ] Config UI API tests
  - [ ] Test all admin endpoints
  - [ ] Test authorization (admin only)
  - [ ] Test validation errors

---

### 5.2 Configuration Versioning

**Goal:** Track and manage configuration versions over time

**Backend:**
- [ ] Add `config_version` field to ConfigFile schema
- [ ] Automatic config migration system
  - [ ] Detect config version on load
  - [ ] Apply migrations to upgrade to current version
  - [ ] Support downgrade migrations
- [ ] Config version compatibility checking
  - [ ] Warn if config version doesn't match app version
  - [ ] Provide migration path
- [ ] Config backup and restore
  - [ ] Automatic backups before changes
  - [ ] Restore from backup
  - [ ] Backup retention policy

**Scripts:**
- [ ] Config upgrade script
  - [ ] Upgrade config from v1.x to v2.x
  - [ ] Handle breaking changes gracefully
- [ ] Config diff tool
  - [ ] Compare configs between environments
  - [ ] Highlight differences
  - [ ] Merge configs

**Documentation:**
- [ ] Config version changelog
- [ ] Migration guide for each version
- [ ] Breaking changes documentation

---

### 5.3 Full Deprecation of .env-only Configuration

**Goal:** Remove backward compatibility for .env-only configuration

**Breaking Changes:**
- [ ] Remove .env-only fallback from config.py
- [ ] Make config/*.json files mandatory
- [ ] Remove deprecation warnings (no longer needed)
- [ ] Update all documentation

**Migration Support:**
- [ ] Enhanced migration script with auto-detection
- [ ] Pre-migration validation
- [ ] Dry-run mode
- [ ] Automated testing of migrated configs

**Communication:**
- [ ] Publish migration guide
- [ ] Add migration deadline to documentation
- [ ] Email notifications to users (if applicable)
- [ ] Clear error messages directing to migration script

**Completed Tasks:**
- [ ] All users migrated to JSON config
- [ ] Old .env-only tests removed
- [ ] Cleanup of backward compatibility code

---

### 5.4 Advanced Configuration Features

**Configuration Templates:**
- [ ] Pre-built configuration templates
  - [ ] Development template
  - [ ] Production template
  - [ ] High-performance template
  - [ ] Security-focused template
- [ ] Template customization wizard
- [ ] Import/export configurations

**Configuration Validation:**
- [ ] Enhanced validation rules
  - [ ] Cross-field validation
  - [ ] Environment-specific validation
  - [ ] Performance impact warnings
- [ ] Configuration testing framework
  - [ ] Test configs before deployment
  - [ ] Simulate config changes
  - [ ] Performance benchmarks

**Configuration Documentation:**
- [ ] Interactive configuration guide
- [ ] Configuration best practices
- [ ] Troubleshooting guide
- [ ] Performance tuning guide

---

## Phase 4: Polish & Production

### 4.1 UI/UX Improvements

- [ ] Add animations and transitions (subtle, Material-inspired)
- [ ] Improve loading states
- [ ] Add tooltips and onboarding
- [ ] Keyboard shortcuts
- [ ] Dark mode support
- [ ] Accessibility audit (WCAG AA)
- [ ] Mobile app wrapper (PWA or React Native)

---

### 4.2 Performance & Scalability

- [ ] Redis caching layer
- [ ] Message queue for long-running tasks (RabbitMQ/Redis)
- [ ] CDN integration for static assets
- [ ] Database migrations (Alembic)
- [ ] Horizontal scaling support
- [ ] Load balancing (multiple backend instances)

---

### 4.3 Monitoring & Analytics

- [ ] Application monitoring (Sentry, DataDog)
- [ ] Performance monitoring (APM)
- [ ] User analytics (privacy-focused)
- [ ] Error tracking and alerting
- [ ] Usage metrics dashboard

---

### 4.4 Security Hardening

- [ ] Penetration testing
- [ ] Security audit
- [ ] Rate limiting (per user, per endpoint)
- [ ] CAPTCHA for public endpoints
- [ ] Content Security Policy (CSP)
- [ ] Security headers (HSTS, X-Frame-Options)
- [ ] Regular dependency updates
- [ ] Vulnerability scanning

---

### 4.5 Documentation & Community

- [ ] User documentation
  - [ ] Getting started guide
  - [ ] Feature tutorials
  - [ ] FAQ
  - [ ] Troubleshooting guide
- [ ] Developer documentation
  - [ ] API reference (OpenAPI/Swagger)
  - [ ] Architecture documentation
  - [ ] Contributing guide
  - [ ] Code style guide
- [ ] Video tutorials
- [ ] Blog posts/case studies

---

## Technical Debt & Maintenance

### Ongoing Tasks

- [ ] Regular dependency updates
- [ ] Security patches
- [ ] Performance optimization
- [ ] Code refactoring
- [ ] Test coverage improvements
- [ ] Documentation updates
- [ ] User feedback implementation

---

## Success Metrics

### MVP Success Criteria (Phase 1 Complete):

**Functional Requirements:**
- [x] User can login with token ✅
- [x] Auth state persists (localStorage) ✅
- [x] Protected routes work ✅
- [x] "Remember Me" functionality (7 days) ✅
- [ ] User can upload an image
- [ ] User can select from 3 models
- [ ] Image is processed successfully via HF API
- [ ] User can view before/after comparison
- [ ] User can download processed image
- [ ] User can view session history
- [ ] Application runs in Docker with nginx

**Testing Requirements:**
- [x] Backend config tests ✅ (197 lines)
- [ ] Backend auth tests complete (login, validate, protected routes)
- [ ] Backend security utilities tests (JWT, password hashing)
- [ ] Backend health check tests
- [ ] Frontend auth tests complete (login form, hooks, store, protected routes)
- [ ] Frontend API client tests
- [ ] All image processing tests (when implemented in Phase 1.6)
- [ ] Test coverage: Backend ≥70%, Frontend ≥60%
- [ ] All error scenarios tested
- [ ] Security tests pass (no secrets leaked, CORS configured)

**Infrastructure Requirements:**
- [ ] pytest configuration complete (pytest.ini, conftest.py)
- [ ] Vitest configuration complete (vitest.config.ts, setup.ts)
- [ ] Test fixtures and mocks created
- [ ] Test data directory with sample images
- [ ] CI/CD pipeline runs tests automatically

**Documentation Requirements:**
- [x] README.md updated ✅
- [x] Environment variables documented ✅
- [ ] API documentation complete (Swagger/ReDoc)
- [ ] Test documentation (how to run, write tests)
- [ ] Deployment guide complete

### Phase 2 Success Criteria:
- [ ] Pipeline processing works end-to-end
- [ ] Batch processing handles 10+ images
- [ ] At least 5 models available
- [ ] Advanced controls improve results
- [ ] Pipeline tests complete (unit + integration)
- [ ] Batch processing tests complete
- [ ] Additional model integration tests
- [ ] Performance tests show acceptable speeds

### Phase 3 Success Criteria:
- [ ] OwnCloud integration works seamlessly
- [ ] Multi-user support is stable
- [ ] Video frame restoration works
- [ ] AI suggestions are accurate
- [ ] OwnCloud integration tests (mocked WebDAV)
- [ ] Multi-user isolation tests
- [ ] Video processing tests
- [ ] E2E tests cover all major user flows

---

## Notes

- All phases follow coding guidelines: AI.md, AI_FastAPI.md, AI_FRONTEND.md, AI_WEB_COMMON.md, AI_SQLite.md
- Design follows AI_WEB_DESIGN_SQOWE.md (sqowe brand)
- Always propose solution before implementation (CLAUDE.md)
- Keep files under 800 lines
- Use type hints (Python) and TypeScript (frontend)
- Comprehensive error handling
- Security-first approach
- Performance optimization at each phase
- **Test-Driven Development**: Write tests alongside features (follow tmp/TEST_STRATEGY_AI.md)
- **Test Coverage**: Minimum 70% backend, 60% frontend
- **All new code must have tests** - untested code is not allowed

---

**Last Updated:** December 17, 2024
**Current Phase:** Phase 1 - MVP (In Progress)
**Status:** Phase 1.1 Complete ✅ | Phase 1.2 Complete ✅ | Phase 1.3 Complete ✅ | Phase 1.4 Complete ✅ | Phase 1.5 Complete ✅ | Phase 1.6 Complete ✅ | Phase 1.7 Complete ✅ | Phase 1.8 Complete ✅ | Phase 1.8.1 Complete ✅ | Phase 1.8.2 Complete ✅
