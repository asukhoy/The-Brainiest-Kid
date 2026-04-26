import uuid
import logging
from typing import List, Annotated

from fastapi import FastAPI, Depends, HTTPException, File, Path, Form, WebSocket, \
    WebSocketDisconnect, Body, Response, Cookie
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi.middleware.cors import CORSMiddleware

from models import Player, GameSession, PlayerState, GameMode
from schemas.returns import PlayerReturn, SessionReturn, CookieReturn
import schemas.requests
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
    'http://10.111.84.60:5173',
    'http://10.111.84.210:5000'
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
game_manager = GameManager()

@app.post('/change_score', response_model=PlayerReturn)
async def change_score(
        request: schemas.requests.ChangeScoreRequest,
        db_session: AsyncSession = Depends(get_db)
):
    try:
        player = await crud.update_player_score(db_session, request.player_id, request.score)
        await db_session.commit()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail='database error')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return player


@app.post('/sessions', response_model=SessionReturn)
async def create_session(
        request: schemas.requests.CreateSessionRequest,
        db_session: AsyncSession = Depends(get_db)
):

    try:
        session = await crud.create_session(db_session, request.game_data)
    except SQLAlchemyError as e:
        await db_session.rollback()
        logger.info(e)
        raise HTTPException(status_code=500, detail=str(e))

    return session

@app.post('/sessions/reconnect', response_model=SessionReturn)
async def reconnect_session(
        request: schemas.requests.ReconnectSessionRequest,
        db_session: AsyncSession = Depends(get_db)
):
    try:
        session = await db_session.get(GameSession, request.session_code)
    except SQLAlchemyError as e:
        await db_session.rollback()
        logger.info(e)
        raise HTTPException(status_code=500, detail=str(e))

    if session.secret != request.secret:
        raise HTTPException(status_code=401, detail='invalid session secret')

    return session


@app.post('/sessions/join', response_model=PlayerReturn)
async def join_session(
        request: schemas.requests.JoinRequest = Body(),
        db_session: AsyncSession = Depends(get_db)
):
    if await handlers.check_player_exists(request.session_code, request.name, db_session):
        raise HTTPException(status_code=409, detail='User with this name already exists')

    if not await handlers.check_session_exists(request.session_code, db_session):
        raise HTTPException(status_code=404, detail='session not found')


    try:
        player = await crud.create_player(request.session_code, request.name, db_session)
        await db_session.commit()
        await db_session.refresh(player)
    except SQLAlchemyError as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    await handlers.update_lobby(db_session, request.session_code, websocket_manager)
    pl = PlayerReturn.model_validate(player)
    try:
        game_data = await crud.get_game_data(db_session, pl.id)
        pl.game_data = game_data
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return pl




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

    try:
        session_code = await crud.get_code_by_player_id(db_session, player_id)
        await crud.delete_player(db_session, player_id)
        await db_session.commit()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail='database error')


    await handlers.update_lobby(db_session, session_code, websocket_manager)
    await websocket_manager.disconnect_player(session_code, player_id)

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
    mes = {
        'action': 'update-players',
        'data': message
    }
    await websocket_manager.send_to_host(session_code, mes)

    logger.info(f'Host connected to session {session_code}')

    try:
        while True:
            ans = await websocket.receive_json()
            logger.info(f'Host message: {ans}')
            match ans.get('action'):
                case 'abort':
                    try:
                        await websocket_manager.send_to_players(session_code,
                    {
                                'action': 'abort'
                            }
                        )
                        await websocket_manager.disconnect_host(session_code)

                        await crud.delete_session(db_session, session_code)
                        await db_session.commit()

                    except SQLAlchemyError:
                        await db_session.rollback()
                        raise HTTPException(status_code=500, detail='database error')

                case 'let-in':
                    logger.info(f'letting in {ans.get('player_id')}')
                    try:
                        cnt = await crud.get_session_capacity(db_session, session_code)
                        if cnt == 12:
                            continue
                        await crud.change_player_state(
                                                        db_session,
                                                        uuid.UUID(ans.get('data').get('player_id')),
                                                        PlayerState.CONNECTED
                                                       )
                        await db_session.commit()
                        await handlers.update_lobby(db_session, session_code, websocket_manager)
                    except SQLAlchemyError as e:
                        await db_session.rollback()
                        raise HTTPException(status_code=500, detail=str(e))
                    except ValueError as e:
                        raise HTTPException(status_code=404, detail=str(e))

                case 'kick':
                    player_id = uuid.UUID(ans.get('data').get('player_id'))

                    try:
                        session_code = await crud.get_code_by_player_id(db_session, player_id)
                        await crud.delete_player(db_session, player_id)
                        await db_session.commit()
                    except ValueError as e:
                        raise HTTPException(status_code=404, detail=str(e))
                    except SQLAlchemyError:
                        await db_session.rollback()
                        raise HTTPException(status_code=500, detail='database error')

                    await websocket_manager.broadcast(session_code, {
                        'action': 'kick',
                        'data': {
                            'player_id': player_id
                        }
                    })

                    await handlers.update_lobby(db_session, session_code, websocket_manager)
                    await websocket_manager.disconnect_player(session_code, player_id)

                case 'swap':
                    player_id_exist = uuid.UUID(ans.get('data').get('player_id'))
                    player_id_swap = uuid.UUID(ans.get('data').get('player_id_swap'))

                    logger.info(f'Swapping {player_id_exist} to {player_id_swap}')

                    try:
                        await crud.swap_players(db_session, player_id_exist, player_id_swap)
                        await crud.delete_player(db_session, player_id_exist)
                        await db_session.commit()
                        await handlers.update_lobby(db_session, session_code, websocket_manager)
                    except SQLAlchemyError as e:
                        await db_session.rollback()
                        raise HTTPException(status_code=500, detail=str(e))
                    except ValueError as e:
                        raise HTTPException(status_code=404, detail=str(e))

                    await handlers.update_lobby(db_session, session_code, websocket_manager)


                case 'next-round':
                    try:
                        await crud.change_round(db_session, session_code)
                        await crud.clear_turns(db_session, session_code)
                        await db_session.commit()
                    except SQLAlchemyError as e:
                        await db_session.rollback()
                        raise HTTPException(status_code=500, detail=str(e))

                    await websocket_manager.broadcast(session_code, {
                        'action': 'next-round'
                    })

                case 'next-mode':
                    try:
                        mode = ans.get('data').get('mode')
                        await crud.change_mode(db_session, session_code, mode)
                        await db_session.commit()
                    except SQLAlchemyError as e:
                        await db_session.rollback()
                        raise HTTPException(status_code=500, detail=str(e))
                    except ValueError as e:
                        raise HTTPException(status_code=404, detail=str(e))

                    await websocket_manager.broadcast(session_code, {
                        'action': 'next-round',
                        'data' : {
                            'mode': mode
                        }
                    })

                case 'players-eliminated':
                    try:
                        for player in ans.get('data').get('eliminated_players_ids'):
                            await crud.change_player_state(db_session, uuid.UUID(player),
                                                           PlayerState.ELIMINATED)
                        await db_session.commit()
                    except SQLAlchemyError as e:
                        await db_session.rollback()
                        raise HTTPException(status_code=500, detail=str(e))
                    except ValueError as e:
                        raise HTTPException(status_code=404, detail=str(e))

                    await websocket_manager.broadcast(session_code, {
                        'action': 'players-eliminated',
                        'data' : ans.get('data')

                    })

                case 'show-leaderboard':
                    await websocket_manager.broadcast(session_code, {
                        'action': 'show-leaderboard'
                    })

                case 'round1:next-question':
                    try:
                        await crud.question_answered(db_session, session_code, 1,
                                                     int(ans.get('data').get('question')))
                        await db_session.commit()
                    except SQLAlchemyError as e:
                        await db_session.rollback()
                        raise HTTPException(status_code=500, detail=str(e))
                    await websocket_manager.broadcast(session_code, {
                        'action': 'round1:next-question',
                        'data': ans.get('data')
                    })

                case 'round1:show-answer':
                    await websocket_manager.broadcast(session_code, {
                        'action': 'round1:show-answer'
                    })

                case 'round2:show-categories':
                    await websocket_manager.broadcast(session_code, {
                        'action': 'round2:show-categories'
                    })

                case 'round2:start-category':

                    await websocket_manager.broadcast(session_code, {
                        'action': 'round2:show-categories',
                        'data': ans.get('data')
                    })

                case 'round2:next-question':
                    await websocket_manager.broadcast(session_code, {
                        'action': 'round2:next-question',
                        'data': ans.get('data')
                    })

                case 'round2:category-answered':
                    try:
                        await crud.add_score_to_player(db_session, uuid.UUID(ans.get('data').get(
                            'player_id')), int(ans.get('data').get('added_score')))
                        await crud.question_answered(db_session, session_code, 2,
                                                     int(ans.get('data').get('category_idx')))
                        await db_session.commit()
                    except SQLAlchemyError as e:
                        await db_session.rollback()
                        raise HTTPException(status_code=500, detail=str(e))
                    except ValueError as e:
                        raise HTTPException(status_code=404, detail=str(e))

                    await websocket_manager.broadcast(session_code, {
                        'action': 'round2-category-answered',
                        'data': ans.get('data')
                    })

                case 'round3:assign-order':
                    try:
                        for i, pl in enumerate(ans.get('data').get('player_id_order')):
                            await crud.change_player_turn(db_session, uuid.UUID(pl), i)
                        await db_session.commit()
                    except SQLAlchemyError as e:
                        await db_session.rollback()
                        raise HTTPException(status_code=500, detail=str(e))
                    except ValueError as e:
                        raise HTTPException(status_code=404, detail=str(e))

                    await websocket_manager.broadcast(session_code, {
                        'action': 'round3:assign-order',
                        'data': {
                            'player_id_order': ans.get('data').get('player_id_order')
                        }
                    })

                case 'round3:assign-categories':
                    await websocket_manager.broadcast(session_code, {
                        'action': 'round3:assign-categories',
                        'data': ans.get('data')
                    })

                case 'round3:show-categories':
                    await websocket_manager.broadcast(session_code, {
                        'action': 'round3:show-categories'
                    })

                case 'round3:select-cell':
                    await websocket_manager.broadcast(session_code, {
                        'action': 'round3:select-cell',
                        'data': ans.get('data')
                    })

                case 'round3:cell-answered':
                    try:
                        pl_id = uuid.UUID(ans.get('data').get('player_id'))
                        score = int(ans.get('data').get('added_score'))
                        await crud.add_score_to_player(db_session, pl_id, score)
                        await db_session.commit()
                    except SQLAlchemyError as e:
                        await db_session.rollback()
                        raise HTTPException(status_code=500, detail=str(e))
                    except ValueError as e:
                        raise HTTPException(status_code=404, detail=str(e))

                    await websocket_manager.broadcast(session_code, {
                        'action': 'round3-cell-answered',
                        'data': ans.get('data')
                    })

                case 'round3:finish-round':
                    await websocket_manager.broadcast(session_code, {
                        'action': 'round3:finish-round',
                    })

                case _:
                    await websocket_manager.broadcast(session_code, {
                        'action': ans.get('action'),
                        'data': ans.get('data')
                    })


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
        state = await crud.get_player_state(db_session, player_id)
        if state == PlayerState.DISCONNECTED:
            await crud.change_player_state(db_session, player_id, PlayerState.CONNECTED)
        await db_session.commit()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail='database error')

    await websocket_manager.connect_player(player_id, websocket, session_code)
    await handlers.update_lobby(db_session, session_code, websocket_manager)
    logger.info(f'Player: {player_id} connected to session {session_code}')


    logger.info(f'message sent to Player: {player_id} connected to session {session_code}')

    try:
        while True:
            ans = await websocket.receive_json()
            logger.info(f'Player message: {ans}')
            match ans.get('action'):
                case 'left':
                    try:
                        await crud.delete_player(db_session, player_id)
                        await db_session.commit()
                        raise WebSocketDisconnect()

                    except SQLAlchemyError as e:
                        await db_session.rollback()
                        raise HTTPException(status_code=500, detail=str(e))

                case 'decoder:finished':
                    try:
                        turn = await crud.find_maximum_turn(db_session, session_code)
                        await crud.change_player_turn(db_session, player_id, turn + 1)
                        await db_session.commit()
                    except SQLAlchemyError as e:
                        await db_session.rollback()
                        raise HTTPException(status_code=500, detail=str(e))
                    except ValueError as e:
                        raise HTTPException(status_code=404, detail=str(e))

                    await websocket_manager.broadcast(session_code, {
                        'action': 'decoder:finished',
                    })

                case 'tiebreak:finished':
                    await websocket_manager.broadcast(session_code, {
                        'action': 'tiebreak:finished'
                    })

                case 'round1:answered':
                    if ans.get('data').get('is_correct'):
                        try:
                            await crud.add_score_to_player(db_session, player_id, 1)
                            await db_session.commit()
                        except SQLAlchemyError as e:
                            await db_session.rollback()
                            raise HTTPException(status_code=500, detail=str(e))
                        except ValueError as e:
                            raise HTTPException(status_code=404, detail=str(e))

                    await websocket_manager.broadcast(session_code, {
                        'action': 'round1:answered',
                        'data': ans.get('data')
                    })

                case 'round2:question-skip':
                    await websocket_manager.broadcast(session_code, {
                        'action': 'round2:question-skip',
                        'data': ans.get('data')
                    })
                case _:
                    await websocket_manager.broadcast(session_code, {
                        'action': ans.get('action'),
                        'data': ans.get('data')
                    })


    except WebSocketDisconnect:
        logger.info(f'Player {player_id} disconnected from session {session_code}')

        await websocket_manager.disconnect_player(session_code, player_id)
        try:
            player = await db_session.get(Player, player_id)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=str(e))

        if player.state == PlayerState.PENDING:
            try:
                await crud.delete_player(db_session, player_id)
                await db_session.commit()
            except SQLAlchemyError as e:
                await db_session.rollback()
                raise HTTPException(status_code=500, detail=str(e))
        else:
            try:
                state = await crud.get_player_state(db_session, player_id)
                if state != PlayerState.ELIMINATED:
                    await crud.change_player_state(db_session, player_id, PlayerState.DISCONNECTED)
                    await db_session.commit()
            except SQLAlchemyError as e:
                await db_session.rollback()
                logger.error(f'Error in handle_player: {e}')
                raise HTTPException(status_code=500, detail=str(e))
        await handlers.update_lobby(db_session, session_code, websocket_manager)
    except Exception as e:
        logger.error(f'Error in handle_player: {e}')
        await websocket.close()



if __name__ == "__main__":
    import uvicorn

    uvicorn.run('main:app', host="0.0.0.0", port=5000, reload=True, loop='asyncio',
                log_level='debug')
