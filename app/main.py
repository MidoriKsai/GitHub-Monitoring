import asyncio

import httpx
from fastapi import FastAPI
from app.api import github
from app.db.db import engine, SQLModel, async_session
from fastapi.middleware.cors import CORSMiddleware
from app.nats.nats_events import nats_subscribe_task
from app.nats import nats_events
import os
from dotenv import load_dotenv

load_dotenv(override=True)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

app = FastAPI(title="GitHub Monitor API", version="1.0")

origins = [
    "http://localhost",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:8000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(github.router, tags=["GitHub"])


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    asyncio.create_task(nats_events.periodic_sync_task(interval=60))
    asyncio.create_task(nats_subscribe_task())
