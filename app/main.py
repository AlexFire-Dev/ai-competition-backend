from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import uvicorn

from . import crud, models, schemas, auth, database

app = FastAPI()


@app.post("/register", response_model=schemas.User)
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


@app.get("/users/me", response_model=schemas.User)
def get_me(current_user: schemas.User = Depends(auth.get_current_user)):
    """Endpoint to get details of the currently authenticated user."""

    return current_user


@app.put("/update_profile", response_model=schemas.User)
def update_profile(user_update: schemas.User, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_user = crud.get_user_by_email(db, email=current_user.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Only allow updating username, theme, and avatar
    db_user.username = user_update.username
    db_user.theme = user_update.theme
    db_user.avatar = user_update.avatar
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
