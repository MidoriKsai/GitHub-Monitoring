import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from app.db.db import engine
from app.api import github
from app.nats.nats_events import start_nats_and_sync

app = FastAPI(title="GitHub Monitor API", version="1.0")

origins = ["http://localhost", "http://127.0.0.1:5500", "http://127.0.0.1:8000"]
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

    asyncio.create_task(start_nats_and_sync(owner="YOUR_GITHUB_USERNAME"))
