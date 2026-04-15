"""Initial Echo schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-04-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    op.create_table(
        'persons',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('party', sa.String(length=255), nullable=True),
        sa.Column('constituency', sa.String(length=255), nullable=True),
        sa.Column('house', sa.String(length=50), nullable=False),
        sa.Column('role', sa.String(length=255), nullable=True),
        sa.Column('photo_url', sa.String(length=1024), nullable=True),
        sa.Column('parliament_id', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('parliament_id', name='uq_persons_parliament_id'),
    )

    op.create_table(
        'topics',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_topic_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('topics.id', ondelete='SET NULL'), nullable=True),
        sa.UniqueConstraint('name', name='uq_topics_name'),
        sa.UniqueConstraint('slug', name='uq_topics_slug'),
    )

    op.create_table(
        'speeches',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('person_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('persons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('source_url', sa.String(length=1024), nullable=True),
        sa.Column('full_text', sa.Text(), nullable=False),
        sa.Column('debate_title', sa.String(length=512), nullable=True),
        sa.Column('house', sa.String(length=50), nullable=False),
        sa.Column('hansard_id', sa.String(length=255), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('hansard_id', name='uq_speeches_hansard_id'),
    )

    op.create_table(
        'votes',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('person_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('persons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('division_id', sa.Integer(), nullable=False),
        sa.Column('division_title', sa.String(length=512), nullable=True),
        sa.Column('vote', sa.String(length=50), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('house', sa.String(length=50), nullable=False),
    )

    op.create_table(
        'claims',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('speech_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('speeches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('person_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('persons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('claim_text', sa.String(length=1024), nullable=False),
        sa.Column('original_quote', sa.Text(), nullable=True),
        sa.Column('topic_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('topics.id', ondelete='SET NULL'), nullable=True),
        sa.Column('stance', sa.String(length=50), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('date', sa.Date(), nullable=True),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'contradictions',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('claim_a_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('claims.id', ondelete='CASCADE'), nullable=False),
        sa.Column('claim_b_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('claims.id', ondelete='CASCADE'), nullable=False),
        sa.Column('person_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('persons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('topics.id', ondelete='SET NULL'), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('severity', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'position_summaries',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('person_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('persons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('topics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('claim_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('date_range_start', sa.Date(), nullable=True),
        sa.Column('date_range_end', sa.Date(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index('ix_speeches_person_id_date', 'speeches', ['person_id', 'date'])
    op.create_index('ix_votes_person_id_date', 'votes', ['person_id', 'date'])
    op.create_index('ix_claims_person_id_date', 'claims', ['person_id', 'date'])
    op.create_index('ix_claims_person_id_topic_id', 'claims', ['person_id', 'topic_id'])
    op.create_index('ix_position_summaries_person_id_topic_id', 'position_summaries', ['person_id', 'topic_id'])


def downgrade() -> None:
    op.drop_index('ix_position_summaries_person_id_topic_id', table_name='position_summaries')
    op.drop_index('ix_claims_person_id_topic_id', table_name='claims')
    op.drop_index('ix_claims_person_id_date', table_name='claims')
    op.drop_index('ix_votes_person_id_date', table_name='votes')
    op.drop_index('ix_speeches_person_id_date', table_name='speeches')

    op.drop_table('position_summaries')
    op.drop_table('contradictions')
    op.drop_table('claims')
    op.drop_table('votes')
    op.drop_table('speeches')
    op.drop_table('topics')
    op.drop_table('persons')
