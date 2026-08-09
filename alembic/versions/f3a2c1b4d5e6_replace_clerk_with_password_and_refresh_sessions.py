"""replace clerk auth with password and refresh sessions

Revision ID: f3a2c1b4d5e6
Revises: 28a975b09a5b
Create Date: 2026-08-06 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3a2c1b4d5e6"
down_revision: str | Sequence[str] | None = "28a975b09a5b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # users: drop Clerk identity, add password hash.
    op.drop_index(op.f("ix_users_clerk_id"), table_name="users")
    op.drop_column("users", "clerk_id")
    # server_default satisfies NOT NULL on any pre-existing rows, then is removed.
    op.add_column("users", sa.Column("password_hash", sa.String(), nullable=False, server_default=""))
    op.alter_column("users", "password_hash", server_default=None)

    # refresh_sessions: server-side refresh token store (hashed) with rotation families.
    op.create_table(
        "refresh_sessions",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_refresh_sessions_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_sessions")),
    )
    op.create_index(op.f("ix_refresh_sessions_user_id"), "refresh_sessions", ["user_id"], unique=False)
    op.create_index(op.f("ix_refresh_sessions_token_hash"), "refresh_sessions", ["token_hash"], unique=True)
    op.create_index(op.f("ix_refresh_sessions_family_id"), "refresh_sessions", ["family_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_refresh_sessions_family_id"), table_name="refresh_sessions")
    op.drop_index(op.f("ix_refresh_sessions_token_hash"), table_name="refresh_sessions")
    op.drop_index(op.f("ix_refresh_sessions_user_id"), table_name="refresh_sessions")
    op.drop_table("refresh_sessions")

    op.drop_column("users", "password_hash")
    op.add_column("users", sa.Column("clerk_id", sa.String(), nullable=True))
    op.create_index(op.f("ix_users_clerk_id"), "users", ["clerk_id"], unique=True)
