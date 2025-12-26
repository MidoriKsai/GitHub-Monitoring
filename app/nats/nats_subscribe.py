import json
import asyncio
from app.nats.nats_client import nats_client
from app.db.db import get_db
from app.models.github_repo import GitHubRepo

async def handle_nats_message(msg):
    data = json.loads(msg.data.decode())
    event = data.get("event")
    payload = data.get("payload")

    print(f"Received NATS event: {event} - {payload}")

    async with get_db() as session:
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


async def nats_subscribe_task():
    async def message_handler(msg):
        try:
            await handle_nats_message(msg)
        except Exception as e:
            print(f"Error handling NATS message: {e}")

    await nats_client.subscribe("repos.updates", cb=message_handler)
    print("Subscribed to NATS channel: repos.updates")

asyncio.create_task(nats_subscribe_task())
