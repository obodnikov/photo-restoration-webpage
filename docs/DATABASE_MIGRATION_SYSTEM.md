# Database Migration System

## Overview

This document describes the database migration tracking system implemented to safely manage schema evolution and ensure self-healing during container restarts.

## Problem

Previously, when the application container was restarted, there was no tracking of whether the database had been properly initialized. This created risks around:
- No way to track when the database was first set up
- Difficulty safely adding new tables/columns in future code updates
- No recovery mechanism for accidentally deleted data (e.g., admin user)

## Solution

Implemented a migration tracking system that provides:

1. **Migration Tracking** using a `schema_migrations` table
2. **Always runs `create_all()`** for safe schema evolution (idempotent)
3. **Self-healing seeding** runs on every startup (idempotent)
4. **Records migration only after successful seeding** to enable retry on failure
5. **Foundation for future schema migrations**

## Implementation Details

### New Database Model

Added `SchemaMigration` model ([models.py:23-64](backend/app/db/models.py#L23-L64)):

```python
class SchemaMigration(Base):
    """Schema migration tracking model."""
    __tablename__ = "schema_migrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
```

### Migration Tracking Functions

Added to [database.py](backend/app/db/database.py):

- **`is_db_initialized(engine)`** ([database.py:97-137](backend/app/db/database.py#L97-L137))
  - Checks if `schema_migrations` table exists
  - Verifies the initial migration `001_initial_schema` is recorded
  - Returns `True` if database is fully initialized, `False` otherwise

- **`record_migration(session, version, description)`** ([database.py:140-174](backend/app/db/database.py#L140-L174))
  - Records a migration as applied in the database
  - Idempotent - skips if migration already recorded
  - Handles race conditions in multi-instance deployments

### Updated init_db()

Modified `init_db()` ([database.py:177-256](backend/app/db/database.py#L177-L256)) with critical fixes:

**Key Behaviors:**
1. **ALWAYS runs `create_all()`** - Safe and idempotent, allows new tables/columns to be added
2. **First initialization**: Seeds data, then records migration (ensures retry on failure)
3. **Subsequent startups**: Re-runs idempotent seeding for self-healing
4. **Logs clear messages** about initialization vs. self-healing

## Usage

### First Start (Fresh Database)

```
INFO - Database schema synchronized
INFO - First initialization: creating initial data
INFO - Database seeding completed successfully
INFO - Database initialized successfully
```

### Subsequent Restarts

```
INFO - Database schema synchronized
INFO - Database already initialized, running self-healing seed
INFO - Database seeding completed successfully
INFO - Self-healing seed completed
```

## Benefits

1. **New Table Creation**: New tables are automatically created on upgrade
2. **Self-Healing**: Admin user (and other seed data) is automatically restored if deleted
3. **Retry on Failure**: If seeding fails on first init, migration isn't recorded, allowing retry
4. **Graceful Degradation**: Self-healing failures on restart log warnings but don't crash app
5. **Data Preservation**: Existing users and data are preserved across restarts
6. **Clear Logging**: Easy to see initialization state and what's happening
7. **Migration History**: Track when database schema was initialized
8. **Race Condition Safe**: Handles concurrent initializations gracefully
9. **Seeding Idempotency**: Multiple seeding runs never create duplicates

## ⚠️ CRITICAL Limitations

### Database Path Configuration

**IMPORTANT: SQLite URL Format**
- `sqlite+aiosqlite:////data/photo_restoration.db` - **4 slashes** = absolute path `/data/photo_restoration.db`
- `sqlite+aiosqlite:///./data/photo_restoration.db` - **3 slashes** = relative path `./data/photo_restoration.db` from working directory

**For Docker/Production:**
- Use **4 slashes** for absolute paths: `sqlite+aiosqlite:////data/photo_restoration.db`
- This ensures the database is created in `/data/` which is mounted as a Docker volume
- Using 3 slashes will create the database in `/app/data/` which is NOT persistent!

**For Local Development:**
- Use **3 slashes** for relative paths: `sqlite+aiosqlite:///./data/photo_restoration.db`
- This creates the database in the project's `./data/` directory

### Schema Evolution Limitations

**What `create_all()` Does:**
- ✅ Creates missing **tables** only
- ✅ Is idempotent (safe to run multiple times)

**What `create_all()` Does NOT Do:**
- ❌ Does **NOT** add new columns to existing tables
- ❌ Does **NOT** drop columns or tables
- ❌ Does **NOT** rename columns or tables
- ❌ Does **NOT** alter column types or constraints
- ❌ Does **NOT** handle complex data migrations

**For ANY schema change beyond new tables, you MUST use Alembic migrations.**

This includes:
- Adding a new column to an existing table → **Use Alembic**
- Changing a column type → **Use Alembic**
- Renaming anything → **Use Alembic**
- Dropping anything → **Use Alembic**

⚠️ **Self-Healing Behavior:**
- Self-healing seed runs on every startup for data recovery
- Failures during self-healing log warnings but don't crash the application
- First-time initialization failures DO crash the application (as expected)

## Critical Fixes Applied

Based on code review, the following critical issues were fixed:

### [HIGH] Future schema changes will now be applied
**Problem:** Previously skipped `create_all()` after initialization, breaking future table additions.
**Fix:** Now ALWAYS runs `create_all()` (it's idempotent and safe).
**Test:** `test_init_db_allows_new_tables_after_initialization`

### [HIGH] Seeding failures no longer break the database
**Problem:** Previously recorded migration before seeding, leaving DB in broken state on failure.
**Fix:** Now records migration AFTER successful seeding, enabling retry.
**Test:** `test_init_db_retries_seeding_on_failure`

### [MEDIUM] Self-healing for accidentally deleted data
**Problem:** Previously skipped seeding after initialization, no recovery path.
**Fix:** Now runs idempotent seeding every startup for self-healing.
**Test:** `test_init_db_self_healing_admin_user`

## Testing

### Test Coverage

- **test_migrations.py**: 19 tests covering:
  - SchemaMigration model creation and uniqueness
  - `is_db_initialized()` function behavior
  - `record_migration()` idempotency and race conditions
  - `init_db()` idempotency and data preservation
  - **Regression tests**:
    - Schema evolution (new tables added after initialization)
    - Seeding failure retry mechanism
    - Self-healing admin user restoration
    - Data integrity with no duplicates across multiple restarts

- **Updated existing tests**: Fixed tests in `test_database.py` and `test_models.py` to work with migration system

### Manual Testing

Verified with real application:

```bash
# First start
./backend/venv/bin/python -m uvicorn app.main:app
# Output: Database schema synchronized
#         First initialization: creating initial data

# Second start (restart)
./backend/venv/bin/python -m uvicorn app.main:app
# Output: Database schema synchronized
#         Database already initialized, running self-healing seed
```

## Future Enhancements

This system provides a foundation for:

1. **Version Migrations**: Add migration functions for specific version upgrades
2. **Data Migrations**: Run data transformations during schema changes
3. **Rollback Support**: Track and potentially reverse migrations
4. **Migration CLI**: Command-line tools for managing migrations manually

## Database Schema

The `schema_migrations` table structure:

```sql
CREATE TABLE schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500) NOT NULL,
    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_schema_migrations_version ON schema_migrations (version);
```

Current migrations:
- `001_initial_schema`: Initial database schema with users, sessions, and processed_images tables

## Related Files

- [backend/app/db/models.py](backend/app/db/models.py) - SchemaMigration model
- [backend/app/db/database.py](backend/app/db/database.py) - Migration tracking functions and init_db()
- [backend/app/db/seed.py](backend/app/db/seed.py) - Seed database (idempotent)
- [backend/tests/db/test_migrations.py](backend/tests/db/test_migrations.py) - Migration tests including regression tests
- [backend/tests/db/conftest.py](backend/tests/db/conftest.py) - Shared test fixtures
