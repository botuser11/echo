"""Add debate_section_ext_id to speeches

Revision ID: 0003_add_debate_section_ext_id
Revises: 0002_alter_text_columns
Create Date: 2026-04-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = '0003_add_debate_section_ext_id'
down_revision = '0002_alter_text_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('speeches', sa.Column('debate_section_ext_id', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('speeches', 'debate_section_ext_id')