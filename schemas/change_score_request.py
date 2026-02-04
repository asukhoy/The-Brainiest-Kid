from pydantic import BaseModel
import uuid


class ChangeScoreRequest(BaseModel):
    player_id: uuid.UUID
    score: int