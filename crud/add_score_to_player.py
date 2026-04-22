from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import logging

from models import Player

logger = logging.getLogger('app')


async def add_score_to_player(
        db_session: AsyncSession,
        player_id: uuid.UUID,
        new_score: int
):
    player = await db_session.get(Player, player_id)
    if player is None:
        raise ValueError('Player not found')

    player.score += new_score