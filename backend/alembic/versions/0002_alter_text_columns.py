"""Alter long text columns to Text

Revision ID: 0002_alter_text_columns
Revises: 0001_initial_schema
Create Date: 2026-04-16 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = '0002_alter_text_columns'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('claims', 'claim_text', type_=sa.Text(), existing_type=sa.String(length=1024), existing_nullable=False)
    op.alter_column('claims', 'original_quote', type_=sa.Text(), existing_type=sa.Text(), existing_nullable=True)
    op.alter_column('speeches', 'debate_title', type_=sa.Text(), existing_type=sa.String(length=512), existing_nullable=True)
    op.alter_column('contradictions', 'explanation', type_=sa.Text(), existing_type=sa.Text(), existing_nullable=True)


def downgrade() -> None:
    op.alter_column('claims', 'claim_text', type_=sa.String(length=1024), existing_type=sa.Text(), existing_nullable=False)
    op.alter_column('claims', 'original_quote', type_=sa.Text(), existing_type=sa.Text(), existing_nullable=True)
    op.alter_column('speeches', 'debate_title', type_=sa.String(length=512), existing_type=sa.Text(), existing_nullable=True)
    op.alter_column('contradictions', 'explanation', type_=sa.Text(), existing_type=sa.Text(), existing_nullable=True)
