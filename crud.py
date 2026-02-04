from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import random

from models import Player, GameSession


async def update_player_score(
        db_session: AsyncSession,
        player_id: uuid.UUID,
        new_score: int
):
    try:
        player = await db_session.get(Player, player_id)
        if player is None:
            raise ValueError('Player not found')

        player.score = new_score
        await db_session.commit()
        await db_session.refresh(player)
        return player
    except Exception:
        await db_session.rollback()


async def get_session_by_code(
        code: int,
        db_session: AsyncSession
):
    query = select(GameSession).where(GameSession.code == code)
    res = await db_session.execute(query)
    return res.scalars().first()


async def create_session(
        db_session: AsyncSession,
        path: str
):
    session = GameSession(
        path=path,
        code=random.randint(100000, 1000000)
    )

    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    return session


async def create_player(
        session_code: int,
        name: str,
        db_session: AsyncSession
):
    session = await get_session_by_code(session_code, db_session)
    player = Player(
        session_id=session.id,
        name=name
    )

    db_session.add(player)
    await db_session.commit()
    await db_session.refresh(player)

    return player
