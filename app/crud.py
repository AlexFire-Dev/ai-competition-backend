from sqlalchemy.orm import Session
from . import models, schemas, auth
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if user is None:
        return False
    if not auth.verify_password(password, user.hashed_password):
        return False
    return user


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        theme=user.theme,
        avatar=user.avatar,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_lobby(db, game_id, host_id):
    lobby = models.Lobby(game_id=game_id, host_id=host_id)
    db.add(lobby)
    db.commit()
    db.refresh(lobby)
    return lobby


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


def store_match_result(db, lobby_id, winner_id, result, ticks):
    match = models.MatchResult(
        lobby_id=lobby_id,
        winner_id=winner_id,
        result=result,
        ticks=ticks
    )
    db.add(match)
    db.commit()
