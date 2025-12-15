# Photo Restoration Webpage - Development Roadmap

## Project Overview

A web application for restoring old scanned photos using HuggingFace AI models with a clean, sqowe-branded interface.

**Tech Stack:**
- **Backend:** FastAPI (Python 3.13+)
- **Frontend:** Vite + React + TypeScript
- **Deployment:** Docker + Docker Compose + nginx reverse proxy
- **AI Models:** HuggingFace Inference API
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

### 1.6 Image Restoration API

**Backend:**
- [ ] Create restoration schemas in `app/api/v1/schemas/restoration.py`
  - [ ] RestoreRequest (model_id, file)
  - [ ] RestoreResponse (id, original_url, processed_url, model_id, timestamp)
  - [ ] HistoryResponse (list of ProcessedImage)
- [ ] Create restoration routes in `app/api/v1/routes/restoration.py`
  - [ ] POST `/api/v1/restore` - upload and process image
    - [ ] Validate authentication token
    - [ ] Validate image file
    - [ ] Create/get session
    - [ ] Call HF Inference service
    - [ ] Save original and processed images
    - [ ] Store metadata in database
    - [ ] Return processed image info
  - [ ] GET `/api/v1/restore/history` - get session history
  - [ ] GET `/api/v1/restore/{image_id}` - get specific processed image
  - [ ] GET `/api/v1/restore/{image_id}/download` - download processed image
  - [ ] DELETE `/api/v1/restore/{image_id}` - delete processed image
- [ ] Add background cleanup task
  - [ ] Delete sessions older than 24 hours
  - [ ] Delete associated files
- [ ] Add comprehensive error handling and logging
- [ ] Add API tests for all endpoints

**Static File Serving:**
- [ ] Configure FastAPI to serve uploaded/processed images
- [ ] Setup proper CORS headers
- [ ] Add security headers

**Tests for Phase 1.6:**
- [ ] Backend: Restoration validation tests (`backend/tests/api/v1/test_restore_validation.py`)
  - [ ] Upload valid JPEG within size limit → 200 + job_id
  - [ ] Upload valid PNG within size limit → 200 + job_id
  - [ ] Upload unsupported format (BMP, TXT) → 400 with error
  - [ ] Upload exceeds MAX_UPLOAD_SIZE → 413 or 400 with clear error
  - [ ] Upload corrupted image → 400 with "Invalid image data"
  - [ ] Upload without authentication → 401
  - [ ] Upload with expired token → 401
- [ ] Backend: Restoration model tests (`backend/tests/api/v1/test_restore_models.py`)
  - [ ] Request with valid model_id → calls correct HF model
  - [ ] Request with unknown model_id → 400 "Unknown model"
  - [ ] HF returns binary image → response is valid image (image/jpeg or image/png)
  - [ ] HF returns 429 rate limit → backend returns 503 with retry-after
  - [ ] HF network error → backend returns 502/503 "Model service unavailable"
  - [ ] Request timeout → backend returns error within timeout limit
  - [ ] Response includes all required fields (job_id, original_url, processed_url)
- [ ] Backend: Restoration API integration tests (`backend/tests/api/v1/test_restore_integration.py`)
  - [ ] Full restore flow: upload → process → save → return URLs
  - [ ] Original image saved to UPLOAD_DIR
  - [ ] Processed image saved to PROCESSED_DIR
  - [ ] Metadata stored in database
  - [ ] GET `/api/v1/restore/history` returns user's processed images
  - [ ] GET `/api/v1/restore/{image_id}` returns specific image
  - [ ] GET `/api/v1/restore/{image_id}/download` downloads processed image
  - [ ] DELETE `/api/v1/restore/{image_id}` deletes image and files
  - [ ] DELETE with wrong user → 403 Forbidden
- [ ] Backend: Background cleanup tests (`backend/tests/services/test_cleanup.py`)
  - [ ] Cleanup task deletes sessions older than SESSION_CLEANUP_HOURS
  - [ ] Cleanup task deletes associated files from filesystem
  - [ ] Cleanup task preserves recent sessions
  - [ ] Cleanup task handles missing files gracefully
- [ ] Backend: Static file serving tests (`backend/tests/test_static_files.py`)
  - [ ] GET `/uploads/{filename}` serves uploaded image
  - [ ] GET `/processed/{filename}` serves processed image
  - [ ] CORS headers are set correctly
  - [ ] Security headers are present

---

### 1.7 Frontend - Core Features

**Image Upload Feature:**
- [ ] Create restoration feature in `src/features/restoration/`
  - [ ] `components/ImageUploader.tsx` - drag & drop upload component
  - [ ] `components/ModelSelector.tsx` - model selection dropdown
  - [ ] `components/ImageComparison.tsx` - before/after slider
  - [ ] `components/ProcessingStatus.tsx` - loading state, progress
  - [ ] `hooks/useImageRestore.ts` - restoration logic
  - [ ] `services/restorationService.ts` - API calls
  - [ ] `types.ts` - restoration-related types
- [ ] Implement file validation on frontend
  - [ ] File type validation (jpg, png)
  - [ ] File size validation (max 10MB)
  - [ ] User-friendly error messages

**History Feature:**
- [ ] Create history feature in `src/features/history/`
  - [ ] `components/HistoryList.tsx` - list of processed images
  - [ ] `components/HistoryCard.tsx` - individual history item
  - [ ] `hooks/useHistory.ts` - fetch and manage history
  - [ ] `services/historyService.ts` - API calls
  - [ ] `types.ts` - history-related types
- [ ] Implement history UI
  - [ ] Thumbnail grid view
  - [ ] Click to view/compare
  - [ ] Download button
  - [ ] Delete button

**API Client:**
- [ ] Create API client in `src/services/apiClient.ts`
  - [ ] Typed HTTP methods (GET, POST, DELETE)
  - [ ] Auto-inject auth token from store
  - [ ] Error handling and user-friendly messages
  - [ ] File upload support with progress
- [ ] Configure base URL from environment
  - [ ] `VITE_API_BASE_URL=/api/v1`

**Tests for Phase 1.7:**
- [ ] Frontend: Test utilities setup
  - [ ] Create `frontend/src/test-utils/mockApiClient.ts` for mocked API calls
  - [ ] Create `frontend/src/test-utils/testData.ts` for test fixtures
  - [ ] Add mock file upload utilities
- [ ] Frontend: Image upload tests (`frontend/src/__tests__/imageUploader.test.tsx`)
  - [ ] ImageUploader renders drag & drop area
  - [ ] ImageUploader accepts file via file picker
  - [ ] ImageUploader accepts file via drag & drop
  - [ ] ImageUploader shows preview after file selection
  - [ ] ImageUploader rejects non-image files (shows error)
  - [ ] ImageUploader rejects files exceeding size limit
  - [ ] ImageUploader clears selection on cancel
- [ ] Frontend: Model selector tests (`frontend/src/__tests__/modelSelector.test.tsx`)
  - [ ] ModelSelector fetches and renders model list
  - [ ] ModelSelector displays model names and descriptions
  - [ ] ModelSelector allows model selection
  - [ ] ModelSelector highlights selected model
  - [ ] ModelSelector handles API error gracefully
- [ ] Frontend: Image restoration hook tests (`frontend/src/__tests__/useImageRestore.test.tsx`)
  - [ ] `uploadAndRestore()` uploads image and calls API
  - [ ] `uploadAndRestore()` shows loading state during processing
  - [ ] `uploadAndRestore()` returns processed image URL on success
  - [ ] `uploadAndRestore()` shows error on validation failure
  - [ ] `uploadAndRestore()` shows error on network failure
  - [ ] `uploadAndRestore()` handles HF service unavailable (503)
- [ ] Frontend: Restoration service tests (`frontend/src/__tests__/restorationService.test.tsx`)
  - [ ] `restoreImage()` sends multipart form data
  - [ ] `restoreImage()` includes model_id in request
  - [ ] `restoreImage()` includes auth token
  - [ ] `restoreImage()` handles 401 (redirects to login)
  - [ ] `restoreImage()` handles 400 (validation error)
  - [ ] `restoreImage()` handles 503 (service unavailable)
- [ ] Frontend: History tests (`frontend/src/__tests__/history.test.tsx`)
  - [ ] HistoryList fetches and displays processed images
  - [ ] HistoryCard shows thumbnail and metadata
  - [ ] HistoryCard allows clicking to view full image
  - [ ] HistoryCard has download button
  - [ ] HistoryCard has delete button
  - [ ] Delete removes item from list after confirmation
  - [ ] History handles empty state (no images processed)

---

### 1.8 Frontend - UI/UX Implementation

**Layout & Navigation:**
- [ ] Create app shell in `src/app/`
  - [ ] `App.tsx` - main app component with router
  - [ ] `Layout.tsx` - main layout with header/footer
  - [ ] `ProtectedRoute.tsx` - route guard component
- [ ] Create navigation component
  - [ ] Header with sqowe logo
  - [ ] Navigation menu
  - [ ] Logout button
  - [ ] Follow AI_WEB_DESIGN_SQOWE.md for styling

**Shared Components (sqowe branded):**
- [ ] Create shared components in `src/components/`
  - [ ] `Button.tsx` - primary, secondary, gradient variants
  - [ ] `Card.tsx` - light and dark variants
  - [ ] `Input.tsx` - form input component
  - [ ] `Loader.tsx` - loading spinner
  - [ ] `ErrorMessage.tsx` - error display component
  - [ ] `Modal.tsx` - modal dialog component
- [ ] All components follow sqowe design system:
  - [ ] Colors: #222222, #8E88A3, #5B5377, #B2B3B2
  - [ ] Typography: Montserrat font family
  - [ ] Spacing: 8px grid system
  - [ ] Border radius, shadows as per brand guide

**Styling Setup:**
- [ ] Create global styles in `src/styles/`
  - [ ] `base.css` - CSS variables, resets, tokens
  - [ ] `layout.css` - grid, containers, responsive utilities
  - [ ] `components/` - component-specific styles
  - [ ] `themes/` - light/dark theme support
- [ ] Import Montserrat from Google Fonts
- [ ] Setup responsive breakpoints
- [ ] Follow AI_WEB_COMMON.md (no inline styles, separation of concerns)

**Main Pages:**
- [ ] Login page (`/login`)
  - [ ] sqowe branded login form
  - [ ] Token authentication
  - [ ] Error handling
- [ ] Restoration page (`/`) - main application page
  - [ ] Model selector
  - [ ] Image uploader (drag & drop)
  - [ ] Processing status
  - [ ] Before/After comparison slider
  - [ ] Download button
- [ ] History page (`/history`)
  - [ ] Grid of processed images
  - [ ] Filter/search functionality
  - [ ] View, download, delete actions

**Responsive Design:**
- [ ] Mobile-first approach
- [ ] Tablet breakpoint (768px)
- [ ] Desktop breakpoint (1024px)
- [ ] Test on multiple devices

**Tests for Phase 1.8:**
- [ ] Frontend: Shared component tests (`frontend/src/__tests__/components/`)
  - [ ] Button component renders all variants (primary, secondary, gradient)
  - [ ] Button component handles onClick events
  - [ ] Card component renders light and dark variants
  - [ ] Input component handles value changes
  - [ ] Input component validates required fields
  - [ ] Loader component renders with correct animation
  - [ ] ErrorMessage component displays error text
  - [ ] Modal component opens and closes correctly
- [ ] Frontend: Layout tests (`frontend/src/__tests__/layout.test.tsx`)
  - [ ] Header renders with sqowe logo
  - [ ] Navigation menu renders correctly
  - [ ] Logout button triggers logout
  - [ ] Footer renders with correct content
  - [ ] Responsive layout works at mobile breakpoint (< 768px)
  - [ ] Responsive layout works at tablet breakpoint (768px - 1024px)
  - [ ] Responsive layout works at desktop breakpoint (> 1024px)
- [ ] Frontend: Page integration tests (`frontend/src/__tests__/pages/`)
  - [ ] RestorationPage renders all components correctly
  - [ ] RestorationPage: upload → select model → restore flow works
  - [ ] RestorationPage shows loading state during processing
  - [ ] RestorationPage shows before/after comparison on success
  - [ ] RestorationPage shows error message on failure
  - [ ] HistoryPage renders history list
  - [ ] HistoryPage allows viewing, downloading, deleting images
- [ ] Frontend: Accessibility tests
  - [ ] All interactive elements are keyboard accessible
  - [ ] ARIA labels are present on important elements
  - [ ] Color contrast meets WCAG AA standards
  - [ ] Focus indicators are visible

---

### 1.9 Testing & Quality Assurance 🔄 **IN PROGRESS**

**Backend Test Infrastructure:**
- [x] Basic pytest setup (pytest, pytest-asyncio installed)
- [x] One test file exists (`backend/tests/test_config.py`)
- [ ] Complete pytest configuration
  - [ ] Create `backend/pytest.ini` or `backend/pyproject.toml`
  - [ ] Configure test discovery, async mode, coverage
  - [ ] Add `pytest-cov` for coverage reporting
  - [ ] Add `pytest-mock` for better mocking
- [ ] Test fixtures and utilities
  - [ ] Create `backend/tests/conftest.py` with shared fixtures
  - [ ] Test FastAPI client fixture
  - [ ] Test database fixture (in-memory SQLite)
  - [ ] Mock HF API fixture
  - [ ] Test user credentials fixture
- [ ] Test environment configuration
  - [ ] Create `backend/.env.test` with test settings
  - [ ] Fixed SECRET_KEY for deterministic tokens
  - [ ] In-memory database URL
  - [ ] Test HF_API_KEY

**Backend Unit Tests:**
- [x] Configuration tests (`backend/tests/test_config.py`) ✅
- [ ] Health check tests (`backend/tests/test_health.py`)
- [ ] Security utilities tests (`backend/tests/services/test_security.py`)
- [ ] HF Inference service tests (`backend/tests/services/test_hf_inference.py`) - mocked
- [ ] Session manager tests (`backend/tests/services/test_session_manager.py`)
- [ ] Image processing utilities tests (`backend/tests/utils/test_image_processing.py`)
- [ ] Database models tests (`backend/tests/db/test_models.py`)
- [ ] Database setup tests (`backend/tests/db/test_database.py`)

**Backend Integration Tests:**
- [ ] Auth API tests (`backend/tests/api/v1/test_auth.py`)
- [ ] Models API tests (`backend/tests/api/v1/test_models.py`)
- [ ] Restore validation tests (`backend/tests/api/v1/test_restore_validation.py`)
- [ ] Restore models tests (`backend/tests/api/v1/test_restore_models.py`)
- [ ] Restore integration tests (`backend/tests/api/v1/test_restore_integration.py`)
- [ ] Static file serving tests (`backend/tests/test_static_files.py`)
- [ ] Background cleanup tests (`backend/tests/services/test_cleanup.py`)

**Backend Test Data:**
- [ ] Create `backend/tests/data/` directory
- [ ] Add sample test images (small, large, corrupted, invalid)
- [ ] Create `backend/tests/mocks/` directory
- [ ] Implement HF API mock responses

**Frontend Test Infrastructure:**
- [ ] Complete Vitest configuration
  - [ ] Create `frontend/vitest.config.ts`
  - [ ] Configure jsdom environment
  - [ ] Setup coverage reporting
- [ ] Test setup and utilities
  - [ ] Create `frontend/src/__tests__/setup.ts`
  - [ ] Create `frontend/src/test-utils/mockApiClient.ts`
  - [ ] Create `frontend/src/test-utils/testData.ts`
  - [ ] Create `frontend/src/test-utils/renderWithProviders.tsx`

**Frontend Unit Tests:**
- [ ] Auth store tests (`frontend/src/__tests__/authStore.test.tsx`)
- [ ] Auth hook tests (`frontend/src/__tests__/useAuth.test.tsx`)
- [ ] API client tests (`frontend/src/__tests__/apiClient.test.tsx`)
- [ ] Restoration service tests (`frontend/src/__tests__/restorationService.test.tsx`)
- [ ] History service tests (`frontend/src/__tests__/historyService.test.tsx`)

**Frontend Component Tests:**
- [ ] LoginForm tests (`frontend/src/__tests__/auth.test.tsx`)
- [ ] ProtectedRoute tests (included in auth.test.tsx)
- [ ] ImageUploader tests (`frontend/src/__tests__/imageUploader.test.tsx`)
- [ ] ModelSelector tests (`frontend/src/__tests__/modelSelector.test.tsx`)
- [ ] ImageComparison tests (`frontend/src/__tests__/imageComparison.test.tsx`)
- [ ] HistoryList tests (`frontend/src/__tests__/history.test.tsx`)
- [ ] Shared component tests (`frontend/src/__tests__/components/`)

**Frontend Integration Tests:**
- [ ] Login flow integration test
- [ ] Image restoration flow integration test
- [ ] History viewing integration test
- [ ] Layout and navigation tests (`frontend/src/__tests__/layout.test.tsx`)
- [ ] Page integration tests (`frontend/src/__tests__/pages/`)

**Test Coverage Goals:**
- [ ] Backend: ≥70% code coverage
- [ ] Frontend: ≥60% code coverage
- [ ] All auth flows tested
- [ ] All API endpoints tested
- [ ] All error scenarios tested

**Test Automation:**
- [ ] Add npm script: `"test:coverage": "vitest run --coverage"`
- [ ] Add npm script: `"test:watch": "vitest"`
- [ ] Add backend script: `pytest --cov=app --cov-report=html`
- [ ] Setup CI/CD pipeline (GitHub Actions)
  - [ ] Run backend tests on PR
  - [ ] Run frontend tests on PR
  - [ ] Report coverage
  - [ ] Fail PR if tests fail

**End-to-End (E2E) Tests (Optional for MVP):**
- [ ] Setup Playwright for E2E testing
  - [ ] Create `tests/e2e/` directory
  - [ ] Configure Playwright to run against Docker stack
  - [ ] Setup test mode backend (mocked HF API)
- [ ] E2E test scenarios (`tests/e2e/restore.spec.ts`)
  - [ ] Happy path: Login → upload → select model → restore → download
  - [ ] Invalid file upload: Upload .txt → see error message
  - [ ] HF failure: Backend returns error → UI shows clear message
  - [ ] Auto-logout: Token expires → redirected to login
  - [ ] History: View processed images → download/delete

**Security & Performance Tests:**
- [ ] Security validation
  - [ ] No sensitive info in error messages (SECRET_KEY, HF_API_KEY)
  - [ ] CORS configuration tested (allowed origins only)
  - [ ] Auth tokens not logged in backend
  - [ ] SQL injection prevention (parameterized queries)
- [ ] Performance tests (basic)
  - [ ] Typical restore request (mocked HF) completes < 500ms
  - [ ] Large image upload (9.5MB) processed within timeout
  - [ ] Database queries are indexed and efficient

---

### 1.10 Documentation & Deployment

**Documentation:**
- [ ] Update README.md with:
  - [ ] Project description
  - [ ] Features list
  - [ ] Tech stack details
  - [ ] Setup instructions (Docker & local dev)
  - [ ] Environment variables documentation
  - [ ] API documentation link
- [ ] Create API documentation
  - [ ] Use FastAPI auto-generated docs
  - [ ] Add detailed descriptions to all endpoints
  - [ ] Add request/response examples
- [ ] Create deployment guide
  - [ ] Docker Compose deployment steps
  - [ ] nginx configuration details
  - [ ] SSL/HTTPS setup guide
  - [ ] Environment variable configuration

**Docker Deployment:**
- [ ] Test full Docker Compose stack
- [ ] Verify nginx reverse proxy routing
- [ ] Test backend API through proxy
- [ ] Test frontend static serving
- [ ] Verify file upload/download through proxy
- [ ] Test database persistence (volume mounts)
- [ ] Optimize Docker images (multi-stage builds)
- [ ] Add health check endpoints
  - [ ] Backend: GET `/health`
  - [ ] Frontend: nginx status

**Production Readiness:**
- [ ] Add logging configuration
  - [ ] Backend: structured JSON logs
  - [ ] Frontend: error tracking
- [ ] Add monitoring hooks
  - [ ] Health endpoints
  - [ ] Metrics endpoints (optional)
- [ ] Security hardening
  - [ ] CORS configuration
  - [ ] Rate limiting (optional for MVP)
  - [ ] Input sanitization
  - [ ] File upload size limits
- [ ] Performance optimization
  - [ ] Image compression
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

### 2.4 Enhanced Authentication Features

**Backend:**
- [ ] Database-backed user management (replace hardcoded credentials)
  - [ ] User table in SQLite
  - [ ] CRUD operations for users
  - [ ] Admin user management endpoints
- [ ] Configurable token expiration
  - [ ] Allow users to set token lifetime
  - [ ] Short-lived tokens with refresh token support
  - [ ] Configurable per-user token settings
- [ ] Enhanced password security
  - [ ] Password complexity requirements
  - [ ] Password change functionality
  - [ ] Password reset flow via email (optional)
- [ ] Session management improvements
  - [ ] Multiple device support
  - [ ] Active session viewing
  - [ ] Remote logout capability

**Frontend:**
- [ ] User registration page
- [ ] Profile management page
- [ ] Password change interface
- [ ] Active sessions viewer
- [ ] Security settings

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

**Last Updated:** December 15, 2024
**Current Phase:** Phase 1 - MVP (In Progress)
**Status:** Phase 1.1 Complete ✅ | Phase 1.2 Complete ✅ | Phase 1.3 Complete ✅ | Phase 1.4 Complete ✅
