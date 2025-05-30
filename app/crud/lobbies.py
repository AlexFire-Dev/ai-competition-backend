from sqlalchemy.orm import Session
from app import models, schemas
from fastapi import HTTPException
from sqlalchemy import or_, func
from typing import Optional


def create_lobby(
    db: Session,
    game_id: str,
    host_id: int,
    avg_rating: float,
    is_private: bool = True,
) -> models.Lobby:
    lobby = models.Lobby(
        host_id=host_id,
        game_id=game_id,
        avg_rating=avg_rating,
        is_private=is_private,
        status=models.LobbyStatus.waiting,
    )
    db.add(lobby)
    db.commit()
    db.refresh(lobby)
    return lobby


def update_lobby_status(
    db: Session,
    lobby_id: int,
    new_status: models.LobbyStatus,
) -> models.Lobby:
    lobby = db.query(models.Lobby).filter(models.Lobby.id == lobby_id).first()
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")
    lobby.status = new_status
    db.commit()
    db.refresh(lobby)
    return lobby


def get_quickgame_lobby(
    db: Session,
    user_id: int,
    user_rating: float,
    max_delta: float = 200.0,
    only_open: bool = True,
    require_game_id: bool = True,
) -> Optional[models.Lobby]:
    # Базовый фильтр: только waiting
    q = db.query(models.Lobby).filter(
        models.Lobby.status == models.LobbyStatus.waiting
    )

    # Только публичные, если нужно
    if only_open:
        q = q.filter(models.Lobby.is_private == False)

    # Только с game_id, если нужно
    if require_game_id:
        q = q.filter(models.Lobby.game_id != None)

    # По рейтингу
    q = q.filter(
        models.Lobby.avg_rating.between(
            user_rating - max_delta,
            user_rating + max_delta
        )
    )

    # Исключаем лобби, где этот пользователь уже играет
    q = q.filter(
        ~models.Lobby.players.any(models.LobbyPlayer.user_id == user_id)
    )

    # Оставляем только те, где сейчас меньше 2 участников
    q = (
        q
        .outerjoin(models.LobbyPlayer, models.Lobby.id == models.LobbyPlayer.lobby_id)
        .group_by(models.Lobby.id)
        .having(func.count(models.LobbyPlayer.id) < 2)
    )

    return q.order_by(models.Lobby.created_at.asc()).first()


def join_lobby(db, user_id, lobby_id):
    existing = db.query(models.LobbyPlayer).filter_by(user_id=user_id, lobby_id=lobby_id).first()
    if existing:
        return existing
    slot = db.query(models.LobbyPlayer).filter_by(lobby_id=lobby_id).count()
    player = models.LobbyPlayer(user_id=user_id, lobby_id=lobby_id, slot=slot)
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def get_lobby(db, game_id):
    return db.query(models.Lobby).filter_by(game_id=game_id).first()
