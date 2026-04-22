from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import Player, PlayerState

async def find_maximum_turn(db_session: AsyncSession, session_code: int):
    query = select(func.max(Player.turn)).where(Player.session_code == session_code, Player.state
                                                != PlayerState.ELIMINATED)
    result = await db_session.execute(query)
    result = result.scalar()
    if result is None:
        raise ValueError('Players not found')
    return result