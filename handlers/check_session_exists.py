from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from models import GameSession


async def check_session_exists(
        session_code: int,
        db_session: AsyncSession
) -> bool:
    try:
        query = select(GameSession).where(GameSession.session_code == session_code)
        res = await db_session.execute(query)
        return res.scalars().first() is not None
    except SQLAlchemyError:
        raise