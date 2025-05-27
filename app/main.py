import io
import os
import uuid
from typing import List, Dict, Any

import aiofiles
from fastapi.responses import StreamingResponse, FileResponse

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from uuid import uuid4

from . import crud, models, schemas, auth, database, simulation
import app.websocket as ws_handler
from .database import get_db

app = FastAPI()


from fastapi.middleware.cors import CORSMiddleware


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Можно заменить "*" на ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],  # Разрешает все методы (GET, POST и т.д.)
    allow_headers=["*"],  # Разрешает все заголовки
)


MEDIA_DIR = "media"


@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_username = crud.get_user_by_username(db, username=user.username)
    if db_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    return crud.create_user(db=db, user=user)


@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/protected")
def protected_route(current_user: models.User = Depends(auth.get_current_user)):
    return {"message": f"Hello, {current_user.username}. You have access to this protected route!"}


@app.get("/users/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    """Endpoint to get details of the currently authenticated user."""

    return current_user


@app.get(
    "/users/me/matches",
    response_model=List[schemas.MatchResultOut],
    summary="История ваших матчей"
)
def read_my_match_history(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    - skip: сколько записей пропустить (для пагинации)
    - limit: максимальное число матчей в ответе
    """
    return crud.get_matches_by_user(db, current_user.id, skip=skip, limit=limit)


@app.put("/update_profile", response_model=schemas.UserOut)
def update_profile(data: schemas.UserUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_user = crud.get_user_by_email(db, email=current_user.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Only allow updating username, theme, and avatar
    for field, val in data.dict(exclude_unset=True).items():
        setattr(current_user, field, val)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.put("/change_password")
def change_password(old_password: str, new_password: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_user = crud.get_user_by_email(db, email=current_user.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify old password
    if not auth.verify_password(old_password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    db_user.hashed_password = auth.hash_password(new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@app.post("/create_lobby", response_model=schemas.LobbyOut)
def create_lobby(payload: schemas.LobbyCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    game_id = str(uuid4())

    avg = current_user.rating
    lobby = crud.create_lobby(
        db=db,
        game_id=game_id,
        host_id=current_user.id,
        avg_rating=avg,
        is_private=payload.is_private,
    )

    crud.join_lobby(db, current_user.id, lobby.id)
    db.refresh(lobby)
    return schemas.LobbyOut(
        id=lobby.id,
        game_id=lobby.game_id,
        host_id=lobby.host_id,
        status=lobby.status,
        players=[p.user_id for p in lobby.players],
        created_at=lobby.created_at,
        is_private=lobby.is_private
    )


@app.post(
    "/quickgame",
    response_model=schemas.LobbyOut,
    summary="Быстрый подбор игры: найти или создать лобби"
)
def quickgame(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Пытается найти открытое лобби на ожидании с близким рейтингом.
    Если найдено — присоединяется, иначе создаёт новое (закрытое по умолчанию).
    """
    user_rating = current_user.rating

    lobby = crud.get_quickgame_lobby(db, current_user.id, user_rating)

    if lobby:
        crud.join_lobby(db, current_user.id, lobby.id)
        db.refresh(lobby)
    else:
        game_id = str(uuid4())

        lobby = crud.create_lobby(
            db=db,
            host_id=current_user.id,
            game_id=game_id,
            avg_rating=user_rating,
            is_private=False,
        )

        crud.join_lobby(db, current_user.id, lobby.id)
        db.refresh(lobby)

    return schemas.LobbyOut(
        id=lobby.id,
        game_id=str(lobby.game_id),
        host_id=lobby.host_id,
        status=lobby.status,
        players=[p.user_id for p in lobby.players],
        created_at=lobby.created_at,
        is_private=lobby.is_private
    )


@app.post("/join_lobby/{game_id}", response_model=schemas.LobbyOut)
def join_lobby(game_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    lobby = crud.get_lobby(db, game_id)
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")
    crud.join_lobby(db, current_user.id, lobby.id)
    db.refresh(lobby)
    return schemas.LobbyOut(
        id=lobby.id,
        game_id=lobby.game_id,
        host_id=lobby.host_id,
        status=lobby.status,
        players=[p.user_id for p in lobby.players]
    )


@app.websocket("/ws/{lobby_id}")
async def websocket_endpoint(websocket: WebSocket, lobby_id: str, db: Session = Depends(get_db)):
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    # try:
    #     user = auth.get_current_user(token, db)
    # except Exception:
    #     await websocket.close(code=1008)
    #     return

    try:
        user = auth.get_current_user(token, db)
    except Exception as e:
        print("Token decode failed:", e)
        await websocket.close(code=1008)
        return

    await ws_handler.handle_ws(websocket, user.id, lobby_id, db)


@app.post("/uploadfile")
async def create_upload_file(file: UploadFile):
    file_name = str(uuid.uuid4())
    extension = file.filename.split('.')[1]

    async with aiofiles.open(f"{MEDIA_DIR}/{file_name}.{extension}", 'wb') as out_file:
        content = await file.read()  # async read
        await out_file.write(content)  # async write

    result = {
        "status": "ok",
        "original_file": f"/loadfile/{file_name}.{extension}"
    }

    return result


@app.get("/loadfile/{file_path}", response_class=FileResponse)
async def load_file(file_path: str):
    full_path = os.path.join(MEDIA_DIR, file_path)
    if not os.path.isfile(full_path):
        raise HTTPException(404, "No such file")

    return FileResponse(
        path=full_path,
        media_type="application/octet-stream",        # generic fallback
        filename=os.path.basename(full_path),         # suggests a download filename
    )


@app.get(
    "/replays/{replay_id}",
    response_model=schemas.ReplayOut,
    summary="Получить повтор по ID"
)
def read_replay(
    replay_id: int,
    db       : Session = Depends(database.get_db)
):
    replay = crud.get_replay(db, replay_id)
    if not replay:
        raise HTTPException(404, "Replay not found")
    return replay


@app.get(
    "/replays/{replay_id}/frames",
    summary="Воссоздать и вернуть кадры игры по реплею"
)
def replay_frames(
    replay_id: int,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    replay = crud.get_replay(db, replay_id)
    if not replay:
        raise HTTPException(status_code=404, detail="Replay not found")

    frames = simulation.simulate_replay(
        replay.game_params,
        replay.initial_map,
        replay.actions
    )
    return frames


@app.get(
    "/replays/match/{match_id}",
    response_model=schemas.ReplayOut,
    summary="Получить повтор по ID"
)
def read_replay(
    match_id: int,
    db       : Session = Depends(database.get_db)
):
    replay = crud.get_replay_by_match_id(db, match_id)
    if not replay:
        raise HTTPException(404, "Replay not found")
    return replay


@app.get(
    "/replays/match/{match_id}/frames",
    summary="Воссоздать и вернуть кадры игры по match_id"
)
def replay_frames_by_match(
    match_id: int,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    replay = crud.get_replay_by_match_id(db, match_id)
    if not replay:
        raise HTTPException(status_code=404, detail="Replay not found")

    frames = simulation.simulate_replay(
        replay.game_params,
        replay.initial_map,
        replay.actions
    )
    return frames
