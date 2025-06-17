from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas, models
from app.core import database, auth
from typing import List


router = APIRouter()


@router.get("/users/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    """Endpoint to get details of the currently authenticated user."""

    return current_user


@router.put("/update_profile", response_model=schemas.UserOut)
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


@router.put("/change_password")
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


@router.get("/users/top", response_model=List[schemas.UserOut])
def get_top_rating(limit: int = 20, db: Session = Depends(database.get_db)):
    """Return top users by rating."""
    return crud.get_top_users(db, limit=limit)
