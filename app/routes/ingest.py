from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config import get_ingest_max_attempts
from app.db import get_session
from app.models import IngestJob
from app.schemas import IngestJobCreate, IngestJobRead
from app.services.ingest_scheduler import IngestJobError, create_ingest_job, process_due_jobs

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/jobs", response_model=IngestJobRead, status_code=201)
def create_job(payload: IngestJobCreate, session: Session = Depends(get_session)) -> IngestJobRead:
    try:
        job = create_ingest_job(
            session=session,
            project_id=payload.project_id,
            source_name=payload.source_name,
            max_retries=get_ingest_max_attempts(),
        )
    except IngestJobError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IngestJobRead.model_validate(job)


@router.get("/jobs", response_model=list[IngestJobRead])
def list_jobs(session: Session = Depends(get_session)) -> list[IngestJobRead]:
    rows = session.exec(select(IngestJob).order_by(IngestJob.created_at.desc())).all()
    return [IngestJobRead.model_validate(row) for row in rows]


@router.post("/jobs/run", response_model=dict[str, int])
def run_jobs(session: Session = Depends(get_session)) -> dict[str, int]:
    processed = process_due_jobs(session)
    return {"processed": processed}
