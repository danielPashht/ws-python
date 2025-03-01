import asyncio
import websockets

uri = "ws://localhost:8000/ws"
timeout_seconds = 5


async def chat_client():
	async with websockets.connect(uri) as ws:
		print("Connected to chat server")

		async def receive_message():
			while True:
				try:
					message = await ws.recv()
					print(f"New message: {message}")
				except websockets.exceptions.ConnectionClosed:
					print("Connection closed by server")
					break

		async def send_message():
			while True:
				message = input("Your message: ")
				await ws.send(message)

		await asyncio.gather(receive_message(), send_message())


if __name__ == "__main__":
	asyncio.run(chat_client())
