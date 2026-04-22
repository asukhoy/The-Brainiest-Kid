from pydantic import BaseModel
import uuid


class ReconnectSessionRequest(BaseModel):
    session_code: int
    secret: uuid.UUID