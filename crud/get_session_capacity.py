from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from models import Player

logger = logging.getLogger('app')


async def get_session_capacity(
        db_session: AsyncSession,
        session_code: int
) -> int:
    query = select(Player).where(Player.session_code == session_code)
    res = await db_session.execute(query)
    return len(res.scalars().all())
