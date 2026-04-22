from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from models import Player

logger = logging.getLogger('app')


async def get_player_id_by_name(
        db_session: AsyncSession,
        session_code: int,
        name: str
):
    query = select(Player).where(Player.session_code == session_code, Player.name == name)
    res = await db_session.execute(query)
    player = res.scalars().first()
    if player is None:
        raise ValueError('Player not found')
    return player.id
