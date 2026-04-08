from sqlalchemy.ext.asyncio import AsyncSession
import logging

from models import Player
from .get_session_by_code import get_session_by_code

logger = logging.getLogger('app')


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