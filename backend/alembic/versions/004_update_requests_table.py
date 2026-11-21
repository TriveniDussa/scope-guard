"""004 Update requests table for AI Request Checker

Revision ID: 004_update_requests_table
Revises: 003_update_tasks_table
Create Date: 2026-11-21 19:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_update_requests_table"
down_revision: Union[str, None] = "003_update_tasks_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns as nullable initially
    op.add_column("requests", sa.Column("client_request", sa.Text(), nullable=True))
    op.add_column("requests", sa.Column("classification", sa.String(length=50), nullable=True))
    op.add_column("requests", sa.Column("reason", sa.Text(), nullable=True))
    op.add_column("requests", sa.Column("client_reply", sa.Text(), nullable=True))
    op.add_column("requests", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))

    # 2. Add foreign key and index for user_id
    op.create_foreign_key(
        "fk_requests_user_id_users",
        "requests",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_requests_user_id"), "requests", ["user_id"], unique=False)

    # 3. Migrate any existing records safely
    op.execute(
        """
        UPDATE requests
        SET client_request = COALESCE(description, title, ''),
            classification = CASE 
                WHEN status = 'in_scope' THEN 'In scope'
                WHEN status = 'scope_creep_detected' THEN 'Out of scope'
                ELSE 'Not sure'
            END,
            reason = COALESCE(ai_analysis, 'Initial scope assessment'),
            client_reply = 'Thank you for your request. This will be evaluated based on the agreed scope of work.',
            user_id = submitted_by_user_id
        WHERE client_request IS NULL;
        """
    )

    # 4. Enforce NOT NULL constraints on new required columns
    op.alter_column("requests", "client_request", nullable=False, server_default="")
    op.alter_column("requests", "classification", nullable=False, server_default="Not sure")
    op.alter_column("requests", "reason", nullable=False, server_default="")
    op.alter_column("requests", "client_reply", nullable=False, server_default="")

    # 5. Drop deprecated columns
    op.drop_column("requests", "title")
    op.drop_column("requests", "description")
    op.drop_column("requests", "ai_analysis")
    op.drop_column("requests", "impact_hours")
    op.drop_column("requests", "impact_cost")
    op.drop_column("requests", "status")
    op.drop_column("requests", "submitted_by_user_id")


def downgrade() -> None:
    # 1. Re-add dropped columns
    op.add_column("requests", sa.Column("title", sa.String(length=255), server_default="Request", nullable=False))
    op.add_column("requests", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("requests", sa.Column("ai_analysis", sa.Text(), nullable=True))
    op.add_column("requests", sa.Column("impact_hours", sa.Numeric(precision=8, scale=2), nullable=True))
    op.add_column("requests", sa.Column("impact_cost", sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column("requests", sa.Column("status", sa.String(length=50), server_default="pending_analysis", nullable=False))
    op.add_column("requests", sa.Column("submitted_by_user_id", postgresql.UUID(as_uuid=True), nullable=True))

    # 2. Restore data
    op.execute(
        """
        UPDATE requests
        SET description = client_request,
            title = SUBSTRING(client_request FROM 1 FOR 250),
            ai_analysis = reason,
            submitted_by_user_id = user_id;
        """
    )

    # 3. Drop user_id foreign key & index
    op.drop_index(op.f("ix_requests_user_id"), table_name="requests")
    op.drop_constraint("fk_requests_user_id_users", "requests", type_="foreignkey")

    # 4. Drop new columns
    op.drop_column("requests", "user_id")
    op.drop_column("requests", "client_reply")
    op.drop_column("requests", "reason")
    op.drop_column("requests", "classification")
    op.drop_column("requests", "client_request")
