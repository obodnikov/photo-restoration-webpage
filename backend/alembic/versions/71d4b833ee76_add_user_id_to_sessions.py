"""add_user_id_to_sessions

Revision ID: 71d4b833ee76
Revises:
Create Date: 2025-12-24 13:01:31.320470

This migration adds the user_id column to the sessions table to support
per-user session tracking. This is a backwards-incompatible change that
requires backfilling existing sessions.

Strategy:
1. Add user_id column as nullable
2. Backfill existing sessions with admin user ID
3. Make user_id non-nullable
4. Add foreign key constraint
5. Add index for performance
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '71d4b833ee76'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add user_id column to sessions table."""
    conn = op.get_bind()

    # Check if user_id column already exists (from create_all())
    result = conn.execute(text("PRAGMA table_info(sessions)"))
    columns = result.fetchall()
    column_names = [col[1] for col in columns]  # col[1] is column name

    if 'user_id' not in column_names:
        # Column doesn't exist, add it
        op.add_column('sessions', sa.Column('user_id', sa.Integer(), nullable=True))

        # Backfill existing sessions with admin user ID
        result = conn.execute(text("SELECT id FROM users WHERE role = 'admin' LIMIT 1"))
        admin_row = result.fetchone()

        if admin_row:
            admin_id = admin_row[0]
            # Update all sessions without user_id to belong to admin
            conn.execute(
                text("UPDATE sessions SET user_id = :admin_id WHERE user_id IS NULL"),
                {"admin_id": admin_id}
            )
        else:
            # If no admin user exists, delete orphaned sessions
            # This should not happen in production as seed creates admin
            conn.execute(text("DELETE FROM sessions WHERE user_id IS NULL"))

        # Make user_id non-nullable by recreating table
        op.execute("""
            CREATE TABLE sessions_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id VARCHAR(36) UNIQUE NOT NULL,
                created_at DATETIME NOT NULL,
                last_accessed DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Copy data from old table to new table
        op.execute("""
            INSERT INTO sessions_new (id, user_id, session_id, created_at, last_accessed)
            SELECT id, user_id, session_id, created_at, last_accessed
            FROM sessions
        """)

        # Drop old table and rename new table
        op.execute("DROP TABLE sessions")
        op.execute("ALTER TABLE sessions_new RENAME TO sessions")

        # Add indexes for performance
        op.create_index('idx_sessions_user_id', 'sessions', ['user_id'])
        op.create_index('idx_sessions_session_id', 'sessions', ['session_id'], unique=True)
    else:
        # Column already exists, just ensure it's properly configured
        # Check if it has the right constraints and indexes
        result = conn.execute(text("PRAGMA index_list(sessions)"))
        indexes = result.fetchall()
        index_names = [idx[1] for idx in indexes]

        if 'idx_sessions_user_id' not in index_names:
            op.create_index('idx_sessions_user_id', 'sessions', ['user_id'])

        if 'idx_sessions_session_id' not in index_names:
            op.create_index('idx_sessions_session_id', 'sessions', ['session_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema: Remove user_id column from sessions table."""
    # Recreate sessions table without user_id
    op.execute("""
        CREATE TABLE sessions_old (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id VARCHAR(36) UNIQUE NOT NULL,
            created_at DATETIME NOT NULL,
            last_accessed DATETIME NOT NULL
        )
    """)
    
    # Copy data (excluding user_id)
    op.execute("""
        INSERT INTO sessions_old (id, session_id, created_at, last_accessed)
        SELECT id, session_id, created_at, last_accessed
        FROM sessions
    """)
    
    # Drop new table and rename old table
    op.execute("DROP TABLE sessions")
    op.execute("ALTER TABLE sessions_old RENAME TO sessions")
    
    # Recreate session_id index
    op.create_index('idx_sessions_session_id', 'sessions', ['session_id'], unique=True)
