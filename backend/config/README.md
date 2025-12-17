# Configuration Directory

This directory contains environment-specific configuration files for the Photo Restoration API.

## Files

### Committed to Git (Version Controlled)
- `default.json` - Base configuration with all default values
- `development.json.example` - Example development configuration
- `production.json.example` - Example production configuration
- `staging.json.example` - Example staging configuration
- `testing.json` - Configuration for automated tests

### Not Committed (Runtime Configs)
- `development.json` - Active development configuration
- `production.json` - Active production configuration
- `staging.json` - Active staging configuration

## Usage

### Initial Setup

⚠️ **CRITICAL**: The configuration system requires `default.json` to exist!

**Step 1: Ensure `default.json` exists**

The `default.json` file is committed to git and should already be present. However, if you're deploying with Docker volume mounts, you must copy it to your mounted directory:

```bash
# For Docker deployments with volume mounts
# Example: -v /opt/retro/config:/app/config
sudo cp backend/config/default.json /opt/retro/config/

# Verify it exists
ls -la /opt/retro/config/default.json
```

**Step 2: Create environment-specific config (optional but recommended)**

```bash
# For development
cp config/development.json.example config/development.json

# For production
cp config/production.json.example config/production.json

# For staging
cp config/staging.json.example config/staging.json
```

**Step 3: Edit the environment-specific file with your settings**

Edit `production.json` (or `development.json`) to customize for your environment.

**Step 4: Set the environment variable**

```bash
export APP_ENV=production  # or development, staging
```

### Configuration Loading Priority

The application loads configuration in this order (each level overrides the previous):

1. **`config/default.json`** - Base configuration (**REQUIRED** - must exist!)
2. **`config/{APP_ENV}.json`** - Environment-specific overrides (optional)
3. **Environment Variables** (from `.env` file) - Highest priority overrides

**Example:** If `APP_ENV=production`, the app loads:
1. `config/default.json` (base) - **MUST EXIST**
2. `config/production.json` (overrides defaults) - optional
3. `.env` variables (override everything) - optional

### What Happens If `default.json` Is Missing?

If `config/default.json` doesn't exist, the system will:
- ❌ **Fall back to deprecated `.env`-only mode**
- ⚠️ **Only load 1 hardcoded default model** instead of your configured models
- ⚠️ Show warning: `Default config not found: /app/config/default.json`
- ⚠️ Show warning: `⚠ Using .env-only configuration (DEPRECATED)`

**How to verify config loaded correctly:**
```bash
# Check startup logs
docker logs retro-backend 2>&1 | grep "Configuration source"

# Expected (correct):
# Configuration source: JSON config files

# Wrong (default.json missing):
# Configuration source: .env only (DEPRECATED)
```

### Secrets vs Configuration

**Secrets (in `.env` file):**
- API keys (HF_API_KEY, REPLICATE_API_TOKEN)
- JWT secret (SECRET_KEY)
- Credentials (AUTH_USERNAME, AUTH_PASSWORD)

**Configuration (in `config/*.json`):**
- Application settings
- Server configuration
- CORS origins
- Models configuration
- Database settings (non-sensitive)
- File storage settings
- Session settings

## Validation

Validate your configuration:
```bash
python scripts/validate_config.py --env production
```

## Migration from .env

If you have an existing `.env` file with all configuration:
```bash
python scripts/migrate_env_to_config.py --env-file backend/.env --output config/production.json
```

## Auto-Generated Documentation

Generate complete configuration reference:
```bash
python scripts/generate_config_docs.py --output docs/configuration.md
```

## Docker

In Docker, mount the config directory as a volume:
```yaml
volumes:
  - ./backend/config:/app/config:ro
```

This allows you to update configuration without rebuilding containers.
