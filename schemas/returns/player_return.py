from pydantic import BaseModel, ConfigDict
import uuid


class PlayerReturn(BaseModel):
    id: uuid.UUID
    session_id: int
    name: str
    score: int
    is_connected: bool
    is_eliminated: bool
    is_pending: bool

    model_config = ConfigDict(from_attributes=True)