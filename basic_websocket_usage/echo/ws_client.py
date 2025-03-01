import asyncio
import websockets

address = "ws://localhost:8765"
timeout_seconds = 5


async def connect():
    async with websockets.connect(address) as websocket:
        async def send_messages():
            for i in range(10):
                await websocket.send(f"Hello from client {i}")
                await asyncio.sleep(0.5)

        async def receive_messages():
            try:
                while True:
                    message = await asyncio.wait_for(
                        websocket.recv(), timeout_seconds
                    )
                    print(f"SERVER SAYS: {message}")
            except asyncio.TimeoutError:
                print(f"Timeout of {timeout_seconds} seconds reached")
                await websocket.close()
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed by server")

        await asyncio.gather(send_messages(), receive_messages())

asyncio.run(connect())
