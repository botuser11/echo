import re
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import Topic

TOPIC_SEEDS = {
    'NHS & Healthcare': ['nhs', 'hospital', 'doctor', 'nurse', 'health', 'patient', 'waiting list', 'ambulance', 'mental health'],
    'Immigration': ['immigration', 'migrant', 'asylum', 'border', 'visa', 'refugee', 'channel crossing', 'deportation'],
    'Economy & Cost of Living': ['economy', 'inflation', 'cost of living', 'wages', 'growth', 'gdp', 'recession', 'poverty'],
    'Housing': ['housing', 'homes', 'rent', 'mortgage', 'building', 'planning', 'homelessness', 'tenant'],
    'Education': ['education', 'school', 'teacher', 'university', 'student', 'curriculum', 'ofsted'],
    'Climate & Energy': ['climate', 'energy', 'net zero', 'renewable', 'carbon', 'green', 'fossil fuel', 'oil', 'gas'],
    'Crime & Policing': ['crime', 'police', 'prison', 'knife crime', 'antisocial', 'victim', 'sentence', 'court'],
    'Defence & Security': ['defence', 'military', 'army', 'nato', 'security', 'terrorism', 'armed forces'],
    'Brexit & EU': ['brexit', 'eu', 'european', 'trade deal', 'single market', 'customs'],
    'Tax & Public Spending': ['tax', 'taxation', 'budget', 'spending', 'austerity', 'fiscal', 'treasury', 'borrowing'],
    'Transport': ['transport', 'rail', 'train', 'bus', 'road', 'hs2', 'cycling'],
    'Foreign Policy': ['foreign', 'diplomatic', 'sanctions', 'ukraine', 'china', 'middle east', 'israel', 'gaza', 'india'],
    'Social Care': ['social care', 'care home', 'elderly', 'disability', 'carer'],
    'Employment & Workers Rights': ['employment', 'worker', 'union', 'strike', 'minimum wage', 'zero hours', 'pension'],
    'Technology & AI': ['technology', 'ai', 'artificial intelligence', 'data', 'digital', 'cyber', 'tech'],
    'Environment': ['environment', 'pollution', 'water', 'sewage', 'biodiversity', 'farming', 'agriculture'],
    'Levelling Up & Regional': ['levelling up', 'regional', 'north', 'devolution', 'council', 'local government'],
    'Children & Families': ['children', 'child', 'family', 'childcare', 'nursery', 'safeguarding'],
    'Democracy & Constitution': ['democracy', 'election', 'voting', 'lords', 'constitution', 'referendum'],
    'Culture & Media': ['culture', 'bbc', 'media', 'sport', 'arts', 'heritage'],
}


def slugify(name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return slug or 'topic'


def ensure_topics(db: Session) -> dict[str, Topic]:
    desired = {slugify(name): name for name in TOPIC_SEEDS}
    existing = db.scalars(select(Topic).where(Topic.slug.in_(list(desired.keys())))).all()
    topic_map = {topic.slug: topic for topic in existing}

    for slug, name in desired.items():
        if slug not in topic_map:
            topic = Topic(name=name, slug=slug, description=f'{name} topic detected by keyword matching')
            db.add(topic)
            db.flush()
            topic_map[slug] = topic

    return topic_map


def classify_claim(db: Session, claim_text: str) -> Topic | None:
    normalized = claim_text.lower()
    match_counts: dict[str, int] = defaultdict(int)

    for topic_name, keywords in TOPIC_SEEDS.items():
        for keyword in keywords:
            if keyword in normalized:
                match_counts[topic_name] += normalized.count(keyword)

    if not match_counts:
        return None

    best_topic_name = max(match_counts, key=match_counts.get)
    best_slug = slugify(best_topic_name)
    topic = db.scalar(select(Topic).where(Topic.slug == best_slug))
    if topic is None:
        topics = ensure_topics(db)
        topic = topics.get(best_slug)

    return topic
