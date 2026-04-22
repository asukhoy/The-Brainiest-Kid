from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import logging

from models import Player, PlayerState

logger = logging.getLogger('app')


async def change_player_state(
    db_session: AsyncSession,
    player_id: uuid.UUID,
    state: PlayerState
):
    player = await db_session.get(Player, player_id)
    if player is None:
        raise ValueError('Player not found')
    player.state = state