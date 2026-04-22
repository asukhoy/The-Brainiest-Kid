from sqlalchemy.ext.asyncio import AsyncSession
from managers import WebSocketManager
from .get_all_players import get_all_players

import logging

logger = logging.getLogger('app')


async def update_lobby(db_session: AsyncSession, session_code: int, websocket_manager: WebSocketManager):
    message = await get_all_players(session_code, db_session)
    logger.info(f'message: {message}')
    to_broadcast = {
        'action': 'update-players',
        'data': message
    }
    await websocket_manager.broadcast(session_code, to_broadcast)