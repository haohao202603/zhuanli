from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.models import Event, MonitorRule, Patent, Project
from app.schemas import (
    MonitorRuleCreate,
    MonitorRuleRead,
    ProjectCreate,
    ProjectEventRead,
    ProjectRead,
    ProjectSummaryRead,
    ProjectUpdate,
    MonitorRuleUpdate,
)
from app.services.event_generator import create_patent_event_if_missing

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, session: Session = Depends(get_session)) -> ProjectRead:
    project = Project(
        name=payload.name.strip(),
        target_name=payload.target_name.strip(),
        synonyms=payload.synonyms,
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return ProjectRead.model_validate(project)


@router.get("", response_model=list[ProjectRead])
def list_projects(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[ProjectRead]:
    rows = session.exec(select(Project).order_by(Project.created_at.desc()).offset(offset).limit(limit)).all()
    return [ProjectRead.model_validate(row) for row in rows]


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, session: Session = Depends(get_session)) -> ProjectRead:
    row = session.get(Project, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRead.model_validate(row)




@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    session: Session = Depends(get_session),
) -> ProjectRead:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return ProjectRead.model_validate(project)

    for key, value in updates.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(project, key, value)

    session.add(project)
    session.commit()
    session.refresh(project)
    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", response_model=dict[str, int])
def delete_project(project_id: int, session: Session = Depends(get_session)) -> dict[str, int]:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    rules = session.exec(select(MonitorRule).where(MonitorRule.project_id == project_id)).all()
    patents = session.exec(select(Patent).where(Patent.project_id == project_id)).all()
    events = session.exec(select(Event).where(Event.project_id == project_id)).all()

    for item in rules + events + patents:
        session.delete(item)
    session.delete(project)
    session.commit()

    return {
        "deleted_project_id": project_id,
        "deleted_rules": len(rules),
        "deleted_patents": len(patents),
        "deleted_events": len(events),
    }


@router.get("/{project_id}/summary", response_model=ProjectSummaryRead)
def get_project_summary(project_id: int, session: Session = Depends(get_session)) -> ProjectSummaryRead:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    rules_count = len(session.exec(select(MonitorRule).where(MonitorRule.project_id == project_id)).all())
    events_count = len(session.exec(select(Event).where(Event.project_id == project_id)).all())
    patents_count = len(session.exec(select(Patent).where(Patent.project_id == project_id)).all())
    return ProjectSummaryRead(project_id=project_id, rules_count=rules_count, events_count=events_count, patents_count=patents_count)


@router.post("/{project_id}/rules", response_model=MonitorRuleRead, status_code=201)
def create_rule(
    project_id: int,
    payload: MonitorRuleCreate,
    session: Session = Depends(get_session),
) -> MonitorRuleRead:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    rule = MonitorRule(project_id=project_id, **payload.model_dump())
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return MonitorRuleRead.model_validate(rule)




@router.patch("/{project_id}/rules/{rule_id}", response_model=MonitorRuleRead)
def update_rule(
    project_id: int,
    rule_id: int,
    payload: MonitorRuleUpdate,
    session: Session = Depends(get_session),
) -> MonitorRuleRead:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    rule = session.get(MonitorRule, rule_id)
    if rule is None or rule.project_id != project_id:
        raise HTTPException(status_code=404, detail="Rule not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return MonitorRuleRead.model_validate(rule)

    for key, value in updates.items():
        setattr(rule, key, value)

    session.add(rule)
    session.commit()
    session.refresh(rule)
    return MonitorRuleRead.model_validate(rule)


@router.get("/{project_id}/rules", response_model=list[MonitorRuleRead])
def list_rules(
    project_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[MonitorRuleRead]:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    rows = session.exec(
        select(MonitorRule).where(MonitorRule.project_id == project_id).order_by(MonitorRule.created_at.desc()).offset(offset).limit(limit)
    ).all()
    return [MonitorRuleRead.model_validate(row) for row in rows]


@router.post("/{project_id}/events/refresh")
def refresh_project_patent_events(project_id: int, session: Session = Depends(get_session)) -> dict:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    patents = session.exec(select(Patent).where(Patent.project_id == project_id)).all()
    created = 0
    for patent in patents:
        before = session.exec(
            select(Event).where(
                Event.project_id == patent.project_id,
                Event.patent_id == patent.publication_number,
                Event.event_type == "new_patent_ingested",
            )
        ).first()
        create_patent_event_if_missing(session, patent)
        if before is None:
            created += 1

    return {"project_id": project_id, "patents_scanned": len(patents), "events_created": created}


@router.get("/{project_id}/events", response_model=list[ProjectEventRead])
def list_project_events(
    project_id: int,
    severity: str | None = Query(default=None, pattern=r"^P[1-3]$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[ProjectEventRead]:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    query = select(Event).where(Event.project_id == project_id).order_by(Event.detected_at.desc()).offset(offset).limit(limit)
    if severity is not None:
        query = query.where(Event.severity == severity)

    rows = session.exec(query).all()
    return [ProjectEventRead.model_validate(row) for row in rows]
