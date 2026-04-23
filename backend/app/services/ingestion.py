import asyncio
import html
import logging
import re
from datetime import date, datetime
from typing import Any

import httpx
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.models import Person, Speech, Vote


class ParliamentIngestionService:
    BASE_URL_MEMBERS = 'https://members-api.parliament.uk/api/Members/Search'
    BASE_URL_SPEECHES = 'https://hansard-api.parliament.uk/search.json'
    BASE_URL_DIVISIONS = 'https://commonsvotes-api.parliament.uk/data/divisions.json/search'
    DIVISION_DETAIL_URL = 'https://commonsvotes-api.parliament.uk/data/divisions/{division_id}.json'

    RETRIES = 3
    BACKOFF_FACTOR = 0.5
    REQUEST_DELAY = 0.5

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _request_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(1, self.RETRIES + 1):
            try:
                return await run_in_threadpool(self._sync_request_json, url, params)
            except Exception as exc:
                self.logger.error(
                    f'HTTP request failed on attempt {attempt} for {url}: {type(exc).__name__}: {str(exc)}'
                )
                if attempt == self.RETRIES:
                    raise
                backoff = self.BACKOFF_FACTOR * 2 ** (attempt - 1)
                self.logger.warning(
                    'Retrying in %s seconds after error on attempt %s for %s.',
                    backoff,
                    attempt,
                    url,
                )
                await asyncio.sleep(backoff)
        raise RuntimeError('Request retry loop exited unexpectedly')

    def _sync_request_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=httpx.Timeout(30.0), verify=True, follow_redirects=True) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _get_nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
        return value if value is not None else default

    @staticmethod
    def _parse_date(value: Any) -> date | None:
        if not value:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        try:
            parsed = datetime.fromisoformat(str(value))
            return parsed.date()
        except ValueError:
            try:
                return datetime.strptime(str(value), '%Y-%m-%d').date()
            except ValueError:
                return None

    @staticmethod
    def _strip_html(content: str) -> str:
        text = re.sub(r'<[^>]+>', '', content)
        return html.unescape(text).strip()

    async def ingest_members(self) -> dict[str, int]:
        imported = 0
        for house in (1, 2):
            skip = 0
            while True:
                params = {
                    'House': house,
                    'IsCurrentMember': 'true',
                    'take': 100,
                    'skip': skip,
                }
                payload = await self._request_json(self.BASE_URL_MEMBERS, params)
                items = payload.get('items') or payload.get('results') or []
                if not items:
                    break

                for item in items:
                    member = item.get('value', item)
                    parliament_id = self._get_nested(member, 'memberId') or self._get_nested(member, 'id')
                    if parliament_id is None:
                        continue

                    if await run_in_threadpool(self._person_exists, parliament_id):
                        continue

                    person = Person(
                        name=self._get_nested(member, 'nameDisplayAs') or 'Unknown',
                        party=self._get_nested(member, 'latestParty', 'name'),
                        constituency=self._get_nested(member, 'latestHouseMembership', 'membershipFrom'),
                        house='commons' if house == 1 else 'lords',
                        role=self._get_nested(member, 'role'),
                        photo_url=self._get_nested(member, 'thumbnailUrl'),
                        parliament_id=int(parliament_id),
                        active=True,
                    )
                    await run_in_threadpool(self._save_person, person)
                    imported += 1

                total = payload.get('totalResults') or payload.get('count') or len(items)
                skip += len(items)
                if skip >= int(total):
                    break

                await asyncio.sleep(self.REQUEST_DELAY)

        return {'imported_members': imported}

    async def ingest_speeches(self, parliament_id: int) -> dict[str, int]:
        person = await run_in_threadpool(self._get_person_by_parliament_id, parliament_id)
        if not person:
            raise ValueError(f'Person with parliament_id {parliament_id} not found')

        saved = 0
        skip = 0
        take = 20
        total_contributions = None
        page = 0

        while total_contributions is None or skip < total_contributions:
            page += 1
            params = {
                'queryParameters.memberId': parliament_id,
                'queryParameters.startDate': '2024-01-01',
                'queryParameters.skip': skip,
                'queryParameters.take': take,
            }
            payload = await self._request_json(self.BASE_URL_SPEECHES, params)
            contributions = payload.get('Contributions') or []
            if total_contributions is None:
                total_contributions = payload.get('TotalContributions') or 0

            total_pages = (
                (int(total_contributions) + take - 1) // take if total_contributions else None
            )
            self.logger.info(
                'Fetching page %s of %s for parliament_id %s; imported %s speeches so far',
                page,
                total_pages or '?',
                parliament_id,
                saved,
            )

            if not contributions:
                break

            for contribution in contributions:
                hansard_id = self._get_nested(contribution, 'ContributionExtId')
                if not hansard_id:
                    continue

                full_text = self._get_nested(contribution, 'ContributionTextFull')
                if not full_text:
                    continue

                if await run_in_threadpool(self._speech_exists, hansard_id):
                    continue

                speech_date = self._parse_date(self._get_nested(contribution, 'SittingDate'))
                debate_title = self._get_nested(contribution, 'DebateSection')
                section = self._get_nested(contribution, 'Section')
                house = self._get_nested(contribution, 'House')
                house_value = ' / '.join(filter(None, [section, house])) or 'commons'

                # Extract debate_section_ext_id and construct source_url
                debate_section_ext_id = self._get_nested(contribution, 'DebateSectionExtId')
                source_url = None
                if debate_section_ext_id and speech_date and debate_title:
                    # Map house to slug: take last word and lowercase
                    house_slug = house_value.split()[-1].lower() if house_value else 'commons'
                    # Remove spaces from debate title
                    debate_title_slug = re.sub(r'\s+', '', debate_title)
                    # Construct Hansard URL
                    source_url = f"https://hansard.parliament.uk/{house_slug}/{speech_date}/debates/{debate_section_ext_id}/{debate_title_slug}"

                speech = Speech(
                    person_id=person.id,
                    date=speech_date or date.today(),
                    source='hansard',
                    source_url=source_url,
                    full_text=self._strip_html(str(full_text)),
                    debate_title=debate_title,
                    house=house_value,
                    hansard_id=str(hansard_id),
                    debate_section_ext_id=debate_section_ext_id,
                    processed=False,
                )
                await run_in_threadpool(self._save_speech, speech)
                saved += 1

                if saved % 100 == 0 and total_contributions:
                    self.logger.info('Imported %s of %s speeches...', saved, total_contributions)

            skip += len(contributions)
            if total_contributions and skip >= int(total_contributions):
                break

            await asyncio.sleep(self.REQUEST_DELAY)

        return {'imported_speeches': saved}

    async def ingest_votes(self, start_date: str = '2024-01-01') -> dict[str, int]:
        imported = 0
        skip = 0
        while True:
            params = {
                'queryParameters.startDate': start_date,
                'take': 100,
                'skip': skip,
            }
            payload = await self._request_json(self.BASE_URL_DIVISIONS, params)
            divisions = payload.get('items') or payload.get('results') or []
            if not divisions:
                break

            for division in divisions:
                division_id = self._get_nested(division, 'id') or self._get_nested(division, 'divisionId')
                if not division_id:
                    continue

                detail_url = self.DIVISION_DETAIL_URL.format(division_id=division_id)
                division_payload = await self._request_json(detail_url, {})
                division_title = self._get_nested(division_payload, 'title') or division_payload.get('name')
                division_date = self._parse_date(self._get_nested(division_payload, 'date'))
                house = self._get_nested(division_payload, 'house') or division_payload.get('divisionHouse') or 'commons'

                members = (
                    division_payload.get('divisionMembers')
                    or division_payload.get('members')
                    or division_payload.get('divisionMember')
                    or []
                )
                for member_vote in members:
                    parliament_member_id = (
                        self._get_nested(member_vote, 'memberId')
                        or self._get_nested(member_vote, 'id')
                    )
                    if parliament_member_id is None:
                        continue

                    person = await run_in_threadpool(self._get_person_by_parliament_id, int(parliament_member_id))
                    if not person:
                        continue

                    vote_value = (
                        self._get_nested(member_vote, 'vote')
                        or self._get_nested(member_vote, 'divisionVote')
                        or self._get_nested(member_vote, 'voteText')
                    )
                    if vote_value is None:
                        continue

                    if await run_in_threadpool(self._vote_exists, person.id, division_id):
                        continue

                    vote = Vote(
                        person_id=person.id,
                        division_id=int(division_id),
                        division_title=str(division_title) if division_title else '',
                        vote=str(vote_value),
                        date=division_date or date.today(),
                        house=str(house),
                    )
                    await run_in_threadpool(self._save_vote, vote)
                    imported += 1
                await asyncio.sleep(self.REQUEST_DELAY)

            total = payload.get('totalResults') or payload.get('count') or len(divisions)
            skip += len(divisions)
            if skip >= int(total):
                break
            await asyncio.sleep(self.REQUEST_DELAY)

        return {'imported_votes': imported}

    def _person_exists(self, parliament_id: int) -> bool:
        return bool(self.db.query(Person).filter(Person.parliament_id == int(parliament_id)).first())

    def _save_person(self, person: Person) -> None:
        self.db.add(person)
        self.db.commit()

    def _get_person_by_parliament_id(self, parliament_id: int) -> Person | None:
        return self.db.query(Person).filter(Person.parliament_id == int(parliament_id)).first()

    def _speech_exists(self, hansard_id: str) -> bool:
        return bool(self.db.query(Speech).filter(Speech.hansard_id == str(hansard_id)).first())

    def _save_speech(self, speech: Speech) -> None:
        self.db.add(speech)
        self.db.commit()

    def _vote_exists(self, person_id: Any, division_id: Any) -> bool:
        return bool(
            self.db.query(Vote)
            .filter(Vote.person_id == person_id, Vote.division_id == int(division_id))
            .first()
        )

    def _save_vote(self, vote: Vote) -> None:
        self.db.add(vote)
        self.db.commit()
