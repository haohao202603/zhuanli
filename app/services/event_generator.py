from sqlmodel import Session, select

from app.models import Event, MonitorRule, Patent


SEVERITY_ORDER = {"P1": 3, "P2": 2, "P3": 1}


def _max_severity(a: str, b: str) -> str:
    return a if SEVERITY_ORDER.get(a, 1) >= SEVERITY_ORDER.get(b, 1) else b


def derive_patent_event_severity(session: Session, patent: Patent) -> str:
    severity = "P3"
    rules = session.exec(
        select(MonitorRule).where(MonitorRule.project_id == patent.project_id, MonitorRule.enabled == True)  # noqa: E712
    ).all()

    for rule in rules:
        rule_sev = rule.severity or "P3"
        severity = _max_severity(severity, rule_sev)

        for assignee in rule.assignees:
            if assignee.lower() in patent.assignee.lower():
                severity = _max_severity(severity, "P1")

        for keyword in rule.keywords:
            if keyword.lower() in patent.title.lower():
                severity = _max_severity(severity, rule_sev)

    return severity


def create_patent_event_if_missing(session: Session, patent: Patent) -> Event:
    existing = session.exec(
        select(Event).where(
            Event.project_id == patent.project_id,
            Event.patent_id == patent.publication_number,
            Event.event_type == "new_patent_ingested",
        )
    ).first()

    if existing is not None:
        return existing

    severity = derive_patent_event_severity(session, patent)
    event = Event(
        project_id=patent.project_id,
        patent_id=patent.publication_number,
        event_type="new_patent_ingested",
        severity=severity,
        summary=f"New patent ingested: {patent.publication_number} / {patent.assignee}",
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event
