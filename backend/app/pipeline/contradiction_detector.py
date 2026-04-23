from collections import defaultdict
from datetime import timedelta

from sqlalchemy import select

from app.models.models import Claim, Contradiction, Person

POSITIVE_WORDS = ['support', 'committed', 'will deliver', 'in favour', 'back', 'invest']
NEGATIVE_WORDS = ['oppose', 'reject', 'wrong', 'cut', 'against', 'scrap', 'abandon']


def _normalize(text: str) -> str:
    return text.lower()


def _stance_from_text(text: str) -> str | None:
    normalized = _normalize(text)
    has_positive = any(word in normalized for word in POSITIVE_WORDS)
    has_negative = any(word in normalized for word in NEGATIVE_WORDS)

    if has_positive and not has_negative:
        return 'positive'
    if has_negative and not has_positive:
        return 'negative'
    return None


def detect_contradictions(db, person: Person, claims: list[Claim]) -> list[Contradiction]:
    claims_by_topic: dict[str, list[Claim]] = defaultdict(list)
    existing_pairs = set()

    existing = db.scalars(
        select(Contradiction.claim_a_id, Contradiction.claim_b_id).where(Contradiction.person_id == person.id)
    ).all()
    for claim_a_id, claim_b_id in existing:
        existing_pairs.add((str(claim_a_id), str(claim_b_id)))
        existing_pairs.add((str(claim_b_id), str(claim_a_id)))

    for claim in claims:
        if claim.topic_id is None:
            continue
        claims_by_topic[str(claim.topic_id)].append(claim)

    contradictions: list[Contradiction] = []

    for topic_id, topic_claims in claims_by_topic.items():
        topic_claims.sort(key=lambda claim: claim.date or claim.created_at)

        for i, first in enumerate(topic_claims):
            for second in topic_claims[i + 1:]:
                if first.date is None or second.date is None:
                    continue
                if abs((second.date - first.date).days) < 30:
                    continue

                first_stance = first.stance or _stance_from_text(first.claim_text)
                second_stance = second.stance or _stance_from_text(second.claim_text)
                if first_stance == second_stance or first_stance is None or second_stance is None:
                    continue

                if {first_stance, second_stance} == {'positive', 'negative'}:
                    pair = (str(first.id), str(second.id))
                    if pair in existing_pairs:
                        continue

                    explanation = (
                        f"On {first.date}, {person.name} said: '{first.claim_text}'. "
                        f"But on {second.date}, they said: '{second.claim_text}'. "
                        f"These statements appear to conflict on the topic of {first.topic.name if first.topic else 'this issue'}."
                    )

                    contradiction = Contradiction(
                        claim_a_id=first.id,
                        claim_b_id=second.id,
                        person_id=person.id,
                        topic_id=first.topic_id,
                        explanation=explanation,
                        severity=0.7,
                        status='detected',
                    )
                    contradictions.append(contradiction)
                    existing_pairs.add(pair)
                    existing_pairs.add((pair[1], pair[0]))

    return contradictions
