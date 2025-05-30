from sqlalchemy.orm import Session
from app import models, schemas
from sqlalchemy import or_, func


def update_elo(db: Session, winner_id: int, loser_id: int, is_draw: bool = False):
    winner = db.query(models.User).filter(models.User.id == winner_id).one()
    loser  = db.query(models.User).filter(models.User.id == loser_id).one()

    R_w, R_l = winner.rating, loser.rating

    E_w = 1 / (1 + pow(10, (R_l - R_w) / 400))
    E_l = 1 / (1 + pow(10, (R_w - R_l) / 400))

    if not is_draw:
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
        result    = result,
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
