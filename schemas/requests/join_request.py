from pydantic import BaseModel
import uuid


class JoinRequest(BaseModel):
    name: str
    session_code: int