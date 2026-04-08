import uuid

from .websocket_manager import WebSocketManager
import crud


class GameManager:
    def __init__(self):
        self._manager = WebSocketManager()



