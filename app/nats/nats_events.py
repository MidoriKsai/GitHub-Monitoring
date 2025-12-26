import json
import asyncio
from app.nats.nats_client import nats_client
from app.db.db import get_db
from app.models.github_repo import GitHubRepo
from app.tasks.github_task import fetch_github_data
from app.ws.connection_manager import GitHubWSManager

github_ws_manager = GitHubWSManager()

async def handle_nats_message(msg):
    try:
        data = json.loads(msg.data.decode())
        event = data.get("event")
        payload = data.get("payload")
        print(f"Received NATS event: {event} - {payload}")

        async for session in get_db():
            repo = await session.get(GitHubRepo, payload["id"])
            if event == "repo_created" and not repo:
                repo = GitHubRepo(**payload)
                session.add(repo)
                await session.commit()
            elif event == "repo_updated" and repo:
                for k, v in payload.items():
                    setattr(repo, k, v)
                session.add(repo)
                await session.commit()
            elif event == "repo_deleted" and repo:
                await session.delete(repo)
                await session.commit()

        await github_ws_manager.broadcast(json.dumps({"event": event, "repo": payload}))
    except Exception as e:
        print(f"Error handling NATS message: {e}")


async def nats_subscribe_task(subject: str = "repos.updates"):
    async def message_handler(msg):
        await handle_nats_message(msg)

    await nats_client.subscribe(subject, cb=message_handler)
    print(f"Subscribed to NATS channel: {subject}")


async def periodic_sync_task(interval: int = 60):
    async for session in get_db():
        while True:
            try:
                await fetch_github_data(session)
            except Exception as e:
                print(f"Error in periodic sync task: {e}")
            await asyncio.sleep(interval)
