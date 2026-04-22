from sqlalchemy.ext.asyncio import AsyncSession

from models import GameSession, GameMode

async def change_mode(db_session: AsyncSession, session_code: int, mode: GameMode):
    session = await db_session.get(GameSession, session_code)
    if session is None:
        raise ValueError('Session not found')
    session.current_mode = mode