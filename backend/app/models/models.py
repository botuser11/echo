from __future__ import annotations

import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Person(Base):
    __tablename__ = 'persons'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    party: Mapped[str | None] = mapped_column(String(255), nullable=True)
    constituency: Mapped[str | None] = mapped_column(String(255), nullable=True)
    house: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    parliament_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    speeches: Mapped[list["Speech"]] = relationship('Speech', back_populates='person', cascade='all, delete-orphan')
    claims: Mapped[list["Claim"]] = relationship('Claim', back_populates='person', cascade='all, delete-orphan')
    votes: Mapped[list["Vote"]] = relationship('Vote', back_populates='person', cascade='all, delete-orphan')
    contradictions: Mapped[list["Contradiction"]] = relationship('Contradiction', back_populates='person', cascade='all, delete-orphan')
    position_summaries: Mapped[list["PositionSummary"]] = relationship(
        'PositionSummary', back_populates='person', cascade='all, delete-orphan'
    )


class Topic(Base):
    __tablename__ = 'topics'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_topic_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey('topics.id', ondelete='SET NULL'), nullable=True
    )

    parent_topic: Mapped[Topic | None] = relationship('Topic', remote_side=[id], back_populates='children')
    children: Mapped[list[Topic]] = relationship('Topic', back_populates='parent_topic', cascade='all, delete-orphan')
    claims: Mapped[list['Claim']] = relationship('Claim', back_populates='topic', cascade='all, delete-orphan')
    contradictions: Mapped[list['Contradiction']] = relationship('Contradiction', back_populates='topic', cascade='all, delete-orphan')
    position_summaries: Mapped[list['PositionSummary']] = relationship('PositionSummary', back_populates='topic', cascade='all, delete-orphan')


class Speech(Base):
    __tablename__ = 'speeches'
    __table_args__ = (
        Index('ix_speeches_person_id_date', 'person_id', 'date'),
        UniqueConstraint('hansard_id', name='uq_speeches_hansard_id'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('persons.id', ondelete='CASCADE'), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    debate_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    house: Mapped[str] = mapped_column(String(50), nullable=False)
    hansard_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    person: Mapped[Person] = relationship('Person', back_populates='speeches')
    claims: Mapped[list['Claim']] = relationship('Claim', back_populates='speech', cascade='all, delete-orphan')


class Claim(Base):
    __tablename__ = 'claims'
    __table_args__ = (
        Index('ix_claims_person_id_date', 'person_id', 'date'),
        Index('ix_claims_person_id_topic_id', 'person_id', 'topic_id'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    speech_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('speeches.id', ondelete='CASCADE'), nullable=False)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('persons.id', ondelete='CASCADE'), nullable=False)
    claim_text: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    topic_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('topics.id', ondelete='SET NULL'), nullable=True)
    stance: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    speech: Mapped[Speech] = relationship('Speech', back_populates='claims')
    person: Mapped[Person] = relationship('Person', back_populates='claims')
    topic: Mapped[Topic | None] = relationship('Topic', back_populates='claims')
    contradictions_as_claim_a: Mapped[list['Contradiction']] = relationship(
        'Contradiction', back_populates='claim_a', foreign_keys='Contradiction.claim_a_id', cascade='all, delete-orphan'
    )
    contradictions_as_claim_b: Mapped[list['Contradiction']] = relationship(
        'Contradiction', back_populates='claim_b', foreign_keys='Contradiction.claim_b_id', cascade='all, delete-orphan'
    )


class Vote(Base):
    __tablename__ = 'votes'
    __table_args__ = (Index('ix_votes_person_id_date', 'person_id', 'date'),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('persons.id', ondelete='CASCADE'), nullable=False)
    division_id: Mapped[int] = mapped_column(Integer, nullable=False)
    division_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    vote: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    house: Mapped[str] = mapped_column(String(50), nullable=False)

    person: Mapped[Person] = relationship('Person', back_populates='votes')


class Contradiction(Base):
    __tablename__ = 'contradictions'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_a_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('claims.id', ondelete='CASCADE'), nullable=False)
    claim_b_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('claims.id', ondelete='CASCADE'), nullable=False)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('persons.id', ondelete='CASCADE'), nullable=False)
    topic_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('topics.id', ondelete='SET NULL'), nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    claim_a: Mapped[Claim] = relationship('Claim', foreign_keys=[claim_a_id], back_populates='contradictions_as_claim_a')
    claim_b: Mapped[Claim] = relationship('Claim', foreign_keys=[claim_b_id], back_populates='contradictions_as_claim_b')
    person: Mapped[Person] = relationship('Person', back_populates='contradictions')
    topic: Mapped[Topic | None] = relationship('Topic', back_populates='contradictions')


class PositionSummary(Base):
    __tablename__ = 'position_summaries'
    __table_args__ = (Index('ix_position_summaries_person_id_topic_id', 'person_id', 'topic_id'),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('persons.id', ondelete='CASCADE'), nullable=False)
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('topics.id', ondelete='CASCADE'), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    date_range_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_range_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    person: Mapped[Person] = relationship('Person', back_populates='position_summaries')
    topic: Mapped[Topic] = relationship('Topic', back_populates='position_summaries')
