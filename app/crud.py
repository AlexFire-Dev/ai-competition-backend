from sqlalchemy import or_
from sqlalchemy.orm import Session
from . import models, schemas, auth
from passlib.context import CryptContext
from math import pow


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


def update_elo(db: Session, winner_id: int, loser_id: int, is_draw: bool = False):
    winner = db.query(models.User).filter(models.User.id == winner_id).one()
    loser  = db.query(models.User).filter(models.User.id == loser_id).one()

    R_w, R_l = winner.rating, loser.rating

    E_w = 1 / (1 + pow(10, (R_l - R_w) / 400))
    E_l = 1 / (1 + pow(10, (R_w - R_l) / 400))

    if is_draw:
        S_w = S_l = 0.5
    else:
        S_w, S_l = 1.0, 0.0

    def choose_K(games):
        if games < 30: return 40
        if games < 300: return 20
        return 10

    K_w = choose_K(winner.games_played)
    K_l = choose_K(loser.games_played)

    winner.rating = round(R_w + K_w * (S_w - E_w))
    loser.rating  = round(R_l + K_l * (S_l - E_l))

    winner.games_played += 1
    loser.games_played  += 1

    db.commit()
    return winner.rating, loser.rating

#
# def store_match_result(db, lobby_id, winner_id, result, ticks):
#     match = models.MatchResult(
#         lobby_id=lobby_id,
#         winner_id=winner_id,
#         result=result,
#         ticks=ticks
#     )
#     db.add(match)
#     db.commit()


def store_match_result(
    db: Session,
    lobby_id: int,
    winner_id: int | None,
    loser_id:  int | None,
    result:    str,
    ticks:     int
):
    """
    Сохраняет результат матча в БД, включая победителя и проигравшего.
    """
    winner = db.query(models.User).filter(models.User.id == winner_id).one()
    loser  = db.query(models.User).filter(models.User.id == loser_id).one()

    pre_win = winner.rating
    pre_los = loser.rating

    update_elo(db, winner_id, loser_id, True if (result == "draw") else False)

    db.refresh(winner)
    db.refresh(loser)

    elo_win_change = winner.rating - pre_win
    elo_los_change = loser.rating - pre_los

    match = models.MatchResult(
        lobby_id  = lobby_id,
        winner_id = winner_id,
        loser_id  = loser_id,
        result    = "win" if elo_win_change > 0 else "draw",
        ticks     = ticks,
        winner_elo_change = elo_win_change,
        loser_elo_change  = elo_los_change,
    )
    db.add(match)
    db.commit()
    db.refresh(match)

    return match


def get_matches_by_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 10
):
    """
    Возвращает все матчи, в которых участвовал пользователь.
    """
    return (
        db.query(models.MatchResult)
          .filter(
              or_(
                  models.MatchResult.winner_id  == user_id,
                  models.MatchResult.loser_id   == user_id
              )
          )
          .order_by(models.MatchResult.id.desc())
          .offset(skip)
          .limit(limit)
          .all()
    )
