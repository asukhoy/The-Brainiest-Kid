from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from models import Player
from .get_session_by_code import get_session_by_code

logger = logging.getLogger('app')


async def get_session_players(
        db_session: AsyncSession,
        session_code: int
):
    session = await get_session_by_code(session_code, db_session)
    query = select(Player).where(Player.session_id == session.id)
    res = await db_session.execute(query)
    return res.scalars().all()