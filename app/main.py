import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.database import init_db
from app.services.scheduler import setup_scheduler, shutdown_scheduler

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    setup_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title="AI Researcher Network",
    description="Track influence and relationships among top AI researchers from China",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
async def index():
    return FileResponse("frontend/index.html")


@app.post("/api/ingest/seed")
async def trigger_seed_ingestion():
    """Manually trigger seed data ingestion."""
    from app.database import async_session
    from app.services.ingestion import run_seed_ingestion

    async with async_session() as db:
        await run_seed_ingestion(db)
    return {"status": "Seed ingestion complete"}


@app.post("/api/ingest/refresh")
async def trigger_refresh():
    """Manually trigger data refresh."""
    from app.database import async_session
    from app.services.ingestion import run_refresh

    async with async_session() as db:
        await run_refresh(db)
    return {"status": "Refresh complete"}
