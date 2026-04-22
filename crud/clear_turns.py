from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Player

async def clear_turns(db_session: AsyncSession, session_code: int):
    query = select(Player).where(Player.session_code == session_code)
    result = await db_session.execute(query)
    res = result.scalars().all()
    if res is not None:
        for player in res:
            player.turn = -1
