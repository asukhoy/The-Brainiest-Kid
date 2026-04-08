from pydantic import BaseModel, ConfigDict
import uuid


class SessionReturn(BaseModel):
    code: int
    path: str
    current_round: int
    current_question: int

    model_config = ConfigDict(from_attributes=True)