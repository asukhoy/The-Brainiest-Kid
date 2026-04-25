from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import logging

from models import Player, PlayerState

logger = logging.getLogger('app')


async def get_player_state(
        db_session: AsyncSession,
        player_id: uuid.UUID
):
    player = await db_session.get(Player, player_id)
    if player is None:
        raise ValueError('Player not found')
    return player.state