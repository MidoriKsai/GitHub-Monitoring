from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.staticfiles import StaticFiles
from app.ws.connection_manager import GitHubWSManager

from app.api import github
from app.db.db import engine, SQLModel
import asyncio

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.nats.nats_events import fetch_github_data
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="GitHub Monitor API", version="1.0")
static = Jinja2Templates(directory="app/static")
github_ws_manager = GitHubWSManager()
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

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return static.TemplateResponse("index.html", {"request": request})

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def schedule_github_sync(db: AsyncSession, interval: int = 300):
    while True:
        try:
            await fetch_github_data(db)
        except Exception as e:
            print("Error in GitHub sync:", e)
        await asyncio.sleep(interval)

@app.websocket("/ws/repos")
async def ws_repos(websocket: WebSocket):
    await websocket.accept()
    await github_ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data.lower() == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await github_ws_manager.disconnect(websocket)