from pydantic import BaseModel, EmailStr
from typing import List, Optional


# class UserBase(BaseModel):
#     email: str
#     username: str
#
#
# class UserCreate(UserBase):
#     password: str
#     theme: str = "light"
#     avatar: str = None
#
#
# class User(UserBase):
#     id: int
#     theme: str
#     avatar: str
#
#     class Config:
#         from_attributes = True


class UserBase(BaseModel):
    email: EmailStr
    username: str
    theme: Optional[str] = None
    avatar: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email:    Optional[EmailStr] = None
    username: Optional[str]      = None
    theme:    Optional[str]      = None
    avatar:   Optional[str]      = None

    class Config:
        orm_mode = True


class UserOut(UserBase):
    id: int
    rating:       int
    games_played: int

    class Config:
        orm_mode = True


class LobbyCreate(BaseModel):
    game_id: str
    host_id: int


class LobbyOut(BaseModel):
    id: int
    game_id: str
    host_id: int
    status: str
    players: List[int]  # stays the same

    class Config:
        from_attributes = True  # <- replaces orm_mode in Pydantic v2

