from pydantic import BaseModel, ConfigDict
import uuid

from models import PlayerState


class PlayerReturn(BaseModel):
    id: uuid.UUID
    session_code: int
    name: str
    score: int
    state: PlayerState
    turn: int
    game_data: str | None = None

    model_config = ConfigDict(from_attributes=True)