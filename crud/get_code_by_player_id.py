from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import logging

from models import Player

logger = logging.getLogger('app')


async def get_code_by_player_id(
        db_session: AsyncSession,
        player_id: uuid.UUID
):
    player = await db_session.get(Player, player_id)
    if player is None:
        raise ValueError('Code not found')
    return player.session_code
