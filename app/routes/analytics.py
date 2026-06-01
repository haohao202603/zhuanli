from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Event, Patent, Project

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/projects/{project_id}/overview")
def project_overview(project_id: int, session: Session = Depends(get_session)) -> dict:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    patents = session.exec(select(Patent).where(Patent.project_id == project_id)).all()
    events = session.exec(select(Event).where(Event.project_id == project_id)).all()

    assignee_counter = Counter([p.assignee for p in patents])
    jurisdiction_counter = Counter([p.jurisdiction for p in patents])
    severity_counter = Counter([e.severity for e in events])

    top_assignees = [
        {"assignee": assignee, "count": count}
        for assignee, count in assignee_counter.most_common(5)
    ]
    top_jurisdictions = [
        {"jurisdiction": j, "count": count}
        for j, count in jurisdiction_counter.most_common(5)
    ]

    recent_patents = sorted(patents, key=lambda x: x.publication_date, reverse=True)[:5]
    recent_events = sorted(events, key=lambda x: x.detected_at, reverse=True)[:5]

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "target_name": project.target_name,
        },
        "metrics": {
            "patents_count": len(patents),
            "events_count": len(events),
            "severity_breakdown": dict(severity_counter),
        },
        "top_assignees": top_assignees,
        "top_jurisdictions": top_jurisdictions,
        "recent_patents": [
            {
                "publication_number": p.publication_number,
                "title": p.title,
                "assignee": p.assignee,
                "publication_date": str(p.publication_date),
            }
            for p in recent_patents
        ],
        "recent_events": [
            {
                "patent_id": e.patent_id,
                "event_type": e.event_type,
                "severity": e.severity,
                "detected_at": e.detected_at.isoformat(),
            }
            for e in recent_events
        ],
    }
