from pydantic import BaseModel


class CookieReturn(BaseModel):
    code: int | None
