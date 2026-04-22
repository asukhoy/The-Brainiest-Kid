import uuid

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from .websocket_manager import WebSocketManager
import crud


class GameManager:

    async def next_round(self, db_session: AsyncSession, session_code: int):
        try:
            await crud.change_round(db_session, session_code)
            await crud.clear_turns(db_session, session_code)
            await db_session.commit()
        except SQLAlchemyError as e:
            await db_session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
