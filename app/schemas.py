from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    target_name: str = Field(min_length=2, max_length=120)
    synonyms: list[str] = Field(default_factory=list)


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    target_name: str
    synonyms: list[str]
    status: str
    created_at: datetime




class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    target_name: str | None = Field(default=None, min_length=2, max_length=120)
    synonyms: list[str] | None = None
    status: str | None = Field(default=None, max_length=30)


class MonitorRuleUpdate(BaseModel):
    keywords: list[str] | None = None
    assignees: list[str] | None = None
    ipc_cpc: list[str] | None = None
    severity: str | None = Field(default=None, pattern=r"^P[1-3]$")
    enabled: bool | None = None


class ProjectSummaryRead(BaseModel):
    project_id: int
    rules_count: int
    events_count: int
    patents_count: int


class MonitorRuleCreate(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    assignees: list[str] = Field(default_factory=list)
    ipc_cpc: list[str] = Field(default_factory=list)
    severity: str = Field(pattern=r"^P[1-3]$")
    enabled: bool = True


class MonitorRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    keywords: list[str]
    assignees: list[str]
    ipc_cpc: list[str]
    severity: str
    enabled: bool
    created_at: datetime


class PatentCreate(BaseModel):
    project_id: int
    publication_number: str = Field(min_length=5, max_length=64)
    title: str = Field(min_length=3, max_length=300)
    assignee: str = Field(min_length=2, max_length=200)
    jurisdiction: str = Field(min_length=2, max_length=10)
    publication_date: date
    legal_status: str = Field(default="published", max_length=50)
    abstract: str = Field(default="", max_length=5000)


class PatentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    publication_number: str
    title: str
    assignee: str
    jurisdiction: str
    publication_date: date
    legal_status: str
    abstract: str
    created_at: datetime


class EventCreate(BaseModel):
    project_id: int
    patent_id: str = Field(min_length=3, max_length=64)
    event_type: str = Field(min_length=3, max_length=64)
    severity: str = Field(pattern=r"^P[1-3]$")
    summary: str = Field(default="", max_length=500)


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    patent_id: str
    event_type: str
    severity: str
    summary: str
    detected_at: datetime


class ProjectEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    patent_id: str
    event_type: str
    severity: str
    summary: str
    detected_at: datetime


class PatentBulkCreate(BaseModel):
    items: list[PatentCreate] = Field(default_factory=list, min_length=1)


class PatentBulkResult(BaseModel):
    created: int
    skipped_conflict: int
    invalid_project: int
    created_ids: list[int] = Field(default_factory=list)


class IngestJobCreate(BaseModel):
    project_id: int
    source_name: str = Field(default="mock_source", min_length=2, max_length=100)


class IngestJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    source_name: str
    status: str
    retry_count: int
    max_retries: int
    error_message: str
    next_run_at: datetime
    last_run_at: datetime | None
    created_at: datetime
