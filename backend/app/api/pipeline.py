import logging
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Claim, Contradiction, Speech
from app.pipeline.processor import process_all, process_person

router = APIRouter(prefix='/pipeline')
logger = logging.getLogger(__name__)


@router.post('/process/{person_id}')
def process_person_pipeline(
    person_id: str = Path(..., description='Person UUID to process'),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return process_person(db, person_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception('Failed to process person %s', person_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post('/process-all')
def process_all_pipeline(db: Session = Depends(get_db)) -> dict:
    try:
        return process_all(db)
    except Exception as exc:
        logger.exception('Failed to process all people')
        raise HTTPException(status_code=500, detail=str(exc))


@router.get('/status')
def pipeline_status(db: Session = Depends(get_db)) -> dict:
    total_speeches = db.scalar(select(func.count()).select_from(Speech)) or 0
    processed_speeches = db.scalar(select(func.count()).select_from(Speech).where(Speech.processed == True)) or 0
    total_claims = db.scalar(select(func.count()).select_from(Claim)) or 0
    total_contradictions = db.scalar(select(func.count()).select_from(Contradiction)) or 0

    return {
        'total_speeches': int(total_speeches),
        'processed_speeches': int(processed_speeches),
        'total_claims': int(total_claims),
        'total_contradictions': int(total_contradictions),
    }
