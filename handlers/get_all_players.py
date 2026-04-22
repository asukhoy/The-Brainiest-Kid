from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
import crud
from fastapi import HTTPException


async def get_all_players(session_code: int, db_session: AsyncSession):
    try:
        players = await crud.get_session_players(db_session, session_code)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail='database error')

    return [p.to_dict() for p in players]