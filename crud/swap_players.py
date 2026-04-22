from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import logging

from models import Player, PlayerState

logger = logging.getLogger('app')


async def swap_players(
    db_session: AsyncSession,
    player_id_exist: uuid.UUID,
    player_id_swap: uuid.UUID
):
    player_exist = await db_session.get(Player, player_id_exist)
    if player_exist is None:
        raise ValueError('player not found')

    player_swap = await db_session.get(Player, player_id_swap)
    if player_swap is None:
        raise ValueError('player swap not found')

    player_swap.name = player_exist.name
    player_swap.state = PlayerState.CONNECTED
    player_swap.score = player_exist.score
    player_swap.turn = player_exist.turn
