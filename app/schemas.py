from pydantic import BaseModel
from typing import List, Optional


class UserBase(BaseModel):
    email: str
    username: str


class UserCreate(UserBase):
    password: str
    theme: str = "light"
    avatar: str = None


class User(UserBase):
    id: int
    theme: str
    avatar: str

    class Config:
        from_attributes = True


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

