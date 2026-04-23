"""
Bootstrap script for Echo — ingests speeches for ALL active MPs from Hansard API.
Resumable: if it crashes, re-running picks up where it left off.

Usage:
  docker-compose exec backend python -m app.scripts.bootstrap
"""

import asyncio
import logging
import time
import httpx
from sqlalchemy import func, select, text

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Hansard API config
HANSARD_SEARCH_URL = "https://hansard-api.parliament.uk/search.json"
REQUEST_TIMEOUT = 30.0
DELAY_BETWEEN_REQUESTS = 0.2
MAX_PAGES_PER_MP = 50  # Cap at 1000 speeches per MP (50 pages x 20 per page)
START_DATE = "2024-01-01"


def get_db():
    """Get a database session."""
    from app.db.session import SessionLocal
    return SessionLocal()


def get_all_persons_with_parliament_id(db):
    """Get all persons from the database that have a parliament_id."""
    from app.models.models import Person
    stmt = select(Person).where(Person.parliament_id.isnot(None)).order_by(Person.name)
    return db.execute(stmt).scalars().all()


def get_speech_count_for_person(db, person_id):
    """Count speeches with source_url for a person."""
    from app.models.models import Speech
    stmt = select(func.count(Speech.id)).where(
        Speech.person_id == person_id,
        Speech.source_url.isnot(None),
        Speech.source_url != ""
    )
    return db.scalar(stmt) or 0


def construct_source_url(house_raw, date_str, debate_section_ext_id, debate_title):
    """Construct Hansard URL from speech metadata."""
    if not debate_section_ext_id:
        return None
    
    # Extract house slug
    house_lower = house_raw.lower() if house_raw else "commons"
    if "commons" in house_lower:
        house_slug = "commons"
    elif "lords" in house_lower:
        house_slug = "lords"
    else:
        house_slug = "commons"
    
    # Clean debate title for URL
    title_slug = (debate_title or "debate").replace(" ", "").replace("'", "").replace(",", "").replace(":", "")
    
    return f"https://hansard.parliament.uk/{house_slug}/{date_str}/debates/{debate_section_ext_id}/{title_slug}"


def ingest_speeches_for_person(db, person, http_client):
    """Ingest speeches for a single person from Hansard API."""
    from app.models.models import Speech
    
    parliament_id = person.parliament_id
    imported = 0
    skip = 0
    take = 20
    total_contributions = None
    
    for page in range(MAX_PAGES_PER_MP):
        try:
            params = {
                "queryParameters.memberId": parliament_id,
                "queryParameters.startDate": START_DATE,
                "queryParameters.take": take,
                "queryParameters.skip": skip,
            }
            
            response = http_client.get(HANSARD_SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if total_contributions is None:
                total_contributions = data.get("TotalContributions", 0)
                if total_contributions == 0:
                    return 0  # No speeches for this MP
            
            contributions = data.get("Contributions", [])
            if not contributions:
                break
            
            for contrib in contributions:
                ext_id = contrib.get("ContributionExtId")
                if not ext_id:
                    continue
                
                # Check if speech already exists
                existing = db.execute(
                    select(Speech.id).where(Speech.hansard_id == ext_id)
                ).scalar()
                
                if existing:
                    continue
                
                # Extract fields
                sitting_date = contrib.get("SittingDate", "")[:10]  # "2026-04-13T00:00:00" -> "2026-04-13"
                full_text = contrib.get("ContributionTextFull", "")
                debate_title = contrib.get("DebateSection", "")
                house = f"{contrib.get('Section', 'Commons Chamber')} / {contrib.get('House', 'Commons')}"
                debate_section_ext_id = contrib.get("DebateSectionExtId", "")
                
                # Strip HTML tags from text
                import re
                clean_text = re.sub(r'<[^>]+>', '', full_text) if full_text else ""
                
                # Construct source URL
                source_url = construct_source_url(house, sitting_date, debate_section_ext_id, debate_title)
                
                speech = Speech(
                    person_id=person.id,
                    date=sitting_date,
                    source="hansard",
                    source_url=source_url,
                    full_text=clean_text,
                    debate_title=debate_title,
                    house=house,
                    hansard_id=ext_id,
                    debate_section_ext_id=debate_section_ext_id,
                    processed=False,
                )
                db.add(speech)
                imported += 1
            
            db.commit()
            skip += take
            
            if skip >= total_contributions:
                break
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
        except httpx.TimeoutException:
            logger.warning(f"  Timeout on page {page} for {person.name}, retrying...")
            time.sleep(2)
            continue
        except Exception as e:
            logger.warning(f"  Error on page {page} for {person.name}: {type(e).__name__}: {e}")
            db.rollback()
            break
    
    return imported


async def bootstrap_data():
    """Main bootstrap function — ingest speeches for all MPs, then run NLP."""
    db = get_db()
    
    # Get all persons
    persons = get_all_persons_with_parliament_id(db)
    total_persons = len(persons)
    logger.info(f"Found {total_persons} persons with parliament_id")
    
    # Track progress
    total_imported = 0
    skipped = 0
    processed = 0
    
    # Create HTTP client with proper timeout
    with httpx.Client(timeout=httpx.Timeout(REQUEST_TIMEOUT), follow_redirects=True) as http_client:
        for idx, person in enumerate(persons, 1):
            # Check if already has speeches with source URLs
            existing_count = get_speech_count_for_person(db, person.id)
            if existing_count > 0:
                skipped += 1
                if idx % 100 == 0:
                    logger.info(f"  Progress: {idx}/{total_persons} (skipped {skipped}, imported for {processed})")
                continue
            
            try:
                count = ingest_speeches_for_person(db, person, http_client)
                if count > 0:
                    processed += 1
                    total_imported += count
                    logger.info(f"  [{idx}/{total_persons}] {person.name}: {count} speeches imported")
                elif idx % 200 == 0:
                    logger.info(f"  Progress: {idx}/{total_persons} (skipped {skipped}, imported for {processed})")
            except Exception as e:
                logger.warning(f"  [{idx}/{total_persons}] {person.name}: FAILED — {type(e).__name__}: {e}")
                db.rollback()
                continue
    
    logger.info(f"Ingestion complete: {total_imported} new speeches for {processed} MPs (skipped {skipped} already done)")
    
    # Run NLP pipeline on all unprocessed speeches
    logger.info("Running NLP pipeline on unprocessed speeches...")
    try:
        from app.pipeline.processor import process_all
        nlp_result = process_all(db)
        logger.info(f"NLP complete: {nlp_result}")
    except Exception as e:
        logger.error(f"NLP pipeline failed: {type(e).__name__}: {e}")
    
    # Final stats
    speech_count = db.scalar(select(func.count()).select_from(text("speeches")))
    claim_count = db.scalar(select(func.count()).select_from(text("claims")))
    contradiction_count = db.scalar(select(func.count()).select_from(text("contradictions")))
    
    logger.info(f"Bootstrap complete: {speech_count} speeches, {claim_count} claims, {contradiction_count} contradictions")
    
    db.close()


if __name__ == "__main__":
    asyncio.run(bootstrap_data())