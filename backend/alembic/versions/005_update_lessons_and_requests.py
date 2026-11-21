"""005 Update lessons and requests tables for Learning and Check Again

Revision ID: 005_update_lessons_and_requests
Revises: 004_update_requests_table
Create Date: 2026-11-21 19:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_update_lessons_and_requests"
down_revision: Union[str, None] = "004_update_requests_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update requests table with feedback and parent_request_id for re-evaluation linking
    op.add_column("requests", sa.Column("feedback", sa.String(length=20), nullable=True))
    op.add_column("requests", sa.Column("parent_request_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_requests_parent_request_id_requests",
        "requests",
        "requests",
        ["parent_request_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_requests_parent_request_id"), "requests", ["parent_request_id"], unique=False)

    # 2. Update lessons table with Day 9 required fields
    op.add_column("lessons", sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("lessons", sa.Column("ai_answer", sa.String(length=50), nullable=True))
    op.add_column("lessons", sa.Column("correct_result", sa.String(length=50), nullable=True))
    op.add_column("lessons", sa.Column("correction_reason", sa.Text(), nullable=True))

    op.create_foreign_key(
        "fk_lessons_request_id_requests",
        "lessons",
        "requests",
        ["request_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_lessons_request_id"), "lessons", ["request_id"], unique=False)

    # 3. Migrate any existing lessons safely
    op.execute(
        """
        UPDATE lessons
        SET ai_answer = COALESCE(category, 'Not sure'),
            correct_result = CASE 
                WHEN category = 'in_scope' THEN 'In scope' 
                ELSE 'Out of scope' 
            END,
            correction_reason = COALESCE(content, title, 'Retrospective correction')
        WHERE correction_reason IS NULL;
        """
    )

    # 4. Enforce NOT NULL on new required fields
    op.alter_column("lessons", "ai_answer", nullable=False, server_default="")
    op.alter_column("lessons", "correct_result", nullable=False, server_default="In scope")
    op.alter_column("lessons", "correction_reason", nullable=False, server_default="")

    # 5. Drop deprecated columns from lessons
    op.drop_column("lessons", "title")
    op.drop_column("lessons", "category")
    op.drop_column("lessons", "content")
    op.drop_column("lessons", "action_items")


def downgrade() -> None:
    # 1. Restore old columns on lessons
    op.add_column("lessons", sa.Column("action_items", sa.Text(), nullable=True))
    op.add_column("lessons", sa.Column("content", sa.Text(), nullable=True))
    op.add_column("lessons", sa.Column("category", sa.String(length=100), server_default="general", nullable=False))
    op.add_column("lessons", sa.Column("title", sa.String(length=255), nullable=True))

    op.execute(
        """
        UPDATE lessons
        SET title = COALESCE(SUBSTRING(correction_reason FROM 1 FOR 255), 'Lesson Learned'),
            content = COALESCE(correction_reason, ''),
            category = 'general'
        WHERE title IS NULL;
        """
    )
    op.alter_column("lessons", "title", nullable=False)
    op.alter_column("lessons", "content", nullable=False)

    # 2. Drop new columns and constraints on lessons
    op.drop_constraint("fk_lessons_request_id_requests", "lessons", type_="foreignkey")
    op.drop_index(op.f("ix_lessons_request_id"), table_name="lessons")
    op.drop_column("lessons", "correction_reason")
    op.drop_column("lessons", "correct_result")
    op.drop_column("lessons", "ai_answer")
    op.drop_column("lessons", "request_id")

    # 3. Drop parent_request_id and feedback on requests
    op.drop_constraint("fk_requests_parent_request_id_requests", "requests", type_="foreignkey")
    op.drop_index(op.f("ix_requests_parent_request_id"), table_name="requests")
    op.drop_column("requests", "parent_request_id")
    op.drop_column("requests", "feedback")
