import uuid
from engine import Engine
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates


app = FastAPI()
templates = Jinja2Templates(directory="templates")
engine = Engine()


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
	return templates.TemplateResponse("home.html", {"request": request})


@app.post("/create-room")
async def create_room():
	room_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID for readability
	engine.active_rooms[room_id] = {
		"players": [],
		"connected": 0,
		"state": "waiting"  # waiting, playing, finished
	}
	return RedirectResponse(url=f"/game/{room_id}", status_code=303)


@app.get("/game/{room_id}", response_class=HTMLResponse)
async def get_game(request: Request, room_id: str):
	if room_id not in engine.active_rooms:
		return HTMLResponse("Room not found", status_code=404)

	return templates.TemplateResponse("game.html", {"request": request, "room_id": room_id})


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
	if room_id not in engine.active_rooms:
		await websocket.close(code=1000)
		return

	await websocket.accept()

	# Add player to room
	player_id = str(uuid.uuid4())
	engine.active_rooms[room_id]["players"].append({"id": player_id, "ws": websocket, "score": 0})
	engine.active_rooms[room_id]["connected"] += 1

	try:
		# Notify all players that someone joined
		await engine.broadcast_room_state(room_id)

		# Start game if 2 players
		if engine.active_rooms[room_id]["connected"] == 2:
			engine.active_rooms[room_id]["state"] = "playing"
			await engine.start_game(room_id)

		# Main message loop
		while True:
			data = await websocket.receive_json()
			await engine.handle_player_message(room_id, player_id, data)

	except WebSocketDisconnect:
		# Remove player from room
		engine.active_rooms[room_id]["players"] = [p for p in engine.active_rooms[room_id]["players"] if p["id"] != player_id]
		engine.active_rooms[room_id]["connected"] -= 1

		if engine.active_rooms[room_id]["connected"] == 0:
			# Remove room if empty
			del engine.active_rooms[room_id]
		else:
			# Notify remaining player
			await engine.broadcast_room_state(room_id)

