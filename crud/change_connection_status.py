from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import logging

from models import Player

logger = logging.getLogger('app')


async def change_connection_status(
    db_session: AsyncSession,
    player_id: uuid.UUID,
    status: bool
):
    player = await db_session.get(Player, player_id)
    if player is None:
        raise ValueError('Player not found')
    player.is_connected = status
    await db_session.commit()