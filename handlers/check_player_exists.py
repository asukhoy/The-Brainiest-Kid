from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

import crud


async def check_player_exists(
        session_code: int,
        name: str,
        db_session: AsyncSession
) -> bool:
    try:
        await crud.get_player_id_by_name(db_session, session_code, name)
        return True
    except ValueError:
        return False
    except SQLAlchemyError:
        raise