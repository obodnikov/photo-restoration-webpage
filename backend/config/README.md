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

1. Copy the appropriate example file:
```bash
# For development
cp config/development.json.example config/development.json

# For production
cp config/production.json.example config/production.json

# For staging
cp config/staging.json.example config/staging.json
```

2. Edit the file with your environment-specific settings

3. Set the environment variable:
```bash
export APP_ENV=production  # or development, staging
```

### Configuration Loading Priority

The application loads configuration in this order (highest to lowest priority):

1. **Environment Variables** (from `.env` file)
2. **Environment-specific config** (`config/{APP_ENV}.json`)
3. **Default config** (`config/default.json`)

Example: If `APP_ENV=production`, the app loads:
- `config/default.json` (base)
- `config/production.json` (overrides defaults)
- `.env` variables (override everything)

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
