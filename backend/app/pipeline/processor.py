from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from sentence_transformers import SentenceTransformer
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.models import Claim, Contradiction, Person, PositionSummary, Speech, Topic
from app.pipeline.claim_extractor import detect_stance, extract_claims
from app.pipeline.contradiction_detector import detect_contradictions
from app.pipeline.topic_classifier import classify_claim, ensure_topics


def _build_summary(person: Person, topic: Topic, claims: list[Claim]) -> str:
    claim_snippets = ' '.join(claim.claim_text for claim in claims[:2])
    return (
        f"{person.name} made {len(claims)} claims about {topic.name}. "
        f"Key examples: {claim_snippets}"
    )


def _normalize_dates(claims: list[Claim]) -> tuple[date | None, date | None]:
    dates = [claim.date for claim in claims if claim.date is not None]
    if not dates:
        return None, None
    return min(dates), max(dates)


def _get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer('all-MiniLM-L6-v2')


def process_person(db: Session, person_id: Any) -> dict[str, Any]:
    person = db.get(Person, person_id)
    if person is None:
        raise ValueError(f'Person {person_id} not found')

    speeches = db.scalars(
        select(Speech).where(Speech.person_id == person_id, Speech.processed == False)
    ).all()
    if not speeches:
        return {
            'person_id': str(person_id),
            'processed_speeches': 0,
            'created_claims': 0,
            'contradictions': 0,
        }

    ensure_topics(db)

    created_claims: list[Claim] = []
    for speech in speeches:
        extracted = extract_claims(speech.full_text, speech.id, speech.person_id, speech.date)
        for item in extracted:
            claim = Claim(
                speech_id=speech.id,
                person_id=speech.person_id,
                claim_text=item['claim_text'],
                original_quote=item['original_quote'],
                confidence=item['confidence'],
                date=item['date'],
                stance=item['stance'],
            )
            db.add(claim)
            created_claims.append(claim)

    db.flush()

    for claim in created_claims:
        topic = classify_claim(db, claim.claim_text)
        if topic is not None:
            claim.topic_id = topic.id
        if claim.stance is None:
            claim.stance = detect_stance(claim.claim_text)

    if created_claims:
        model = _get_embedding_model()
        texts = [claim.claim_text for claim in created_claims]
        embeddings = model.encode(texts, show_progress_bar=False)
        for claim, embedding in zip(created_claims, embeddings):
            claim.embedding = list(map(float, embedding.tolist() if hasattr(embedding, 'tolist') else embedding))

    for speech in speeches:
        speech.processed = True

    db.commit()

    db.execute(delete(Contradiction).where(Contradiction.person_id == person_id))
    db.execute(delete(PositionSummary).where(PositionSummary.person_id == person_id))
    db.flush()

    all_claims = db.scalars(select(Claim).where(Claim.person_id == person_id).order_by(Claim.date)).all()
    contradictions = detect_contradictions(db, person, all_claims)
    for contradiction in contradictions:
        db.add(contradiction)

    topic_groups: dict[Any, list[Claim]] = defaultdict(list)
    for claim in all_claims:
        if claim.topic_id is not None:
            topic_groups[claim.topic_id].append(claim)

    for topic_id, claims in topic_groups.items():
        topic = db.get(Topic, topic_id)
        if topic is None:
            continue
        start_date, end_date = _normalize_dates(claims)
        summary_text = _build_summary(person, topic, claims)
        position_summary = PositionSummary(
            person_id=person_id,
            topic_id=topic_id,
            summary_text=summary_text,
            claim_count=len(claims),
            date_range_start=start_date,
            date_range_end=end_date,
        )
        db.add(position_summary)

    db.commit()

    return {
        'person_id': str(person_id),
        'processed_speeches': len(speeches),
        'created_claims': len(created_claims),
        'contradictions': len(contradictions),
    }


def process_all(db: Session) -> dict[str, Any]:
    persons = db.scalars(
        select(Person).join(Speech).where(Speech.processed == False).distinct()
    ).all()

    results = []
    for person in persons:
        results.append(process_person(db, person.id))

    return {
        'processed_people': len(results),
        'results': results,
    }
