import asyncio
from fastapi import FastAPI
from app.api import github
from app.db.db import engine, SQLModel, async_session
from fastapi.middleware.cors import CORSMiddleware
from app.nats import nats_events
import os
from dotenv import load_dotenv

load_dotenv()
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

app.include_router(github.router, prefix="/github", tags=["GitHub"])


@app.on_event("startup")
async def on_startup():
    # Создаем таблицы в базе
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Запуск фоновой задачи GitHub
    asyncio.create_task(start_periodic_sync())


async def start_periodic_sync():
    """
    Фоновая задача для периодической синхронизации GitHub каждые N секунд.
    """
    # Указываем интервал в секундах (например, каждые 60 секунд)
    interval = 60

    async with async_session() as session:
        await nats_events.periodic_sync_task(session, interval)
