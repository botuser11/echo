from datetime import date as DateType, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, UUID4


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int


class PersonSummary(BaseModel):
    id: UUID4
    name: str
    party: Optional[str] = None
    constituency: Optional[str] = None
    house: str
    role: Optional[str] = None
    photo_url: Optional[str] = None
    speech_count: int = 0
    claim_count: int = 0
    latest_speech_date: Optional[DateType] = None


class PersonTopicPosition(BaseModel):
    id: UUID4
    name: str
    slug: str
    claim_count: int


class SpeechSummary(BaseModel):
    id: UUID4
    date: DateType
    debate_title: Optional[str] = None
    full_text: str
    claim_count: int
    source_url: Optional[str] = None


class ClaimSummary(BaseModel):
    id: UUID4
    claim_text: str
    original_quote: Optional[str] = None
    topic: Optional[str] = None
    stance: Optional[str] = None
    confidence: Optional[float] = None
    date: Optional[DateType] = None
    source_url: Optional[str] = None


class ShortClaim(BaseModel):
    id: UUID4
    date: Optional[DateType] = None
    stance: Optional[str] = None
    claim_text: str
    original_quote: Optional[str] = None
    confidence: Optional[float] = None


class ContradictionClaimData(BaseModel):
    id: UUID4
    date: Optional[DateType] = None
    claim_text: str
    original_quote: Optional[str] = None
    topic: Optional[str] = None
    stance: Optional[str] = None


class ContradictionResponse(BaseModel):
    id: UUID4
    claim_a: ContradictionClaimData
    claim_b: ContradictionClaimData
    explanation: Optional[str] = None
    severity: Optional[float] = None
    status: str
    detected_at: datetime


class PersonDetail(PersonSummary):
    parliament_id: int
    active: bool
    created_at: datetime
    updated_at: datetime
    topic_positions: List[PersonTopicPosition]
    recent_speeches: List[SpeechSummary]
    contradiction_count: int


class TimelineItem(BaseModel):
    id: UUID4
    date: Optional[DateType] = None
    stance: Optional[str] = None
    claim_text: str
    original_quote: Optional[str] = None
    confidence: Optional[float] = None


class SearchResult(BaseModel):
    id: UUID4
    claim_text: str
    original_quote: Optional[str] = None
    topic: Optional[str] = None
    stance: Optional[str] = None
    confidence: Optional[float] = None
    date: Optional[DateType] = None
    source_url: Optional[str] = None
    person_id: UUID4
    person_name: str
    person_photo_url: Optional[str] = None
    score: Optional[float] = None


class ComparePersonSummary(BaseModel):
    id: UUID4
    name: str
    party: Optional[str] = None
    photo_url: Optional[str] = None


class CompareResponse(BaseModel):
    topic_slug: str
    topic_name: Optional[str] = None
    person_a: ComparePersonSummary
    person_b: ComparePersonSummary
    claims_a: List[ShortClaim]
    claims_b: List[ShortClaim]


class TopicNode(BaseModel):
    id: UUID4
    name: str
    slug: str
    description: Optional[str] = None
    claim_count: int = 0
    children: List["TopicNode"] = Field(default_factory=list)
TopicNode.model_rebuild()

class PaginatedPersonResponse(BaseModel):
    data: List[PersonSummary]
    meta: PaginationMeta


class PaginatedSpeechResponse(BaseModel):
    data: List[SpeechSummary]
    meta: PaginationMeta


class PaginatedClaimResponse(BaseModel):
    data: List[ClaimSummary]
    meta: PaginationMeta


class PaginatedSearchResponse(BaseModel):
    data: List[SearchResult]
    meta: PaginationMeta
