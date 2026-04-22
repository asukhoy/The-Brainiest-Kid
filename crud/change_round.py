from sqlalchemy.ext.asyncio import AsyncSession

from models import GameSession, GameMode

async def change_round(db_session: AsyncSession, session_code: int):
    session = await db_session.get(GameSession, session_code)
    if session is None:
        raise ValueError('Session not found')
    session.current_round += 1
    session.current_mode = GameMode.DECODER