"""add_session_metadata

Revision ID: 001_add_session_metadata
Revises: 71d4b833ee76
Create Date: 2025-12-30

This migration adds session metadata columns to the sessions table to support
enhanced session details display including browser, OS, device type, IP address,
and approximate geolocation.

All new columns are nullable to ensure backward compatibility with existing sessions.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '001_add_session_metadata'
down_revision: Union[str, Sequence[str], None] = '71d4b833ee76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add metadata columns to sessions table.

    Adds the following nullable columns:
    - user_agent: Full user agent string (VARCHAR(500))
    - ip_address: IP address used for login (VARCHAR(45) for IPv6 support)
    - device_type: Device category - mobile/desktop/tablet (VARCHAR(50))
    - browser: Browser name and version (VARCHAR(100))
    - os: Operating system name and version (VARCHAR(100))
    - location: Approximate geographic location (VARCHAR(200))
    """
    conn = op.get_bind()

    # Check if columns already exist to make migration idempotent
    result = conn.execute(text("PRAGMA table_info(sessions)"))
    columns = result.fetchall()
    column_names = [col[1] for col in columns]  # col[1] is column name

    # Add each column if it doesn't exist
    if 'user_agent' not in column_names:
        op.add_column('sessions', sa.Column('user_agent', sa.String(500), nullable=True))

    if 'ip_address' not in column_names:
        op.add_column('sessions', sa.Column('ip_address', sa.String(45), nullable=True))

    if 'device_type' not in column_names:
        op.add_column('sessions', sa.Column('device_type', sa.String(50), nullable=True))

    if 'browser' not in column_names:
        op.add_column('sessions', sa.Column('browser', sa.String(100), nullable=True))

    if 'os' not in column_names:
        op.add_column('sessions', sa.Column('os', sa.String(100), nullable=True))

    if 'location' not in column_names:
        op.add_column('sessions', sa.Column('location', sa.String(200), nullable=True))


def downgrade() -> None:
    """Downgrade schema: Remove metadata columns from sessions table."""
    # Drop the metadata columns
    # Note: SQLite doesn't support ALTER TABLE DROP COLUMN directly
    # We need to recreate the table without these columns

    op.execute("""
        CREATE TABLE sessions_old (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id VARCHAR(36) UNIQUE NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_accessed DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Copy data (excluding metadata columns)
    op.execute("""
        INSERT INTO sessions_old (id, user_id, session_id, created_at, last_accessed)
        SELECT id, user_id, session_id, created_at, last_accessed
        FROM sessions
    """)

    # Drop new table and rename old table
    op.execute("DROP TABLE sessions")
    op.execute("ALTER TABLE sessions_old RENAME TO sessions")

    # Recreate indexes
    op.create_index('idx_sessions_user_id', 'sessions', ['user_id'])
    op.create_index('idx_sessions_session_id', 'sessions', ['session_id'], unique=True)
