from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.models import Patent, Project
from app.schemas import PatentBulkCreate, PatentBulkResult, PatentCreate, PatentRead
from app.services.event_generator import create_patent_event_if_missing

router = APIRouter(prefix="/patents", tags=["patents"])


@router.post("", response_model=PatentRead, status_code=201)
def create_patent(payload: PatentCreate, session: Session = Depends(get_session)) -> PatentRead:
    project = session.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=400, detail="Invalid project_id")

    exists = session.exec(
        select(Patent).where(
            Patent.project_id == payload.project_id,
            Patent.publication_number == payload.publication_number,
        )
    ).first()
    if exists is not None:
        raise HTTPException(status_code=409, detail="publication_number already exists in project")

    patent = Patent(**payload.model_dump())
    session.add(patent)
    session.commit()
    session.refresh(patent)
    create_patent_event_if_missing(session, patent)
    return PatentRead.model_validate(patent)


@router.post("/bulk", response_model=PatentBulkResult)
def bulk_create_patents(payload: PatentBulkCreate, session: Session = Depends(get_session)) -> PatentBulkResult:
    created = 0
    skipped_conflict = 0
    invalid_project = 0
    created_ids: list[int] = []

    for item in payload.items:
        project = session.get(Project, item.project_id)
        if project is None:
            invalid_project += 1
            continue

        exists = session.exec(
            select(Patent).where(
                Patent.project_id == item.project_id,
                Patent.publication_number == item.publication_number,
            )
        ).first()
        if exists is not None:
            skipped_conflict += 1
            continue

        patent = Patent(**item.model_dump())
        session.add(patent)
        session.commit()
        session.refresh(patent)
        create_patent_event_if_missing(session, patent)

        created += 1
        created_ids.append(patent.id)

    return PatentBulkResult(
        created=created,
        skipped_conflict=skipped_conflict,
        invalid_project=invalid_project,
        created_ids=created_ids,
    )


@router.get("", response_model=list[PatentRead])
def list_patents(
    project_id: int | None = Query(default=None),
    assignee: str | None = Query(default=None),
    q: str | None = Query(default=None, description="Search in title"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[PatentRead]:
    query = select(Patent).order_by(Patent.publication_date.desc()).offset(offset).limit(limit)

    if project_id is not None:
        query = query.where(Patent.project_id == project_id)
    if assignee is not None:
        query = query.where(Patent.assignee == assignee)
    if q is not None:
        query = query.where(Patent.title.contains(q))

    rows = session.exec(query).all()
    return [PatentRead.model_validate(row) for row in rows]


@router.get("/{patent_id}", response_model=PatentRead)
def get_patent(patent_id: int, session: Session = Depends(get_session)) -> PatentRead:
    patent = session.get(Patent, patent_id)
    if patent is None:
        raise HTTPException(status_code=404, detail="Patent not found")
    create_patent_event_if_missing(session, patent)
    return PatentRead.model_validate(patent)
