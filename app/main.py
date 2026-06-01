from contextlib import asynccontextmanager
from threading import Event as ThreadEvent, Thread
from time import sleep

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_ingest_poll_seconds
from app.db import engine
from sqlmodel import Session
from app.db import init_db
from app.routes.ingest import router as ingest_router
from app.routes.analytics import router as analytics_router
from app.routes.events import router as events_router
from app.routes.patents import router as patents_router
from app.routes.projects import router as projects_router
from app.routes.reports import router as reports_router


_scheduler_stop_event = ThreadEvent()


def _scheduler_loop(stop_event: ThreadEvent) -> None:
    from app.services.ingest_scheduler import process_due_jobs

    while not stop_event.is_set():
        with Session(engine) as session:
            process_due_jobs(session)
        sleep(get_ingest_poll_seconds())


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    _scheduler_stop_event.clear()
    worker = Thread(target=_scheduler_loop, args=(_scheduler_stop_event,), daemon=True)
    worker.start()
    yield
    _scheduler_stop_event.set()
    worker.join(timeout=1)


app = FastAPI(title="Patent Insight Tracker API", version="0.5.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def demo_page() -> FileResponse:
    return FileResponse("app/static/index.html")


app.include_router(projects_router)
app.include_router(events_router)
app.include_router(patents_router)
app.include_router(analytics_router)
app.include_router(reports_router)
app.include_router(ingest_router)
