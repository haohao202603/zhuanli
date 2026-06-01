from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlmodel import Session, select

from app.db import get_session
from app.models import Event, Patent, Project

router = APIRouter(prefix="/reports", tags=["reports"])


def _windowed(project: Project, patents: list[Patent], events: list[Event], days: int) -> tuple[list[Patent], list[Event]]:
    since = datetime.utcnow() - timedelta(days=days)
    recent_patents = [p for p in patents if p.created_at >= since]
    recent_events = [e for e in events if e.detected_at >= since]
    return recent_patents, recent_events


def _severity_breakdown(events: list[Event]) -> dict[str, int]:
    counts = Counter([e.severity for e in events])
    return {"P1": counts.get("P1", 0), "P2": counts.get("P2", 0), "P3": counts.get("P3", 0)}


def _build_weekly_report(project: Project, patents: list[Patent], events: list[Event], days: int) -> str:
    recent_patents, recent_events = _windowed(project, patents, events, days)
    sev = _severity_breakdown(recent_events)

    lines = [
        f"# Patent Insight Weekly Report - {project.name}",
        "",
        f"Generated at: {datetime.utcnow().isoformat()} UTC",
        f"Window: last {days} days",
        "",
        "## Summary",
        f"- Total patents: {len(patents)}",
        f"- New patents in window: {len(recent_patents)}",
        f"- Total events: {len(events)}",
        f"- New events in window: {len(recent_events)}",
        f"- Severity breakdown (window): P1={sev['P1']}, P2={sev['P2']}, P3={sev['P3']}",
        "",
        "## Recent Patents",
    ]

    if recent_patents:
        for p in sorted(recent_patents, key=lambda x: x.publication_date, reverse=True)[:20]:
            lines.append(
                f"- {p.publication_number} | {p.assignee} | {p.jurisdiction} | {p.publication_date} | {p.title}"
            )
    else:
        lines.append("- No new patents in this window")

    lines += ["", "## Recent Events"]
    if recent_events:
        for e in sorted(recent_events, key=lambda x: x.detected_at, reverse=True)[:30]:
            lines.append(f"- {e.detected_at.isoformat()} | {e.severity} | {e.event_type} | {e.patent_id}")
    else:
        lines.append("- No new events in this window")

    return "\n".join(lines) + "\n"


def _build_weekly_html(project: Project, patents: list[Patent], events: list[Event], days: int) -> str:
    recent_patents, recent_events = _windowed(project, patents, events, days)
    sev = _severity_breakdown(recent_events)
    patents_li = "".join(
        [
            f"<li>{p.publication_number} | {p.assignee} | {p.jurisdiction} | {p.publication_date} | {p.title}</li>"
            for p in sorted(recent_patents, key=lambda x: x.publication_date, reverse=True)[:20]
        ]
    ) or "<li>No new patents in this window</li>"

    events_li = "".join(
        [
            f"<li>{e.detected_at.isoformat()} | {e.severity} | {e.event_type} | {e.patent_id}</li>"
            for e in sorted(recent_events, key=lambda x: x.detected_at, reverse=True)[:30]
        ]
    ) or "<li>No new events in this window</li>"

    return f"""
<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8' />
  <title>Patent Insight Weekly Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    h1, h2 {{ margin-bottom: 8px; }}
    .meta {{ color: #555; margin-bottom: 16px; }}
  </style>
</head>
<body>
  <h1>Patent Insight Weekly Report - {project.name}</h1>
  <div class='meta'>Generated at: {datetime.utcnow().isoformat()} UTC | Window: last {days} days</div>
  <h2>Summary</h2>
  <ul>
    <li>Total patents: {len(patents)}</li>
    <li>New patents in window: {len(recent_patents)}</li>
    <li>Total events: {len(events)}</li>
    <li>New events in window: {len(recent_events)}</li>
    <li>Severity breakdown (window): P1={sev['P1']}, P2={sev['P2']}, P3={sev['P3']}</li>
  </ul>
  <h2>Recent Patents</h2>
  <ul>{patents_li}</ul>
  <h2>Recent Events</h2>
  <ul>{events_li}</ul>
</body>
</html>
""".strip()


def _build_weekly_csv(project: Project, patents: list[Patent], events: list[Event], days: int) -> str:
    recent_patents, recent_events = _windowed(project, patents, events, days)
    sev = _severity_breakdown(recent_events)

    rows = [
        "section,field,value",
        f"summary,project,{project.name}",
        f"summary,target,{project.target_name}",
        f"summary,window_days,{days}",
        f"summary,total_patents,{len(patents)}",
        f"summary,new_patents,{len(recent_patents)}",
        f"summary,total_events,{len(events)}",
        f"summary,new_events,{len(recent_events)}",
        f"summary,severity_p1,{sev['P1']}",
        f"summary,severity_p2,{sev['P2']}",
        f"summary,severity_p3,{sev['P3']}",
    ]

    rows.append("recent_patents,publication_number,assignee|jurisdiction|publication_date|title")
    for p in sorted(recent_patents, key=lambda x: x.publication_date, reverse=True)[:50]:
        rows.append(
            f"recent_patents,{p.publication_number},{p.assignee}|{p.jurisdiction}|{p.publication_date}|{p.title.replace(',', ' ')}"
        )

    rows.append("recent_events,patent_id,severity|event_type|detected_at")
    for e in sorted(recent_events, key=lambda x: x.detected_at, reverse=True)[:80]:
        rows.append(
            f"recent_events,{e.patent_id},{e.severity}|{e.event_type}|{e.detected_at.isoformat()}"
        )

    return "\n".join(rows) + "\n"


def _fetch_project_data(project_id: int, session: Session) -> tuple[Project, list[Patent], list[Event]]:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    patents = session.exec(select(Patent).where(Patent.project_id == project_id)).all()
    events = session.exec(select(Event).where(Event.project_id == project_id)).all()
    return project, patents, events


@router.get("/projects/{project_id}/weekly", response_class=PlainTextResponse)
def project_weekly_report(project_id: int, days: int = Query(default=7, ge=1, le=30), session: Session = Depends(get_session)) -> str:
    project, patents, events = _fetch_project_data(project_id, session)
    return _build_weekly_report(project, patents, events, days)


@router.get("/projects/{project_id}/weekly.md", response_class=PlainTextResponse)
def project_weekly_report_markdown(project_id: int, days: int = Query(default=7, ge=1, le=30), session: Session = Depends(get_session)) -> PlainTextResponse:
    project, patents, events = _fetch_project_data(project_id, session)
    content = _build_weekly_report(project, patents, events, days)
    filename = f"{project.name.replace(' ', '_').lower()}_weekly_report.md"
    return PlainTextResponse(content, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/projects/{project_id}/weekly.html", response_class=HTMLResponse)
def project_weekly_report_html(project_id: int, days: int = Query(default=7, ge=1, le=30), session: Session = Depends(get_session)) -> HTMLResponse:
    project, patents, events = _fetch_project_data(project_id, session)
    return HTMLResponse(_build_weekly_html(project, patents, events, days))


@router.get("/projects/{project_id}/weekly.json")
def project_weekly_report_json(project_id: int, days: int = Query(default=7, ge=1, le=30), session: Session = Depends(get_session)) -> dict:
    project, patents, events = _fetch_project_data(project_id, session)
    recent_patents, recent_events = _windowed(project, patents, events, days)
    sev = _severity_breakdown(recent_events)

    return {
        "project": {"id": project.id, "name": project.name, "target": project.target_name},
        "window_days": days,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_patents": len(patents),
            "new_patents": len(recent_patents),
            "total_events": len(events),
            "new_events": len(recent_events),
            "severity": sev,
        },
    }


@router.get("/projects/{project_id}/weekly.csv", response_class=PlainTextResponse)
def project_weekly_report_csv(project_id: int, days: int = Query(default=7, ge=1, le=30), session: Session = Depends(get_session)) -> str:
    project, patents, events = _fetch_project_data(project_id, session)
    return _build_weekly_csv(project, patents, events, days)
