import asyncio
import websockets
import uuid


clients = {}


async def handler(websocket):
    client_id = str(uuid.uuid4())
    clients[client_id] = websocket
    print(f"Client connected with id: {client_id}")
    try:
        async for message in websocket:
            print(f"CLIENT SAYS: {message}")
            await websocket.send(message)
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Client disconnected")
        await websocket.close()


async def main():
    start_server = await websockets.serve(handler, "localhost", 8765)
    print("Websocket server started on ws://localhost:8765")
    await start_server.wait_closed()

asyncio.run(main())