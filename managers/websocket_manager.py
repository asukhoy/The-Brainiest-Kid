from fastapi import WebSocket
import uuid
import crud

class WebSocketManager:
    def __init__(self):
        self._active_connections: dict[int, WebSocket] = {} # [ses_code, socket]
        self._player_connections: dict[int, dict[uuid.UUID, WebSocket]] = {} # [ses_code, [player_id, socket]]

        self._session_players: dict[int, set[uuid.UUID]] = {} # [ses_code, set[player_id]]


    async def connect_host(self, session_code: int, websocket: WebSocket):
        await websocket.accept()
        self._active_connections[session_code] = websocket
        self._session_players[session_code] = set()
        self._player_connections[session_code] = {}

    async def connect_player(self, player_id: uuid.UUID, websocket: WebSocket, session_code):
        await websocket.accept()


        if session_code not in self._player_connections:
            self._player_connections[session_code] = {}

        self._player_connections[session_code][player_id] = websocket

        if session_code not in self._session_players:
            self._session_players[session_code] = set()
        self._session_players[session_code].add(player_id)

    async def disconnect_player(self, session_code: int, player_id: uuid.UUID):
        if session_code in self._player_connections and player_id in self._player_connections[
            session_code]:
            del self._player_connections[session_code][player_id]

            # Удаляем из активных игроков
            if session_code in self._session_players:
                self._session_players[session_code].discard(player_id)

    async def disconnect_host(self, session_code: int):
        if session_code in self._active_connections:
            del self._active_connections[session_code]
            del self._player_connections[session_code]
            del self._session_players[session_code]

    async def send_to_host(self, session_code: int, message: list[dict]):
        """Отправка сообщения ведущему"""
        if session_code in self._active_connections:
            try:
                await self._active_connections[session_code].send_json(message)
            except Exception as e:
                print(e)

    async def broadcast(self, session_code: int, message):
        players = self.get_players(session_code)
        for player in players:
            try:
                await self._player_connections[session_code][player].send_json(message)
            except Exception as e:
                print(e)

    async def send_to_player(self, session_code: int, player_id: uuid.UUID, message):
        """Отправка сообщения конкретному игроку"""
        if (session_code in self._player_connections and
                player_id in self._player_connections[session_code]):
            try:
                await self._player_connections[session_code][player_id].send_json(message)
            except Exception as e:
                print(e)


    def get_players(self, session_code: int):
        return self._session_players.get(session_code, set())
