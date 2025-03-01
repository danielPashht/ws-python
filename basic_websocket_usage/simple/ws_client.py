import asyncio
import websockets

address = "ws://localhost:8765"


async def connect():
	async with websockets.connect(address) as websocket:
		message = await websocket.recv()
		print("Received: ", message)

asyncio.run(connect())
