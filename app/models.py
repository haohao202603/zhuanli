from datetime import date, datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import Field, SQLModel


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, min_length=2, max_length=120)
    target_name: str = Field(index=True, min_length=2, max_length=120)
    synonyms: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: str = Field(default="active", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class MonitorRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True, foreign_key="project.id")
    keywords: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    assignees: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    ipc_cpc: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    severity: str = Field(default="P2", index=True)
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Patent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True, foreign_key="project.id")
    publication_number: str = Field(index=True, min_length=5, max_length=64)
    title: str = Field(min_length=3, max_length=300)
    assignee: str = Field(index=True, min_length=2, max_length=200)
    jurisdiction: str = Field(index=True, min_length=2, max_length=10)
    publication_date: date
    legal_status: str = Field(default="published", index=True)
    abstract: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)


class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True, foreign_key="project.id")
    patent_id: str = Field(index=True)
    event_type: str = Field(index=True)
    severity: str = Field(index=True, default="P3")
    summary: str = Field(default="")
    detected_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)


class IngestJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True, foreign_key="project.id")
    source_name: str = Field(default="mock_source", min_length=2, max_length=100)
    status: str = Field(default="pending", index=True)
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    error_message: str = Field(default="")
    next_run_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    last_run_at: Optional[datetime] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
