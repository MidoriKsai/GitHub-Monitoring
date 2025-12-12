import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db.base import engine, SQLModel
from app.ws.manager import manager
from app.tasks.github_task import github_scheduler
from app.api import tasks, github
from app.nats.nats_client import start_nats

app = FastAPI(title="Async Backend Service", version="1.0")

app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(github.router, prefix="/github", tags=["GitHub"])

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    asyncio.create_task(start_nats(manager))

    asyncio.create_task(github_scheduler(manager))

@app.on_event("shutdown")
async def on_shutdown():
    pass
