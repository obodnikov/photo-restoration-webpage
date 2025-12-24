# Database Migration System

## Overview

This document describes the database migration tracking system implemented to prevent data loss during container restarts.

## Problem

Previously, when the application container was restarted, the `init_db()` function would:
1. Run `Base.metadata.create_all()` - which creates tables if they don't exist
2. Always run `seed_database()` - which could potentially overwrite existing data

While `create_all()` is idempotent (it doesn't drop existing tables), there was no formal mechanism to track whether the database had already been initialized, making it difficult to manage schema changes and prevent re-seeding.

## Solution

Implemented a migration tracking system similar to Alembic/Django migrations that:

1. **Tracks applied migrations** using a `schema_migrations` table
2. **Checks if database is initialized** before running schema creation and seeding
3. **Prevents data loss** by skipping migrations that have already been applied
4. **Provides a foundation** for future schema evolution

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

Modified `init_db()` ([database.py:177-250](backend/app/db/database.py#L177-L250)) to:

1. Check if database is already initialized using `is_db_initialized()`
2. Skip schema creation and seeding if already initialized
3. Record the `001_initial_schema` migration on first initialization
4. Log clear messages about what's happening

## Usage

### First Start (Fresh Database)

```
INFO - Database not initialized, creating schema and seeding initial data
INFO - Database schema created successfully
INFO - Recorded initial migration: 001_initial_schema
INFO - Database seeding completed successfully
```

### Subsequent Restarts

```
INFO - Database already initialized, skipping schema creation and seeding
```

## Benefits

1. **Data Preservation**: Existing users and data are never removed on restart
2. **Clear Logging**: Easy to see whether migrations ran or were skipped
3. **Migration History**: Track when database schema was initialized
4. **Future-Proof**: Foundation for adding schema evolution migrations
5. **Race Condition Safe**: Handles concurrent initializations gracefully

## Testing

### Test Coverage

- **test_migrations.py**: 15 tests covering:
  - SchemaMigration model creation and uniqueness
  - `is_db_initialized()` function behavior
  - `record_migration()` idempotency and race conditions
  - `init_db()` idempotency and data preservation

- **Updated existing tests**: Fixed tests in `test_database.py` and `test_models.py` to work with new migration system

### Manual Testing

Verified with real application:

```bash
# First start
./backend/venv/bin/python -m uvicorn app.main:app
# Output: Database not initialized, creating schema...

# Second start (restart)
./backend/venv/bin/python -m uvicorn app.main:app
# Output: Database already initialized, skipping...
```

## Future Enhancements

This system provides a foundation for:

1. **Schema Migrations**: Add new migration versions for schema changes
2. **Data Migrations**: Run data transformations during upgrades
3. **Rollback Support**: Track and potentially reverse migrations
4. **Migration CLI**: Command-line tools for managing migrations

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
- [backend/app/db/database.py](backend/app/db/database.py) - Migration tracking functions and updated init_db()
- [backend/app/db/seed.py](backend/app/db/seed.py) - Seed database (already idempotent)
- [backend/tests/db/test_migrations.py](backend/tests/db/test_migrations.py) - Migration tests
- [backend/tests/db/conftest.py](backend/tests/db/conftest.py) - Shared test fixtures
