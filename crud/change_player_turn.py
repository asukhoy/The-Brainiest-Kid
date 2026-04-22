from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from models import Player

async def change_player_turn(db_session: AsyncSession, player_id: uuid.UUID, new_turn: int):
    player = await db_session.get(Player, player_id)
    if not player:
        raise ValueError('Player not found')
    player.turn = new_turn