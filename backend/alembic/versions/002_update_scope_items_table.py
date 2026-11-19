"""002 Update scope_items table with included_description and not_included_description

Revision ID: 002_update_scope_items_table
Revises: 001_initial_schema
Create Date: 2026-11-19 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_update_scope_items_table"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns as nullable initially
    op.add_column("scope_items", sa.Column("included_description", sa.Text(), nullable=True))
    op.add_column("scope_items", sa.Column("not_included_description", sa.Text(), nullable=True))

    # 2. Safely migrate existing records if present
    op.execute(
        """
        UPDATE scope_items
        SET 
            included_description = COALESCE(description, title, ''),
            not_included_description = CASE 
                WHEN status = 'out_of_scope' THEN COALESCE(description, title, '')
                ELSE ''
            END
        WHERE included_description IS NULL
        """
    )

    # 3. Enforce NOT NULL constraint on new columns with empty string server default
    op.alter_column("scope_items", "included_description", nullable=False, server_default="")
    op.alter_column("scope_items", "not_included_description", nullable=False, server_default="")

    # 4. Safely drop deprecated columns
    op.drop_column("scope_items", "title")
    op.drop_column("scope_items", "description")
    op.drop_column("scope_items", "status")
    op.drop_column("scope_items", "estimated_hours")


def downgrade() -> None:
    # 1. Re-add deprecated columns
    op.add_column("scope_items", sa.Column("title", sa.String(length=255), server_default="Scope Item", nullable=False))
    op.add_column("scope_items", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("scope_items", sa.Column("status", sa.String(length=50), server_default="included", nullable=False))
    op.add_column("scope_items", sa.Column("estimated_hours", sa.Numeric(precision=8, scale=2), nullable=True))

    # 2. Restore data from included_description
    op.execute(
        """
        UPDATE scope_items
        SET description = included_description,
            title = SUBSTRING(included_description FROM 1 FOR 250)
        """
    )

    # 3. Drop new columns
    op.drop_column("scope_items", "not_included_description")
    op.drop_column("scope_items", "included_description")
