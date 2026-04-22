from sqlalchemy.ext.asyncio import AsyncSession

from models import Question

async def question_answered(db_session: AsyncSession, session_code: int, round_number: int,
                            question_number: int):
    question = Question(
        session_code=session_code,
        round_number=round_number,
        question=question_number,
    )

    db_session.add(question)