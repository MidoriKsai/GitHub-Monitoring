import httpx
import os
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.models.github_repo import GitHubRepo, GitHubRepoUpdate, GitHubRepoCreate, ParsedGitHubRepo
from app.services.parser import get_repos
from app.ws.connection_manager import GitHubWSManager
from app.nats import nats_events

router = APIRouter(prefix="")
github_ws_manager = GitHubWSManager()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "User-Agent": "FastAPI-GitHub-Monitor"
}

@router.get("/parsedrepos", response_model=list[ParsedGitHubRepo])
async def get_repos_endpoint(owner: str, db: AsyncSession = Depends(get_db)):
    repos = await get_repos(owner)

    for repo in repos:
        db.add(ParsedGitHubRepo(**repo))
    await db.commit()

    stmt = select(ParsedGitHubRepo)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/repos", response_model=list[GitHubRepo])
async def list_repos(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GitHubRepo))
    return result.scalars().all()

@router.get("/repos/{repo_id}", response_model=GitHubRepo)
async def get_repo(repo_id: int, db: AsyncSession = Depends(get_db)):
    repo = await db.get(GitHubRepo, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo

@router.post("/")
async def create_repo(name: str, private: bool = True, db: AsyncSession = Depends(get_db)):
    url = "https://api.github.com/user/repos"
    payload = {"name": name, "private": private, "auto_init": True}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=HEADERS)

    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    repo_data = response.json()
    repo = GitHubRepo(
        id=repo_data["id"],
        owner=repo_data["owner"]["login"],
        name=repo_data["name"],
        url=repo_data["html_url"],
        private=repo_data.get("private", False)
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    await github_ws_manager.broadcast({"event": "repo_created", "repo": repo.dict()})

    return repo

@router.patch("/repos/{repo_id}")
async def update_repo(repo_id: int, patch: GitHubRepoUpdate, db: AsyncSession = Depends(get_db)):
    repo = await db.get(GitHubRepo, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    old_name = repo.name
    github_url = f"https://api.github.com/repos/{repo.owner}/{old_name}"

    payload = {}
    if patch.name: payload["name"] = patch.name
    if patch.private is not None: payload["private"] = patch.private

    if payload:
        async with httpx.AsyncClient() as client:
            response = await client.patch(github_url, json=payload, headers=HEADERS)
            if response.status_code not in (200, 201):
                raise HTTPException(status_code=response.status_code, detail=response.json())

        for k, v in patch.dict(exclude_unset=True).items():
            setattr(repo, k, v)
        db.add(repo)
        await db.commit()
        await db.refresh(repo)

        await github_ws_manager.broadcast({"event": "repo_updated", "repo": repo.dict()})

    return repo

@router.delete("/{repo_id}")
async def delete_repo(repo_id: int, db: AsyncSession = Depends(get_db)):
    repo = await db.get(GitHubRepo, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    github_url = f"https://api.github.com/repos/{repo.owner}/{repo.name}"

    async with httpx.AsyncClient() as client:
        response = await client.delete(github_url, headers=HEADERS)
        if response.status_code not in (204, 200):
            raise HTTPException(status_code=response.status_code, detail=response.json())

    await db.delete(repo)
    await db.commit()

    await github_ws_manager.broadcast({"event": "repo_deleted", "repo": {"id": repo.id}})

    return {"message": f"Repository {repo.owner}/{repo.name} deleted successfully"}

@router.websocket("/ws/repos")
async def ws_repos(websocket: WebSocket):
    await github_ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data.lower() == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await github_ws_manager.disconnect(websocket)

@router.post("/tasks/run")
async def run_sync_task(db: AsyncSession = Depends(get_db)):
    await nats_events.fetch_github_data(db)
    return {"message": "GitHub sync started"}
