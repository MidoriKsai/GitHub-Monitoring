import json
from app.nats.nats_client import nats_client

async def publish_event(subject: str, event: str, payload: dict):
    message = {"event": event, "payload": payload}
    await nats_client.publish(subject, json.dumps(message).encode())
