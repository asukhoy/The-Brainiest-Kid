from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import random
import logging

from models import GameSession

logger = logging.getLogger('app')

async def check(
        db_session: AsyncSession,
        session_code: int
):
    query = select(GameSession).where(GameSession.session_code == session_code)
    res = await db_session.execute(query)
    session = res.scalars().first()
    if session is None:
        return True
    return False


async def create_session(
        db_session: AsyncSession,
        game_data: str
):
    session_code = 1
    resp = '1'
    logger.info('afsdfhjaosif')
    while True:
        session_code = random.randint(100000, 1000000)
        resp = await check(db_session, session_code)
        if resp:
            break
    session = GameSession(
        game_data=game_data,
        session_code=session_code
    )

    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    return session