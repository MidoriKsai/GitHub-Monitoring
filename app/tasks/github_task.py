import os
import httpx
import json
from app.models.github_repo import GitHubRepo
from app.nats.nats_publish import publish_event
from app.ws.connection_manager import GitHubWSManager

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}
github_ws_manager = GitHubWSManager()

async def fetch_github_data(session):
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN not found")

    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.github.com/user/repos", headers=HEADERS)

    if resp.status_code != 200:
        print("GitHub fetch error:", resp.text)
        return

    repos = resp.json()
    for repo_data in repos:
        repo = await session.get(GitHubRepo, repo_data["id"])
        event_type = ""

        if not repo:
            repo = GitHubRepo(
                id=repo_data["id"],
                owner=repo_data["owner"]["login"],
                name=repo_data["name"],
                url=repo_data["html_url"],
                private=repo_data.get("private", False)
            )
            session.add(repo)
            await session.commit()
            event_type = "repo_created"
        else:
            changed = False
            for field in ["name", "private", "url"]:
                value = repo_data.get(field)
                if value is not None and getattr(repo, field) != value:
                    setattr(repo, field, value)
                    changed = True
            if changed:
                session.add(repo)
                await session.commit()
                event_type = "repo_updated"

        if event_type:
            await broadcast_event(event_type, repo.dict())


async def broadcast_event(event: str, payload: dict):
    message = {"event": event, "payload": payload}

    # WS
    await github_ws_manager.broadcast(json.dumps(message))

    # NATS
    await publish_event("repos.updates", event, payload)
