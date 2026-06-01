import pytest

try:
    from fastapi.testclient import TestClient
    from app.main import app
    FASTAPI_AVAILABLE = True
except ModuleNotFoundError:
    FASTAPI_AVAILABLE = False

pytestmark = pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi is required for API integration tests")

if FASTAPI_AVAILABLE:
    client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_project_rule_patent_event_summary_and_analytics_flow() -> None:
    create_project = client.post(
        "/projects",
        json={"name": "STING Project", "target_name": "STING", "synonyms": ["TMEM173"]},
    )
    assert create_project.status_code == 201
    project_id = create_project.json()["id"]

    create_rule = client.post(
        f"/projects/{project_id}/rules",
        json={
            "keywords": ["STING inhibitor", "TMEM173"],
            "assignees": ["Company A"],
            "ipc_cpc": ["C07D", "A61K"],
            "severity": "P2",
            "enabled": True,
        },
    )
    assert create_rule.status_code == 201

    create_patent = client.post(
        "/patents",
        json={
            "project_id": project_id,
            "publication_number": "WO2026123456",
            "title": "STING inhibitors and uses thereof",
            "assignee": "Company A",
            "jurisdiction": "WO",
            "publication_date": "2026-04-13",
            "legal_status": "published",
            "abstract": "Demo patent abstract",
        },
    )
    assert create_patent.status_code == 201

    events = client.get(f"/projects/{project_id}/events")
    assert events.status_code == 200
    assert len(events.json()) >= 1
    assert any(e["event_type"] == "new_patent_ingested" for e in events.json())

    summary = client.get(f"/projects/{project_id}/summary")
    assert summary.status_code == 200
    assert summary.json()["rules_count"] >= 1
    assert summary.json()["events_count"] >= 1
    assert summary.json()["patents_count"] >= 1

    analytics = client.get(f"/analytics/projects/{project_id}/overview")
    assert analytics.status_code == 200
    body = analytics.json()
    assert body["metrics"]["patents_count"] >= 1
    assert isinstance(body["top_assignees"], list)


def test_duplicate_publication_in_project() -> None:
    project = client.post("/projects", json={"name": "KRAS", "target_name": "KRAS", "synonyms": []})
    project_id = project.json()["id"]

    payload = {
        "project_id": project_id,
        "publication_number": "US2026000001",
        "title": "KRAS modulator",
        "assignee": "Company B",
        "jurisdiction": "US",
        "publication_date": "2026-04-13",
        "legal_status": "published",
        "abstract": "A KRAS patent",
    }
    assert client.post("/patents", json=payload).status_code == 201
    assert client.post("/patents", json=payload).status_code == 409


def test_refresh_event_endpoint_idempotent() -> None:
    project = client.post("/projects", json={"name": "TYK2", "target_name": "TYK2", "synonyms": []})
    pid = project.json()["id"]

    client.post(
        f"/projects/{pid}/rules",
        json={"keywords": ["TYK2"], "assignees": ["Company C"], "ipc_cpc": ["C07D"], "severity": "P2", "enabled": True},
    )
    client.post(
        "/patents",
        json={
            "project_id": pid,
            "publication_number": "WO2026999999",
            "title": "TYK2 inhibitors",
            "assignee": "Company C",
            "jurisdiction": "WO",
            "publication_date": "2026-04-13",
            "legal_status": "published",
            "abstract": "Demo",
        },
    )

    first = client.post(f"/projects/{pid}/events/refresh")
    second = client.post(f"/projects/{pid}/events/refresh")
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["events_created"] == 0


def test_weekly_report_endpoint() -> None:
    project = client.post("/projects", json={"name": "Report Project", "target_name": "STING", "synonyms": []})
    pid = project.json()["id"]

    client.post(
        "/patents",
        json={
            "project_id": pid,
            "publication_number": "EP2026001234",
            "title": "STING small molecule",
            "assignee": "Company D",
            "jurisdiction": "EP",
            "publication_date": "2026-04-20",
            "legal_status": "published",
            "abstract": "Demo",
        },
    )

    report = client.get(f"/reports/projects/{pid}/weekly?days=14")
    assert report.status_code == 200
    assert "Patent Insight Weekly Report" in report.text
    assert "Recent Patents" in report.text


def test_weekly_report_json_endpoint() -> None:
    project = client.post("/projects", json={"name": "JSON Report Project", "target_name": "KRAS", "synonyms": []})
    pid = project.json()["id"]

    payload = {
        "project_id": pid,
        "publication_number": "US2026111111",
        "title": "KRAS inhibitors",
        "assignee": "Company E",
        "jurisdiction": "US",
        "publication_date": "2026-04-20",
        "legal_status": "published",
        "abstract": "Demo",
    }
    client.post("/patents", json=payload)

    res = client.get(f"/reports/projects/{pid}/weekly.json?days=7")
    assert res.status_code == 200
    body = res.json()
    assert body["project"]["id"] == pid
    assert "summary" in body


def test_weekly_report_csv_endpoint() -> None:
    project = client.post("/projects", json={"name": "CSV Report Project", "target_name": "TYK2", "synonyms": []})
    pid = project.json()["id"]

    client.post(
        "/patents",
        json={
            "project_id": pid,
            "publication_number": "JP2026222222",
            "title": "TYK2 chemistry",
            "assignee": "Company F",
            "jurisdiction": "JP",
            "publication_date": "2026-04-22",
            "legal_status": "published",
            "abstract": "Demo",
        },
    )

    res = client.get(f"/reports/projects/{pid}/weekly.csv?days=14")
    assert res.status_code == 200
    assert "section,field,value" in res.text
    assert "summary,project,CSV Report Project" in res.text


def test_weekly_report_markdown_download() -> None:
    project = client.post("/projects", json={"name": "MD Report Project", "target_name": "STING", "synonyms": []})
    pid = project.json()["id"]

    res = client.get(f"/reports/projects/{pid}/weekly.md?days=7")
    assert res.status_code == 200
    assert "attachment; filename=" in res.headers.get("content-disposition", "")
    assert "Patent Insight Weekly Report" in res.text


def test_weekly_report_html_endpoint() -> None:
    project = client.post("/projects", json={"name": "HTML Report Project", "target_name": "PRMT5", "synonyms": []})
    pid = project.json()["id"]

    res = client.get(f"/reports/projects/{pid}/weekly.html?days=7")
    assert res.status_code == 200
    assert "<html" in res.text.lower()
    assert "Patent Insight Weekly Report" in res.text


def test_weekly_report_severity_in_outputs() -> None:
    project = client.post("/projects", json={"name": "Severity Report Project", "target_name": "STING", "synonyms": []})
    pid = project.json()["id"]

    client.post(
        "/events",
        json={
            "project_id": pid,
            "patent_id": "WO2026111000",
            "event_type": "manual_signal",
            "severity": "P1",
            "summary": "signal",
        },
    )

    j = client.get(f"/reports/projects/{pid}/weekly.json?days=7")
    assert j.status_code == 200
    assert "severity" in j.json()["summary"]

    csv = client.get(f"/reports/projects/{pid}/weekly.csv?days=7")
    assert csv.status_code == 200
    assert "summary,severity_p1" in csv.text

    md = client.get(f"/reports/projects/{pid}/weekly?days=7")
    assert "Severity breakdown" in md.text


def test_bulk_patent_ingest_endpoint() -> None:
    project = client.post("/projects", json={"name": "Bulk Project", "target_name": "STING", "synonyms": []})
    pid = project.json()["id"]

    payload = {
        "items": [
            {
                "project_id": pid,
                "publication_number": "WO2026333301",
                "title": "STING bulk 1",
                "assignee": "Company G",
                "jurisdiction": "WO",
                "publication_date": "2026-04-25",
                "legal_status": "published",
                "abstract": "A",
            },
            {
                "project_id": pid,
                "publication_number": "WO2026333301",
                "title": "STING bulk dup",
                "assignee": "Company G",
                "jurisdiction": "WO",
                "publication_date": "2026-04-25",
                "legal_status": "published",
                "abstract": "B",
            },
            {
                "project_id": 999999,
                "publication_number": "WO2026333302",
                "title": "Invalid project",
                "assignee": "Company H",
                "jurisdiction": "WO",
                "publication_date": "2026-04-25",
                "legal_status": "published",
                "abstract": "C",
            },
        ]
    }

    res = client.post("/patents/bulk", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["created"] == 1
    assert body["skipped_conflict"] == 1
    assert body["invalid_project"] == 1


def test_ingest_job_retry_skeleton() -> None:
    project = client.post("/projects", json={"name": "INGEST", "target_name": "INGEST", "synonyms": []})
    pid = project.json()["id"]

    created = client.post("/ingest/jobs", json={"project_id": pid, "source_name": "mock_source"})
    assert created.status_code == 201
    job_id = created.json()["id"]

    run = client.post("/ingest/jobs/run")
    assert run.status_code == 200
    assert run.json()["processed"] >= 1

    jobs = client.get("/ingest/jobs")
    assert jobs.status_code == 200
    job = next(row for row in jobs.json() if row["id"] == job_id)
    assert job["status"] in ["retry", "failed"]
    assert job["retry_count"] >= 1


def test_project_delete_cascade_and_pagination() -> None:
    project = client.post("/projects", json={"name": "Del Project", "target_name": "STING", "synonyms": []})
    pid = project.json()["id"]

    for i in range(3):
        client.post(
            "/patents",
            json={
                "project_id": pid,
                "publication_number": f"WO20269999{i}",
                "title": f"patent {i}",
                "assignee": "Company Z",
                "jurisdiction": "WO",
                "publication_date": "2026-04-13",
                "legal_status": "published",
                "abstract": "Demo",
            },
        )

    page = client.get(f"/patents?project_id={pid}&offset=1&limit=1")
    assert page.status_code == 200
    assert len(page.json()) == 1

    deleted = client.delete(f"/projects/{pid}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted_project_id"] == pid

    missing = client.get(f"/projects/{pid}")
    assert missing.status_code == 404


def test_project_and_rule_patch() -> None:
    project = client.post("/projects", json={"name": "Patch Project", "target_name": "STING", "synonyms": ["A"]})
    pid = project.json()["id"]

    patched = client.patch(f"/projects/{pid}", json={"name": "Patch Project V2", "status": "paused"})
    assert patched.status_code == 200
    assert patched.json()["name"] == "Patch Project V2"
    assert patched.json()["status"] == "paused"

    rule = client.post(
        f"/projects/{pid}/rules",
        json={"keywords": ["STING"], "assignees": ["Company K"], "ipc_cpc": ["C07D"], "severity": "P2", "enabled": True},
    )
    rid = rule.json()["id"]

    rule_patch = client.patch(f"/projects/{pid}/rules/{rid}", json={"severity": "P1", "enabled": False})
    assert rule_patch.status_code == 200
    assert rule_patch.json()["severity"] == "P1"
    assert rule_patch.json()["enabled"] is False
