import re
from typing import Any

import spacy

nlp = spacy.load('en_core_web_sm')

CLAIM_INDICATORS = [
    'we will',
    'I believe',
    'the government',
    'we are committed',
    'our policy',
    'we have delivered',
    'we must',
    'I support',
    'I oppose',
    'we reject',
    'this government has',
    'we pledge',
    'we promise',
]

STANCE_MARKERS = [
    'never',
    'always',
    'absolutely',
    'categorically',
    'unacceptable',
    'wrong',
    'right',
    'essential',
    'crucial',
]

POSITIVE_STANCE = [
    'support',
    'committed',
    'will deliver',
    'in favour',
    'back',
    'invest',
]

NEGATIVE_STANCE = [
    'oppose',
    'reject',
    'wrong',
    'cut',
    'against',
    'scrap',
    'abandon',
]


def _normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip()).lower()


def _contains_indicator(sentence: str) -> bool:
    lowered = _normalize(sentence)
    return any(indicator.lower() in lowered for indicator in CLAIM_INDICATORS + STANCE_MARKERS)


def detect_stance(text: str) -> str | None:
    lowered = _normalize(text)
    if any(marker in lowered for marker in POSITIVE_STANCE):
        return 'positive'
    if any(marker in lowered for marker in NEGATIVE_STANCE):
        return 'negative'
    return None


def extract_claims(full_text: str, speech_id: Any, person_id: Any, speech_date: Any) -> list[dict[str, Any]]:
    doc = nlp(full_text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    claims: list[dict[str, Any]] = []

    for index, sentence in enumerate(sentences):
        if len(sentence) > 5000:
            continue
        if not _contains_indicator(sentence):
            continue

        surrounding = []
        if index > 0:
            surrounding.append(sentences[index - 1])
        surrounding.append(sentence)
        if index + 1 < len(sentences):
            surrounding.append(sentences[index + 1])

        original_quote = ' '.join(surrounding).strip()
        claim = {
            'speech_id': speech_id,
            'person_id': person_id,
            'claim_text': sentence,
            'original_quote': original_quote,
            'confidence': 0.8,
            'date': speech_date,
            'stance': detect_stance(sentence),
        }
        claims.append(claim)

    return claims
