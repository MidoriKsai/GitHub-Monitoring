import os
import httpx
import asyncio
import json
from app.models.github_repo import GitHubRepo
from app.ws.connection_manager import GitHubWSManager
from app.nats.nats_client import nats_client  # твой NATS клиент
from sqlalchemy.ext.asyncio import AsyncSession

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
github_ws_manager = GitHubWSManager()


async def fetch_github_data(db: AsyncSession):
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN not found")

    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.github.com/user/repos", headers=headers)
        if resp.status_code != 200:
            print("Error fetching GitHub data:", resp.json())
            return
        repos = resp.json()

    for repo_data in repos:
        repo = await db.get(GitHubRepo, repo_data["id"])
        if not repo:
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
            event = {"event": "repo_created", "repo": repo.dict()}
        else:
            # Обновление существующего репозитория
            repo.name = repo_data["name"]
            repo.private = repo_data.get("private", False)
            db.add(repo)
            await db.commit()
            await db.refresh(repo)
            event = {"event": "repo_updated", "repo": repo.dict()}

        # Отправляем в WebSocket (строка JSON)
        await github_ws_manager.broadcast(json.dumps(event))

        # Публикуем в NATS (байты)
        await nats_client.publish("repos.updates", json.dumps(event).encode())


async def publish_event(subject: str, message: dict):
    """
    Публикация события в NATS
    """
    await nats_client.publish(subject, json.dumps(message).encode())


async def periodic_sync_task(db: AsyncSession, interval: int = 60):
    """
    Периодическая синхронизация GitHub каждые `interval` секунд.
    """
    while True:
        try:
            await fetch_github_data(db)
        except Exception as e:
            print(f"Error in GitHub periodic task: {e}")
        await asyncio.sleep(interval)
