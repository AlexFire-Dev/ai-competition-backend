from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from app import models, schemas
from app.core import database, auth


def store_replay(
    db: Session,
    match_id: int,
    game_params: dict,
    initial_map: dict,
    actions: list[dict],
) -> models.Replay:

    replay = models.Replay(
        match_id    = match_id,
        game_params = game_params,
        initial_map = initial_map,
        actions     = actions,
    )
    db.add(replay)
    db.commit()
    db.refresh(replay)

    return replay


def get_replay(db: Session, replay_id: int) -> models.Replay | None:
    return db.query(models.Replay).filter(models.Replay.id == replay_id).first()


def get_replay_by_match_id(db: Session, match_id: int) -> models.Replay | None:
    return (
        db.query(models.Replay)
          .filter(models.Replay.match_id == match_id)
          .first()
    )
