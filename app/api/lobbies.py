from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from app import crud, schemas, models
from app.core import database, auth


router = APIRouter()


@router.post("/create_lobby", response_model=schemas.LobbyOut)
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


@router.post(
    "/quickgame",
    response_model=schemas.LobbyOut,
    summary="Быстрый подбор игры: найти или создать лобби"
)
def quickgame(
    db: Session = Depends(database.get_db),
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


@router.post("/join_lobby/{game_id}", response_model=schemas.LobbyOut)
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
        players=[p.user_id for p in lobby.players],
        created_at=lobby.created_at,
        is_private=lobby.is_private
    )
