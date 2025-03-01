import asyncio
import websockets


async def handler(websocket):
    print("Client connected")
    await websocket.send("Hello, Websocket!")
    await websocket.close()


async def main():
    start_server = await websockets.serve(handler, "localhost", 8765)
    print("Websocket server started on ws://localhost:8765")
    await start_server.wait_closed()

asyncio.run(main())
