from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import logging

from models import GameSession

logger = logging.getLogger('app')


async def delete_session(
        db_session: AsyncSession,
        session_id: int
):
    session = await db_session.get(GameSession, session_id)
    if session is None:
        raise ValueError('Session not found')
    await db_session.delete(session)
    await db_session.commit()