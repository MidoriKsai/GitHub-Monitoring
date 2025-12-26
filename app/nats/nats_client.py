# app/nats/nats_client.py
import asyncio
from nats.aio.client import Client as NATS
import os
from dotenv import load_dotenv

load_dotenv()
NATS_URL = os.getenv("NATS_URL", "nats://127.0.0.1:4222")

nats_client = NATS()


async def connect_nats():
    try:
        await nats_client.connect(servers=[NATS_URL])
        print("Connected to NATS server")
    except Exception as e:
        print(f"Error connecting to NATS: {e}")


async def publish(subject: str, message: dict):
    await nats_client.publish(subject, str(message).encode())


async def subscribe(subject: str, callback):

    async def message_handler(msg):
        data = msg.data.decode()
        await callback(data)

    await nats_client.subscribe(subject, cb=message_handler)

asyncio.create_task(connect_nats())
