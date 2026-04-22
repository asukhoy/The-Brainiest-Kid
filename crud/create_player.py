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
        session_code=session_code,
        name=name
    )

    db_session.add(player)

    return player
