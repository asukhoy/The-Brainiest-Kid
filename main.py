import uuid

from fastapi import FastAPI, Depends, HTTPException, File, Path, Form
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from schemas import ChangeScoreRequest
from db import get_db, init_db, close_db
import crud


@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте приложения
    await init_db()
    yield
    # При завершении
    await close_db()

app = FastAPI(lifespan=lifespan)

@app.post('/change_score')
async def change_score(
        request: ChangeScoreRequest,
        db_session: AsyncSession = Depends(get_db)
):
    print(0)
    try:
        print(1)
        player = await crud.update_player_score(db_session, request.player_id, request.score)
        print(2)
        return player.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail='database error')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/sessions')
async def create_session(
        #question_file_path: str = File(...),
        db_session: AsyncSession = Depends(get_db)
):
    question_file_path = 'a'
    try:
        session = await crud.create_session(db_session, question_file_path)
    except SQLAlchemyError as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return session.to_dict()


@app.post('/sessions/{session_code}/join')
async def join_session(
        session_code: int = Path(...),
        name: str = Form(...),
        db_session: AsyncSession = Depends(get_db)
):
    try:
        player = await crud.create_player(session_code, name, db_session)
    except SQLAlchemyError:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail='database error')

    return player.to_dict()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run('main:app', host="0.0.0.0", port=5000, reload=True, loop='asyncio')
