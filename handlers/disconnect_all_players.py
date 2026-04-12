import uuid

from sqlalchemy.ext.asyncio import AsyncSession

import crud
from managers import WebSocketManager
from .get_all_players import get_all_players


async def disconnect_all_players(session_code: int, db_session: AsyncSession, websocket_manager: WebSocketManager):
    players_dict = await get_all_players(session_code, db_session)
    for player in players_dict:
        await crud.delete_player(db_session, uuid.UUID(player['id']))

    await websocket_manager.disconnect_host(session_code)

    await crud.delete_session(db_session, session_code)