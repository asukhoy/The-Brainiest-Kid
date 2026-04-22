from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from sqlalchemy import select

from models import Player, GameSession

async def get_game_data(db_session: AsyncSession, player_id: uuid.UUID):
    query = select(GameSession.game_data).join(GameSession.player).where(Player.id == player_id)
    game_data = await db_session.execute(query)
    game_data = game_data.scalars().first()
    if not game_data:
        raise ValueError('No game data found')
    return game_data