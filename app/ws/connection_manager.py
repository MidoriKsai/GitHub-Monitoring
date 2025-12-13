from fastapi import WebSocket

class GitHubWSManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            await websocket.close()
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        import json
        for ws in self.active_connections:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                self.active_connections.remove(ws)


github_ws_manager = GitHubWSManager()
