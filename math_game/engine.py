import random
import asyncio


class Engine:
    def __init__(self):
        self.active_rooms = {}

    async def broadcast_room_state(self, room_id):
        """Send room state to all players"""
        for player in self.active_rooms[room_id]["players"]:
            player_data = [
                {"id": p["id"], "score": p["score"]}
                for p in self.active_rooms[room_id]["players"]
            ]
            await player["ws"].send_json({
                "type": "room_update",
                "players": player_data,
                "connected": self.active_rooms[room_id]["connected"],
                "state": self.active_rooms[room_id]["state"]
            })

    async def start_game(self, room_id):
        """Start the game and send questions"""
        round_count = 10  # 10 rounds of questions

        for round_num in range(1, round_count + 1):
            question, answer = self.generate_question()
            self.active_rooms[room_id]["current_question"] = {
                "question": question,
                "answer": answer,
                "answered_by": None
            }

            # Send question to all players
            for player in self.active_rooms[room_id]["players"]:
                await player["ws"].send_json({
                    "type": "question",
                    "round": round_num,
                    "total_rounds": round_count,
                    "question": question
                })

            # Wait 10 seconds for answers
            await asyncio.sleep(10)

            # Move to next round
            if round_num < round_count:
                await self.broadcast_room_state(room_id)
            else:
                # Game finished
                self.active_rooms[room_id]["state"] = "finished"
                await self.broadcast_room_state(room_id)

                # Announce winner
                winner = max(self.active_rooms[room_id]["players"], key=lambda x: x["score"])
                for player in self.active_rooms[room_id]["players"]:
                    await player["ws"].send_json({
                        "type": "game_over",
                        "winner": winner["id"],
                        "scores": [{"id": p["id"], "score": p["score"]} for p in self.active_rooms[room_id]["players"]]
                    })

    @staticmethod
    def generate_question():
        """Generate a simple math question"""
        operations = [
            lambda a, b: (f"{a} + {b}", a + b),
            lambda a, b: (f"{a} - {b}", a - b),
            lambda a, b: (f"{a} × {b}", a * b)
        ]

        a = random.randint(1, 20)
        b = random.randint(1, 20)

        # For subtraction, ensure positive result
        if random.choice(operations) == operations[1] and b > a:
            a, b = b, a

        question_func = random.choice(operations)
        question, answer = question_func(a, b)

        return question, answer

    async def handle_player_message(self, room_id, player_id, data):
        """Handle messages from players"""
        if data["type"] == "answer":
            # Verify answer
            current = self.active_rooms[room_id]["current_question"]

            # If question already answered or game not in playing state, ignore
            if current["answered_by"] is not None or self.active_rooms[room_id]["state"] != "playing":
                return

            player = next(p for p in self.active_rooms[room_id]["players"] if p["id"] == player_id)

            if str(data["answer"]).strip() == str(current["answer"]):
                # Correct answer
                current["answered_by"] = player_id
                player["score"] += 1

                # Notify both players
                for p in self.active_rooms[room_id]["players"]:
                    await p["ws"].send_json({
                        "type": "answer_result",
                        "correct": True,
                        "answered_by": player_id,
                        "score_update": [{"id": pl["id"], "score": pl["score"]} for pl in self.active_rooms[room_id]["players"]]
                    })
            else:
                # Wrong answer - just notify the player who answered
                await player["ws"].send_json({
                    "type": "answer_result",
                    "correct": False
                })