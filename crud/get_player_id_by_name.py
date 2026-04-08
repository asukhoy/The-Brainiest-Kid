from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from models import Player
from .get_session_by_code import get_session_by_code

logger = logging.getLogger('app')


async def get_player_id_by_name(
        db_session: AsyncSession,
        session_code: int,
        name: str
):
    session = await get_session_by_code(session_code, db_session)
    query = select(Player).where(Player.session_id == session.id, Player.name == name)
    res = await db_session.execute(query)
    player = res.scalars().first()
    if player is None:
        raise ValueError('Player not found')
    return player.id