from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from models import GameSession

logger = logging.getLogger('app')


async def get_session_by_code(
        code: int,
        db_session: AsyncSession
):
    query = select(GameSession).where(GameSession.code == code)
    res = await db_session.execute(query)
    session = res.scalars().first()
    if session is None:
        raise ValueError('Session not found')
    return session