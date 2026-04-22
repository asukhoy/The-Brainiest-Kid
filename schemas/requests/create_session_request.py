from pydantic import BaseModel
import uuid
from typing import Any


class CreateSessionRequest(BaseModel):
    game_data: str