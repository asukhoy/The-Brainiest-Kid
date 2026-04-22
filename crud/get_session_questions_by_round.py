from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from models import Question

logger = logging.getLogger('app')


async def get_session_questions_by_round(
        db_session: AsyncSession,
        session_code: int,
        round_number: int
):
    query = select(Question).where(Question.session_code == session_code, Question.round_number == round_number)
    res = await db_session.execute(query)
    return res.scalars().all()
