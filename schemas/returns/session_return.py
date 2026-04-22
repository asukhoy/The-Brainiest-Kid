from pydantic import BaseModel, ConfigDict
import uuid

from models import GameMode


class SessionReturn(BaseModel):
    session_code: int
    game_data: str
    current_round: int
    current_mode: GameMode
    secret: uuid.UUID

    model_config = ConfigDict(from_attributes=True)