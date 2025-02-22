import asyncio
from typing import Dict
import uuid


from fastapi import Cookie, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI(title="WebSocket chat")


def get_uuid() -> str:
    return str(uuid.uuid4())[:6]


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, _id: str):
        await websocket.accept()
        self.active_connections[_id] = websocket

    async def disconnect(self, _id: str):
        if _id in self.active_connections.keys():
            del self.active_connections[_id]
        await self.broadcast(f"User {_id} left the chat")

    async def broadcast(self, message: str):
        for _id, connection in list(self.active_connections.items()):
            try:
                await connection.send_text(message)
            except RuntimeError as exc:
                await self.disconnect(_id)

    async def send_personal_message(self, message: str, _id: str):
        if _id in self.active_connections:
            await self.active_connections[_id].send_text(message)
        else:
            print("Message for non-existent user")


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: str = Cookie(None)):
    if client_id is None:
        client_id = get_uuid()
        await websocket.send({"type": "websocket.set_cookie", "name": "client_id", "value": client_id})
    _id = client_id
    print(f"New connection: {_id}")

    await manager.connect(_id=_id, websocket=websocket)
    await manager.broadcast(f"User {_id} joined the chat")

    async def send_pings():
        while True:
            try:
                await websocket.send_text("ping")
                await asyncio.sleep(5)
            except WebSocketDisconnect:
                print(f"User {_id} disconnected")
                await manager.disconnect(_id)
                break

    await asyncio.create_task(send_pings())

    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith("@"):
                _id = data[1:]
                await manager.send_personal_message(f"Personal message for {_id}", _id)
            else:
                await manager.broadcast(f"User {_id}: {data}")
    except WebSocketDisconnect:
        print(f"User {_id} disconnected")
        await manager.disconnect(_id)

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                if (event.data === "ping") {
                    ws.send("pong");
                } else {
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                }
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ws_server:app", host="0.0.0.0", port=8000, reload=True)
