from fastapi import WebSocket
import uuid

class WebSocketManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {} # [ses_code, socket]
        self.player_connections: dict[int, dict[uuid.UUID, WebSocket]] = {} # [ses_code, [player_id, socket]]

        self.session_players: dict[int, set[uuid.UUID]] = {} # [ses_code, set[player_id]]

        self.session_cache: dict[int, dict] = {} # [ses_code, ses_data]

    async def connect_host(self, session_code: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_code] = websocket

    async def connect_player(self, session_code: int, player_id: uuid.UUID, websocket: WebSocket):
        await websocket.accept()

        if session_code not in self.active_connections:
            self.player_connections[session_code] = {}

        self.player_connections[session_code][player_id] = websocket

        if session_code not in self.session_players:
            self.session_players[session_code] = set()
        self.session_players[session_code].add(player_id)

