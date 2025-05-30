from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app import crud, schemas
from app.core import database, auth
from app.services import simulation


router = APIRouter()


@router.get(
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


@router.get(
    "/replays/{replay_id}/frames",
    summary="Воссоздать и вернуть кадры игры по реплею"
)
def replay_frames(
    replay_id: int,
    db: Session = Depends(database.get_db)
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


@router.get(
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


@router.get(
    "/replays/match/{match_id}/frames",
    summary="Воссоздать и вернуть кадры игры по match_id"
)
def replay_frames_by_match(
    match_id: int,
    db: Session = Depends(database.get_db)
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
