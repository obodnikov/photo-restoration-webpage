#!/bin/bash

# Comprehensive test script for photo-restoration-webpage
# Tests configuration loading, TypeScript compilation, and Docker builds

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/test_results.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Clear previous log
> "$LOG_FILE"

log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log_section() {
    log ""
    log "${BLUE}======================================"
    log "$1"
    log "======================================${NC}"
    log ""
}

log_success() {
    log "${GREEN}✅ $1${NC}"
}

log_error() {
    log "${RED}❌ $1${NC}"
}

log_warning() {
    log "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    log "${BLUE}ℹ️  $1${NC}"
}

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"

    log_info "Running: $test_name"

    if eval "$test_command" >> "$LOG_FILE" 2>&1; then
        log_success "$test_name PASSED"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "$test_name FAILED"
        log "Check $LOG_FILE for details"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Start testing
log_section "Photo Restoration Webpage - Comprehensive Test Suite"
log "Test started at: $(date)"
log "Working directory: $SCRIPT_DIR"

# Test 1: Backend Configuration Tests
log_section "Test 1: Backend Configuration Loading"

log_info "Building test environment with Python 3.13..."
run_test "Backend Config Tests" \
    "cd '$SCRIPT_DIR/backend' && docker run --rm \
    -v \"\$PWD:/app\" \
    -w /app \
    python:3.13-slim \
    bash -c 'pip install -q pytest pydantic==2.10.6 pydantic-settings==2.7.1 && pytest tests/test_config.py -v --tb=short'"

# Test 2: TypeScript Compilation
log_section "Test 2: TypeScript Compilation"

log_info "Checking TypeScript compilation..."

# First, generate package-lock.json if missing
if [ ! -f "$SCRIPT_DIR/frontend/package-lock.json" ]; then
    log_warning "package-lock.json not found, generating..."
    run_test "Generate package-lock.json" \
        "cd '$SCRIPT_DIR' && docker run --rm \
        -v \"\$PWD/frontend:/app\" \
        -w /app \
        node:22.12-alpine \
        npm install"
fi

run_test "TypeScript Compilation Check" \
    "cd '$SCRIPT_DIR/frontend' && docker run --rm \
    -v \"\$PWD:/app\" \
    -w /app \
    node:22.12-alpine \
    sh -c 'npm install && npm run test:typecheck'"

# Test 3: Backend Docker Build
log_section "Test 3: Backend Docker Image Build"

log_info "Building backend Docker image..."
run_test "Backend Docker Build" \
    "cd '$SCRIPT_DIR' && docker build -t photo-restoration-backend:test ./backend"

if [ $? -eq 0 ]; then
    log_info "Checking backend image size..."
    docker images photo-restoration-backend:test --format "Size: {{.Size}}" | tee -a "$LOG_FILE"
fi

# Test 4: Frontend Docker Build
log_section "Test 4: Frontend Docker Image Build"

log_info "Building frontend Docker image..."
run_test "Frontend Docker Build" \
    "cd '$SCRIPT_DIR' && docker build -t photo-restoration-frontend:test ./frontend"

if [ $? -eq 0 ]; then
    log_info "Checking frontend image size..."
    docker images photo-restoration-frontend:test --format "Size: {{.Size}}" | tee -a "$LOG_FILE"
fi

# Test 5: Backend Container Startup Test
log_section "Test 5: Backend Container Startup"

log_info "Testing backend container startup..."
run_test "Backend Container Startup" \
    "docker run --rm -d \
    --name test-backend \
    -e SECRET_KEY=test_secret_key_at_least_32_characters_long_12345 \
    -e CORS_ORIGINS='[\"http://localhost:3000\",\"http://localhost\"]' \
    -e HF_API_KEY=test_key \
    photo-restoration-backend:test && \
    sleep 5 && \
    docker logs test-backend && \
    docker stop test-backend"

# Test 6: Configuration with different CORS formats
log_section "Test 6: CORS Configuration Format Test"

log_info "Testing CORS JSON format..."
run_test "CORS JSON Format" \
    "docker run --rm \
    -e CORS_ORIGINS='[\"http://example.com\",\"https://example.com\"]' \
    -e SECRET_KEY=test_secret_key_at_least_32_characters_long_12345 \
    -e HF_API_KEY=test_key \
    photo-restoration-backend:test \
    python -c 'from app.core.config import settings; assert \"http://example.com\" in settings.cors_origins; print(\"CORS JSON format works:\", settings.cors_origins)'"

log_info "Testing CORS comma-separated format (backward compatibility)..."
run_test "CORS Comma-Separated Format" \
    "docker run --rm \
    -e CORS_ORIGINS='http://test1.com,http://test2.com' \
    -e SECRET_KEY=test_secret_key_at_least_32_characters_long_12345 \
    -e HF_API_KEY=test_key \
    photo-restoration-backend:test \
    python -c 'from app.core.config import settings; assert \"http://test1.com\" in settings.cors_origins; print(\"CORS comma-separated format works:\", settings.cors_origins)'"

# Cleanup
log_section "Cleanup"

log_info "Cleaning up test images..."
docker rmi photo-restoration-backend:test 2>/dev/null || true
docker rmi photo-restoration-frontend:test 2>/dev/null || true
log_success "Cleanup completed"

# Summary
log_section "Test Summary"

log "Total Tests Run: $((TESTS_PASSED + TESTS_FAILED))"
log_success "Tests Passed: $TESTS_PASSED"

if [ $TESTS_FAILED -gt 0 ]; then
    log_error "Tests Failed: $TESTS_FAILED"
    log ""
    log_error "SOME TESTS FAILED!"
    log "Please check $LOG_FILE for details"
    exit 1
else
    log ""
    log_success "ALL TESTS PASSED! 🎉"
    log ""
    log "Test completed at: $(date)"
    log "Full test log saved to: $LOG_FILE"
fi

log_section "Next Steps"
log "1. Review test results in: $LOG_FILE"
log "2. Update your .env file with JSON format for CORS_ORIGINS:"
log "   CORS_ORIGINS=[\"http://localhost:8000\",\"http://localhost\",\"http://retro.sqowe.com\",\"https://retro.sqowe.com\"]"
log "3. Build production images:"
log "   docker build -t obodnikov/photo-restoration-backend:0.1.2 ./backend"
log "   docker build -t obodnikov/photo-restoration-frontend:0.1.2 ./frontend"
log "4. Deploy your containers"

exit 0
