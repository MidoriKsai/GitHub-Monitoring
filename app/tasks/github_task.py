import asyncio
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.nats.nats_events import publish_event
from app.ws.connection_manager import ItemWSManager
from app.models.github_repo import GitHubRepo

ws_manager: ItemWSManager = ItemWSManager()


async def fetch_github_data_periodically(db: AsyncSession, interval: int = 300):
    while True:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://github.com/explore")
                data = {"event": "github_data", "payload": "some data from github explore"}

                await ws_manager.broadcast(data)

                await publish_event("items.updates", data)
        except Exception as e:
            print("Error in GitHub periodic task:", e)
        await asyncio.sleep(interval)
