from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from models import Player

logger = logging.getLogger('app')


async def get_session_players(
        db_session: AsyncSession,
        session_code: int
):
    query = select(Player).where(Player.session_id == session_code)
    res = await db_session.execute(query)
    return res.scalars().all()
