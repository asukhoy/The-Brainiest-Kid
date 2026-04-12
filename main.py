import uuid
import logging
from typing import List, Annotated

from fastapi import FastAPI, Depends, HTTPException, File, Path, Form, WebSocket, \
    WebSocketDisconnect, Body, Response, Cookie
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi.middleware.cors import CORSMiddleware

from models import Player
from schemas.returns import PlayerReturn, SessionReturn, CookieReturn
from schemas.requests import JoinRequest, ChangeScoreRequest
from db import get_db, init_db, close_db
import crud
from managers import GameManager, WebSocketManager
import handlers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    filename='app.log',
    filemode='a'
)
logger = logging.getLogger('app')

origins = [
    "http://localhost:5173",    # Common React port
    "https://example.com",
    'http://192.168.1.39:5173',
    'http://10.225.218.237:5173',
    'http://192.168.1.68:5173',
]



@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте приложения
    await init_db()
    yield
    # При завершении
    await close_db()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

websocket_manager = WebSocketManager()

@app.post('/change_score', response_model=PlayerReturn)
async def change_score(
        request: ChangeScoreRequest,
        db_session: AsyncSession = Depends(get_db)
):
    try:
        player = await crud.update_player_score(db_session, request.player_id, request.score)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail='database error')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return player.to_dict()


@app.post('/sessions', response_model=SessionReturn)
async def create_session(
        response: Response,
        #question_file_path: str = File(...),
        db_session: AsyncSession = Depends(get_db)
):
    question_file_path = 'a'
    try:
        session = await crud.create_session(db_session, question_file_path)
    except SQLAlchemyError as e:
        await db_session.rollback()
        logger.info(e)
        raise HTTPException(status_code=500, detail=str(e))

    response.set_cookie(
        key='host_session_code',
        value=str(session.code),
        max_age=300,
        httponly=True,
        samesite='lax',
        path='/'
    )

    return session.to_dict()


@app.get('/sessions/previous', response_model=CookieReturn)
async def get_host_session(
        host_session_code: str | None = Cookie(default=None)
):
    resp = host_session_code
    if resp is not None:
        resp = int(resp)
    return {'code': resp}


@app.post('/sessions/join', response_model=PlayerReturn)
async def join_session(
        request: JoinRequest = Body(),
        db_session: AsyncSession = Depends(get_db)
):
    if await handlers.check_player_exists(request.code, request.name, db_session):
        raise HTTPException(status_code=409, detail='User with this name already exists')

    if not await handlers.check_session_exists(request.code, db_session):
        raise HTTPException(status_code=404, detail='session not found')

    player = await crud.create_player(request.code, request.name, db_session)

    message = await handlers.get_all_players(request.code, db_session)
    await websocket_manager.send_to_host(request.code, message)

    await websocket_manager.broadcast(request.code, message)
    return player.to_dict()




@app.get('/sessions/{session_code}/players', response_model=List[PlayerReturn])
async def get_session_players(
        session_code: int = Path(...),
        db_session: AsyncSession = Depends(get_db)
):
    ans = await handlers.get_all_players(session_code, db_session)
    return ans


@app.delete('/sessions/kick/{player_id}')
async def kick_player(
        player_id: uuid.UUID = Path(),
        db_session: AsyncSession = Depends(get_db)
):
    code = await crud.get_code_by_player_id(db_session, player_id)
    try:
        await crud.delete_player(db_session, player_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail='database error')


    message = await handlers.get_all_players(code, db_session)

    await websocket_manager.send_to_host(code, message)
    await websocket_manager.broadcast(code, message)
    await websocket_manager.send_to_player(code, player_id, message)
    await websocket_manager.disconnect_player(code, player_id)

    return {'detail': 'player removed'}


@app.websocket('/ws/host/{session_code}')
async def handle_host(
        websocket: WebSocket,
        session_code: int = Path(...),
        db_session: AsyncSession = Depends(get_db)
):
    logger.info('Got it')
    await websocket_manager.connect_host(session_code, websocket)

    message = await handlers.get_all_players(session_code, db_session)
    await websocket_manager.send_to_host(session_code, message)

    logger.info(f'Host connected to session {session_code}')

    try:
        while True:
            ans = await websocket.receive_json()
            logger.info(f'Host message: {ans}')

            if ans.get('action') == 'abort':
                try:
                    await websocket_manager.broadcast(session_code, [])
                    await handlers.disconnect_all_players(session_code, db_session,
                                                          websocket_manager)

                except SQLAlchemyError:
                    await db_session.rollback()
                    raise HTTPException(status_code=500, detail='database error')

            elif ans.get('action') == 'let-in':
                logger.info(f'letting in {ans.get('player_id')}')
                try:
                    await crud.change_pending_status(db_session, ans.get('player_id'), False)
                    message = await handlers.get_all_players(session_code, db_session)
                    await websocket_manager.send_to_host(session_code, message)
                    await websocket_manager.broadcast(session_code, message)
                except SQLAlchemyError:
                    await db_session.rollback()
                    raise HTTPException(status_code=500, detail='database error')
                except ValueError as e:
                    raise HTTPException(status_code=404, detail=str(e))


    except WebSocketDisconnect:
        logger.info(f'Host disconnected from session {session_code}')

    except Exception as e:
        logger.error(f'Error in handle_host: {e}')
        await websocket.close()


@app.websocket('/ws/player/{player_id}')
async def handle_player(
        websocket: WebSocket,
        player_id: uuid.UUID = Path(...),
        db_session: AsyncSession = Depends(get_db)
):
    logger.info('Got it to endpoint')
    try:
        session_code = await crud.get_code_by_player_id(db_session, player_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail='database error')

    await websocket_manager.connect_player(player_id, websocket, session_code)
    logger.info(f'Player: {player_id} connected to session {session_code}')

    message = await handlers.get_all_players(session_code, db_session)
    await websocket_manager.send_to_player(session_code, player_id, message)

    logger.info(f'message sent to Player: {player_id} connected to session {session_code}')

    try:
        while True:
            ans = await websocket.receive_json()
            logger.info(f'Player message: {ans}')
            if ans['action'] == 'left':
                try:
                    await crud.delete_player(db_session, player_id)
                    raise WebSocketDisconnect()

                except SQLAlchemyError:
                    await db_session.rollback()
                    raise HTTPException(status_code=500, detail='database error')



    except WebSocketDisconnect:
        logger.info(f'Player disconnected from session {session_code}')

        await websocket_manager.disconnect_player(session_code, player_id)
        await crud.change_pending_status(db_session, player_id, False)
        message = await handlers.get_all_players(session_code, db_session)
        await websocket_manager.send_to_host(session_code, message)
        await websocket_manager.broadcast(session_code, message)
    except Exception as e:
        logger.error(f'Error in handle_player: {e}')
        await websocket.close()



if __name__ == "__main__":
    import uvicorn

    uvicorn.run('main:app', host="0.0.0.0", port=5000, reload=True, loop='asyncio',
                log_level='debug')
