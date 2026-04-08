from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import random
import logging

from models import GameSession

logger = logging.getLogger('app')

async def check(
        db_session: AsyncSession,
        code: int
):
    query = select(GameSession).where(GameSession.code == code)
    res = await db_session.execute(query)
    session = res.scalars().first()
    if session is None:
        return True
    return False


async def create_session(
        db_session: AsyncSession,
        path: str
):
    code = 1
    resp = '1'
    logger.info('afsdfhjaosif')
    while True:
        code = random.randint(100000, 1000000)
        resp = await check(db_session, code)
        if resp:
            break
    session = GameSession(
        path=path,
        code=code
    )

    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    return session