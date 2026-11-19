"""003 Update tasks table schema and status values

Revision ID: 003_update_tasks_table
Revises: 002_update_scope_items_table
Create Date: 2026-11-19 22:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_update_tasks_table"
down_revision: Union[str, None] = "002_update_scope_items_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Normalize existing status values
    op.execute(
        """
        UPDATE tasks
        SET status = CASE
            WHEN status = 'todo' THEN 'To do'
            WHEN status = 'in_progress' THEN 'Doing'
            WHEN status = 'done' THEN 'Done'
            ELSE 'To do'
        END;
        """
    )
    op.alter_column("tasks", "status", server_default="To do", existing_type=sa.String(50))

    # 2. Convert due_date to DATE type
    op.execute("ALTER TABLE tasks ALTER COLUMN due_date TYPE DATE USING due_date::date;")

    # 3. Drop deprecated columns if they exist
    op.drop_column("tasks", "description")
    op.drop_column("tasks", "priority")
    op.drop_column("tasks", "assigned_to_user_id")


def downgrade() -> None:
    # 1. Re-add dropped columns
    op.add_column("tasks", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("priority", sa.String(50), server_default="medium", nullable=False))
    op.add_column("tasks", sa.Column("assigned_to_user_id", postgresql.UUID(as_uuid=True), nullable=True))

    # 2. Revert due_date to TIMESTAMP WITH TIME ZONE
    op.execute("ALTER TABLE tasks ALTER COLUMN due_date TYPE TIMESTAMP WITH TIME ZONE USING due_date::timestamp with time zone;")

    # 3. Reset default status to 'todo'
    op.alter_column("tasks", "status", server_default="todo", existing_type=sa.String(50))
