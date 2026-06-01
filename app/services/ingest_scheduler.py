from __future__ import annotations

from datetime import datetime, timedelta
from sqlmodel import Session, select

from app.models import IngestJob, Patent, Project


class IngestJobError(Exception):
    pass


def create_ingest_job(
    session: Session,
    project_id: int,
    source_name: str,
    max_retries: int,
) -> IngestJob:
    project = session.get(Project, project_id)
    if project is None:
        raise IngestJobError("Invalid project_id")

    job = IngestJob(project_id=project_id, source_name=source_name, max_retries=max_retries)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def process_due_jobs(session: Session) -> int:
    now = datetime.utcnow()
    jobs = session.exec(
        select(IngestJob).where(
            IngestJob.status.in_(["pending", "retry"]),
            IngestJob.next_run_at <= now,
        )
    ).all()

    processed = 0
    for job in jobs:
        processed += 1
        job.last_run_at = now

        try:
            _run_single_job(session, job)
        except IngestJobError as exc:
            job.retry_count += 1
            job.error_message = str(exc)
            if job.retry_count >= job.max_retries:
                job.status = "failed"
            else:
                job.status = "retry"
                job.next_run_at = now + timedelta(minutes=5)
        else:
            job.status = "completed"
            job.error_message = ""

        session.add(job)
        session.commit()

    return processed


def _run_single_job(session: Session, job: IngestJob) -> None:
    project = session.get(Project, job.project_id)
    if project is None:
        raise IngestJobError("Project not found")

    # Skeleton ingest behavior: require at least one patent already present for project.
    sample = session.exec(select(Patent).where(Patent.project_id == job.project_id)).first()
    if sample is None:
        raise IngestJobError("No patent records to enrich for project")
