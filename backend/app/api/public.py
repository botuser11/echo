from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import UUID4
from sqlalchemy import and_, asc, case, desc, func, or_, select
from sqlalchemy.orm import aliased, Session

from app.db.session import get_db
from app.models import Claim, Contradiction, Person, Speech, Topic
from app.schemas.public import (
    ClaimSummary,
    ComparePersonSummary,
    CompareResponse,
    ContradictionClaimData,
    ContradictionResponse,
    PaginatedClaimResponse,
    PaginatedPersonResponse,
    PaginatedSearchResponse,
    PaginatedSpeechResponse,
    PersonDetail,
    PersonSummary,
    PersonTopicPosition,
    SearchResult,
    ShortClaim,
    SpeechSummary,
    TimelineItem,
    TopicNode,
    PaginationMeta,
)

router = APIRouter(tags=['Public'])


def _paginate(page: int, page_size: int) -> tuple[int, int]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    offset = (page - 1) * page_size
    return offset, page_size


def _add_cache_headers(response: Response) -> None:
    response.headers['Cache-Control'] = 'public, max-age=60'


@router.get('/persons', response_model=PaginatedPersonResponse)
async def list_persons(
    response: Response,
    db: Session = Depends(get_db),
    house: Optional[str] = Query(None, description='commons or lords'),
    party: Optional[str] = Query(None, description='Party name filter'),
    search: Optional[str] = Query(None, description='Search by name contains'),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: Optional[str] = Query('name', pattern='^(name|speech_count_desc)$'),
):
    offset, page_limit = _paginate(page, page_size)
    speech_stats = (
        select(
            Speech.person_id.label('person_id'),
            func.count(Speech.id).label('speech_count'),
            func.max(Speech.date).label('latest_speech_date'),
        )
        .group_by(Speech.person_id)
        .subquery()
    )

    claim_stats = (
        select(
            Claim.person_id.label('person_id'),
            func.count(Claim.id).label('claim_count'),
        )
        .group_by(Claim.person_id)
        .subquery()
    )

    filters = []
    if house:
        filters.append(Person.house == house)
    if party:
        filters.append(Person.party == party)
    if search:
        filters.append(Person.name.ilike(f'%{search}%'))

    stmt = (
        select(
            Person,
            func.coalesce(speech_stats.c.speech_count, 0).label('speech_count'),
            speech_stats.c.latest_speech_date.label('latest_speech_date'),
            func.coalesce(claim_stats.c.claim_count, 0).label('claim_count'),
        )
        .outerjoin(speech_stats, Person.id == speech_stats.c.person_id)
        .outerjoin(claim_stats, Person.id == claim_stats.c.person_id)
    )

    if filters:
        stmt = stmt.where(and_(*filters))

    if sort == 'speech_count_desc':
        stmt = stmt.order_by(desc(func.coalesce(speech_stats.c.speech_count, 0)), asc(Person.name))
    else:
        stmt = stmt.order_by(asc(Person.name))

    total = db.scalar(select(func.count()).select_from(Person).where(and_(*filters))) if filters else db.scalar(select(func.count()).select_from(Person))
    results = db.execute(stmt.offset(offset).limit(page_limit)).all()
    people = [
        PersonSummary(
            id=row.Person.id,
            name=row.Person.name,
            party=row.Person.party,
            constituency=row.Person.constituency,
            house=row.Person.house,
            role=row.Person.role,
            photo_url=row.Person.photo_url,
            speech_count=int(row.speech_count or 0),
            claim_count=int(row.claim_count or 0),
            latest_speech_date=row.latest_speech_date,
        )
        for row in results
    ]

    _add_cache_headers(response)
    return {
        'data': people,
        'meta': PaginationMeta(page=page, page_size=page_limit, total=int(total or 0)),
    }


@router.get('/persons/{person_id}', response_model=PersonDetail)
async def get_person(person_id: UUID4, response: Response, db: Session = Depends(get_db)):
    person = db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Person not found')

    topic_rows = db.execute(
        select(
            Topic.id,
            Topic.name,
            Topic.slug,
            func.count(Claim.id).label('claim_count'),
        )
        .join(Claim, Claim.topic_id == Topic.id)
        .where(Claim.person_id == person_id)
        .group_by(Topic.id)
        .order_by(Topic.name)
    ).all()

    topic_positions = [
        PersonTopicPosition(
            id=row.id,
            name=row.name,
            slug=row.slug,
            claim_count=int(row.claim_count),
        )
        for row in topic_rows
    ]

    recent_speeches = [
        SpeechSummary(
            id=s.id,
            date=s.date,
            debate_title=s.debate_title,
            full_text=s.full_text[:500],
            claim_count=db.scalar(select(func.count()).select_from(Claim).where(Claim.speech_id == s.id)) or 0,
            source_url=s.source_url,
        )
        for s in db.scalars(
            select(Speech)
            .where(Speech.person_id == person_id)
            .order_by(desc(Speech.date))
            .limit(10)
        )
    ]

    contradiction_count = db.scalar(
        select(func.count()).select_from(Contradiction).where(Contradiction.person_id == person_id)
    )

    person_detail = PersonDetail(
        id=person.id,
        name=person.name,
        party=person.party,
        constituency=person.constituency,
        house=person.house,
        role=person.role,
        photo_url=person.photo_url,
        speech_count=len(person.speeches),
        latest_speech_date=max((speech.date for speech in person.speeches), default=None),
        parliament_id=person.parliament_id,
        active=person.active,
        created_at=person.created_at,
        updated_at=person.updated_at,
        topic_positions=topic_positions,
        recent_speeches=recent_speeches,
        contradiction_count=int(contradiction_count or 0),
    )

    _add_cache_headers(response)
    return person_detail


@router.get('/persons/{person_id}/speeches', response_model=PaginatedSpeechResponse)
async def list_person_speeches(
    person_id: UUID4,
    response: Response,
    db: Session = Depends(get_db),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    topic: Optional[str] = Query(None, description='Topic slug filter'),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    person = db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Person not found')

    offset, page_limit = _paginate(page, page_size)
    claim_alias = Claim

    base_stmt = (
        select(
            Speech,
            func.count(claim_alias.id).label('claim_count'),
        )
        .outerjoin(claim_alias, claim_alias.speech_id == Speech.id)
        .where(Speech.person_id == person_id)
    )

    count_inner = (
        select(Speech.id)
        .outerjoin(claim_alias, claim_alias.speech_id == Speech.id)
        .where(Speech.person_id == person_id)
    )

    if date_from:
        base_stmt = base_stmt.where(Speech.date >= date_from)
        count_inner = count_inner.where(Speech.date >= date_from)
    if date_to:
        base_stmt = base_stmt.where(Speech.date <= date_to)
        count_inner = count_inner.where(Speech.date <= date_to)
    if topic:
        base_stmt = base_stmt.join(claim_alias, claim_alias.speech_id == Speech.id).join(Topic, Topic.id == claim_alias.topic_id)
        base_stmt = base_stmt.where(Topic.slug == topic)
        count_inner = count_inner.join(claim_alias, claim_alias.speech_id == Speech.id).join(Topic, Topic.id == claim_alias.topic_id)
        count_inner = count_inner.where(Topic.slug == topic)

    stmt = base_stmt.group_by(Speech.id).order_by(desc(Speech.date))
    total_stmt = select(func.count()).select_from(count_inner.group_by(Speech.id).subquery())
    rows = db.execute(stmt.offset(offset).limit(page_limit)).all()
    total = db.scalar(total_stmt)

    speeches = [
        SpeechSummary(
            id=row.Speech.id,
            date=row.Speech.date,
            debate_title=row.Speech.debate_title,
            full_text=row.Speech.full_text[:500],
            claim_count=int(row.claim_count or 0),
            source_url=row.Speech.source_url,
        )
        for row in rows
    ]

    _add_cache_headers(response)
    return {
        'data': speeches,
        'meta': PaginationMeta(page=page, page_size=page_limit, total=int(total or 0)),
    }


@router.get('/persons/{person_id}/claims', response_model=PaginatedClaimResponse)
async def list_person_claims(
    person_id: UUID4,
    response: Response,
    db: Session = Depends(get_db),
    topic: Optional[str] = Query(None, description='Topic slug filter'),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    stance: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    person = db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Person not found')

    offset, page_limit = _paginate(page, page_size)
    claim_filters = [Claim.person_id == person_id]
    if topic:
        claim_filters.append(Topic.slug == topic)
    if date_from:
        claim_filters.append(Claim.date >= date_from)
    if date_to:
        claim_filters.append(Claim.date <= date_to)
    if stance:
        claim_filters.append(Claim.stance == stance)

    stmt = (
        select(
            Claim,
            Topic.name.label('topic_name'),
            Speech.source_url.label('source_url'),
        )
        .join(Speech, Claim.speech)
        .outerjoin(Topic, Claim.topic_id == Topic.id)
        .where(and_(*claim_filters))
        .order_by(desc(Claim.date))
    )

    total_stmt = select(func.count()).select_from(
        select(Claim.id)
        .outerjoin(Topic, Claim.topic_id == Topic.id)
        .where(and_(*claim_filters))
        .subquery()
    )

    rows = db.execute(stmt.offset(offset).limit(page_limit)).all()
    total = db.scalar(total_stmt)

    claims = [
        ClaimSummary(
            id=row.Claim.id,
            claim_text=row.Claim.claim_text,
            original_quote=row.Claim.original_quote,
            topic=row.topic_name,
            stance=row.Claim.stance,
            confidence=row.Claim.confidence,
            date=row.Claim.date,
            source_url=row.source_url,
        )
        for row in rows
    ]

    _add_cache_headers(response)
    return {
        'data': claims,
        'meta': PaginationMeta(page=page, page_size=page_limit, total=int(total or 0)),
    }


@router.get('/persons/{person_id}/contradictions', response_model=list[ContradictionResponse])
async def list_person_contradictions(
    person_id: UUID4,
    response: Response,
    db: Session = Depends(get_db),
):
    person = db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Person not found')

    claim_a = aliased(Claim)
    claim_b = aliased(Claim)
    stmt = (
        select(Contradiction, claim_a, claim_b)
        .select_from(Contradiction)
        .join(claim_a, Contradiction.claim_a_id == claim_a.id)
        .join(claim_b, Contradiction.claim_b_id == claim_b.id)
        .where(Contradiction.person_id == person_id)
        .order_by(desc(Contradiction.detected_at))
    )
    rows = db.execute(stmt).all()

    contradictions = []
    for row in rows:
        claim_a_row = row[1]
        claim_b_row = row[2]
        contradictions.append(
            ContradictionResponse(
                id=row[0].id,
                claim_a=ContradictionClaimData(
                    id=claim_a_row.id,
                    date=claim_a_row.date,
                    claim_text=claim_a_row.claim_text,
                    original_quote=claim_a_row.original_quote,
                    topic=claim_a_row.topic.name if claim_a_row.topic else None,
                    stance=claim_a_row.stance,
                ),
                claim_b=ContradictionClaimData(
                    id=claim_b_row.id,
                    date=claim_b_row.date,
                    claim_text=claim_b_row.claim_text,
                    original_quote=claim_b_row.original_quote,
                    topic=claim_b_row.topic.name if claim_b_row.topic else None,
                    stance=claim_b_row.stance,
                ),
                explanation=row[0].explanation,
                severity=row[0].severity,
                status=row[0].status,
                detected_at=row[0].detected_at,
            )
        )

    _add_cache_headers(response)
    return contradictions


@router.get('/persons/{person_id}/timeline/{topic_slug}', response_model=list[TimelineItem])
async def person_timeline(
    person_id: UUID4,
    topic_slug: str,
    response: Response,
    db: Session = Depends(get_db),
):
    person = db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Person not found')

    topic = db.scalar(select(Topic).where(Topic.slug == topic_slug))
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Topic not found')

    rows = db.scalars(
        select(Claim)
        .where(Claim.person_id == person_id, Claim.topic_id == topic.id)
        .order_by(asc(Claim.date))
    ).all()

    timeline = [
        TimelineItem(
            id=claim.id,
            date=claim.date,
            stance=claim.stance,
            claim_text=claim.claim_text,
            original_quote=claim.original_quote,
            confidence=claim.confidence,
        )
        for claim in rows
    ]

    _add_cache_headers(response)
    return timeline


@router.get('/search', response_model=PaginatedSearchResponse)
async def search_claims(
    response: Response,
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=1, description='Search query string'),
    person_id: Optional[UUID4] = Query(None, description='Optional person filter'),
    topic: Optional[str] = Query(None, description='Optional topic slug filter'),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    offset, page_limit = _paginate(page, page_size)
    filters = [
        or_(
            Claim.claim_text.ilike(f'%{q}%'),
            Claim.original_quote.ilike(f'%{q}%'),
        )
    ]
    if person_id:
        filters.append(Claim.person_id == person_id)
    if topic:
        filters.append(Topic.slug == topic)

    stmt = (
        select(
            Claim,
            Person.name.label('person_name'),
            Person.photo_url.label('person_photo_url'),
            Topic.name.label('topic_name'),
            Speech.source_url.label('source_url'),
        )
        .join(Person, Claim.person)
        .join(Speech, Claim.speech)
        .outerjoin(Topic, Claim.topic_id == Topic.id)
        .where(and_(*filters))
        .order_by(desc(Claim.date))
    )

    count_stmt = select(func.count()).select_from(
        select(Claim.id)
        .outerjoin(Topic, Claim.topic_id == Topic.id)
        .where(and_(*filters))
        .subquery()
    )

    rows = db.execute(stmt.offset(offset).limit(page_limit)).all()
    total = db.scalar(count_stmt)

    results = [
        SearchResult(
            id=row.Claim.id,
            claim_text=row.Claim.claim_text,
            original_quote=row.Claim.original_quote,
            topic=row.topic_name,
            stance=row.Claim.stance,
            confidence=row.Claim.confidence,
            date=row.Claim.date,
            source_url=row.source_url,
            person_id=row.Claim.person_id,
            person_name=row.person_name,
            person_photo_url=row.person_photo_url,
            score=None,
        )
        for row in rows
    ]

    _add_cache_headers(response)
    return {
        'data': results,
        'meta': PaginationMeta(page=page, page_size=page_limit, total=int(total or 0)),
    }


@router.get('/compare', response_model=CompareResponse)
async def compare_persons(
    response: Response,
    db: Session = Depends(get_db),
    person_a_id: UUID4 = Query(...),
    person_b_id: UUID4 = Query(...),
    topic_slug: str = Query(...),
):
    person_a = db.get(Person, person_a_id)
    person_b = db.get(Person, person_b_id)
    if not person_a or not person_b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='One or both persons not found')

    topic = db.scalar(select(Topic).where(Topic.slug == topic_slug))
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Topic not found')

    def load_claims(person_id: UUID4) -> list[ShortClaim]:
        claims = db.scalars(
            select(Claim)
            .where(Claim.person_id == person_id, Claim.topic_id == topic.id)
            .order_by(asc(Claim.date))
        ).all()
        return [
            ShortClaim(
                id=claim.id,
                date=claim.date,
                stance=claim.stance,
                claim_text=claim.claim_text,
                original_quote=claim.original_quote,
                confidence=claim.confidence,
            )
            for claim in claims
        ]

    result = CompareResponse(
        topic_slug=topic.slug,
        topic_name=topic.name,
        person_a=ComparePersonSummary(id=person_a.id, name=person_a.name, party=person_a.party, photo_url=person_a.photo_url),
        person_b=ComparePersonSummary(id=person_b.id, name=person_b.name, party=person_b.party, photo_url=person_b.photo_url),
        claims_a=load_claims(person_a_id),
        claims_b=load_claims(person_b_id),
    )

    _add_cache_headers(response)
    return result


@router.get('/topics', response_model=list[TopicNode])
async def list_topics(response: Response, db: Session = Depends(get_db)):
    counts = (
        select(Claim.topic_id, func.count(Claim.id).label('claim_count'))
        .group_by(Claim.topic_id)
        .subquery()
    )

    rows = db.execute(
        select(
            Topic,
            func.coalesce(counts.c.claim_count, 0).label('claim_count'),
        )
        .outerjoin(counts, Topic.id == counts.c.topic_id)
        .order_by(asc(Topic.name))
    ).all()

    nodes: dict[UUID4, TopicNode] = {}
    roots: list[TopicNode] = []
    for row in rows:
        topic = row.Topic
        node = TopicNode(
            id=topic.id,
            name=topic.name,
            slug=topic.slug,
            description=topic.description,
            claim_count=int(row.claim_count or 0),
        )
        nodes[topic.id] = node

    for row in rows:
        topic = row.Topic
        node = nodes[topic.id]
        if topic.parent_topic_id and topic.parent_topic_id in nodes:
            nodes[topic.parent_topic_id].children.append(node)
        else:
            roots.append(node)

    _add_cache_headers(response)
    return roots
