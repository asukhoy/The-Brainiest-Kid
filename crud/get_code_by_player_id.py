from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging

from models import Player, GameSession

logger = logging.getLogger('app')


async def get_code_by_player_id(
        db_session: AsyncSession,
        player_id: uuid.UUID
) -> int:
    player = await db_session.get(Player, player_id)
    query = select(GameSession.code).where(GameSession.id == player.session_id)
    res = await db_session.execute(query)
    code = res.scalars().first()
    if code is None:
        raise ValueError('Code not found')
    return code