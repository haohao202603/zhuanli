import os


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./patent_tracker.db")


def get_ingest_poll_seconds() -> int:
    return int(os.getenv("INGEST_POLL_SECONDS", "30"))


def get_ingest_max_attempts() -> int:
    return int(os.getenv("INGEST_MAX_ATTEMPTS", "3"))
