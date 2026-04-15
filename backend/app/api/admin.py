import logging

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.ingestion import ParliamentIngestionService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post('/ingest/members')
async def ingest_members(db: Session = Depends(get_db)) -> dict:
    service = ParliamentIngestionService(db)
    try:
        return await service.ingest_members()
    except Exception as exc:
        logger.exception('Failed to ingest members')
        raise HTTPException(status_code=500, detail=str(exc))


@router.post('/ingest/speeches/{parliament_id}')
async def ingest_speeches(
    parliament_id: int = Path(..., description='Parliament ID of the MP or Lord'),
    db: Session = Depends(get_db),
) -> dict:
    service = ParliamentIngestionService(db)
    try:
        return await service.ingest_speeches(parliament_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception('Failed to ingest speeches for %s', parliament_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post('/ingest/votes')
async def ingest_votes(db: Session = Depends(get_db)) -> dict:
    service = ParliamentIngestionService(db)
    try:
        return await service.ingest_votes()
    except Exception as exc:
        logger.exception('Failed to ingest votes')
        raise HTTPException(status_code=500, detail=str(exc))
