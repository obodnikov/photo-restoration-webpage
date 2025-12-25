"""initial_schema

Revision ID: 000_initial_schema
Revises:
Create Date: 2025-12-24 12:00:00.000000

This is the base migration that creates the initial database schema.
It creates all core tables: schema_migrations, users, sessions, and processed_images.

IMPORTANT: This migration assumes a fresh, empty database. Alembic's migration
tracking system ensures this migration only runs once. For existing databases
without these tables, use migration 71d4b833ee76_add_user_id_to_sessions to
upgrade the schema.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '000_initial_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema.

    Creates:
    - schema_migrations: Tracks applied migrations (for backwards compatibility)
    - users: User accounts with authentication
    - sessions: User sessions for tracking processed images (with user_id)
    - processed_images: Metadata for processed images

    This migration assumes a fresh database. Alembic tracks which migrations
    have been applied, so this will never run twice on the same database.
    """
    # Create schema_migrations table (for backwards compatibility with old migration tracking)
    op.create_table(
        'schema_migrations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('version', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('applied_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version')
    )
    op.create_index('ix_schema_migrations_version', 'schema_migrations', ['version'], unique=True)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('password_must_change', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create sessions table (with user_id from the start)
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_accessed', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index('ix_sessions_user_id', 'sessions', ['user_id'])
    op.create_index('ix_sessions_session_id', 'sessions', ['session_id'], unique=True)

    # Create processed_images table
    op.create_table(
        'processed_images',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('model_id', sa.String(length=100), nullable=False),
        sa.Column('original_path', sa.String(length=500), nullable=False),
        sa.Column('processed_path', sa.String(length=500), nullable=False),
        sa.Column('model_parameters', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_processed_images_session_id', 'processed_images', ['session_id'])


def downgrade() -> None:
    """Drop all tables created by this migration.

    WARNING: This will delete all data!

    Drops tables in reverse order of creation to respect foreign key constraints.
    """
    # Drop tables in reverse order of creation (to respect foreign keys)
    op.drop_table('processed_images')
    op.drop_table('sessions')
    op.drop_table('users')
    op.drop_table('schema_migrations')
