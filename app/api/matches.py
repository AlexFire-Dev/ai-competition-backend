from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas, models
from app.core import database, auth


router = APIRouter()


@router.get(
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
