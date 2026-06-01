from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.models import Event, Project
from app.schemas import EventCreate, EventRead

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventRead, status_code=201)
def create_event(payload: EventCreate, session: Session = Depends(get_session)) -> EventRead:
    project = session.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=400, detail="Invalid project_id")

    event = Event(**payload.model_dump())
    session.add(event)
    session.commit()
    session.refresh(event)
    return EventRead.model_validate(event)


@router.get("", response_model=list[EventRead])
def list_events(
    project_id: int | None = Query(default=None),
    severity: str | None = Query(default=None, pattern=r"^P[1-3]$"),
    event_type: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[EventRead]:
    query = select(Event).order_by(Event.detected_at.desc()).offset(offset).limit(limit)
    if project_id is not None:
        query = query.where(Event.project_id == project_id)
    if severity is not None:
        query = query.where(Event.severity == severity)
    if event_type is not None:
        query = query.where(Event.event_type == event_type)

    rows = session.exec(query).all()
    return [EventRead.model_validate(row) for row in rows]
