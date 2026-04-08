from sqlalchemy.ext.asyncio import AsyncSession
import logging
from models import Player

logger = logging.getLogger('app')


async def create_player(
        session_code: int,
        name: str,
        db_session: AsyncSession
):
    player = Player(
        session_id=session_code,
        name=name
    )

    db_session.add(player)
    await db_session.commit()
    await db_session.refresh(player)

    return player
