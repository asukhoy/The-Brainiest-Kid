from pydantic import BaseModel


class CookieReturn(BaseModel):
    session_code: int | None
