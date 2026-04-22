import enum


class PlayerState(enum.Enum):
    ELIMINATED = "eliminated"
    CONNECTED = "connected"
    PENDING = "pending"
    DISCONNECTED = "disconnected"
