from sqlalchemy.ext.asyncio import AsyncSession
import logging

from models import GameSession

logger = logging.getLogger('app')


async def delete_session(
        db_session: AsyncSession,
        session_code: int
):
    session = await db_session.get(GameSession, session_code)
    if session is None:
        raise ValueError('Session not found')
    await db_session.delete(session)
    await db_session.commit()
