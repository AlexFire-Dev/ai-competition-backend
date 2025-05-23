from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any
from datetime import datetime


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


class MatchResultOut(BaseModel):
    id: int
    lobby_id: int
    winner_id: Optional[int]
    loser_id: Optional[int]
    result: str  # "win" or "draw"
    ticks: int

    winner_elo_change: int
    loser_elo_change : int

    class Config:
        orm_mode = True


class ReplayAction(BaseModel):
    tick      : int
    player_id : int
    action    : str
    params    : dict | None


class ReplayOut(BaseModel):
    id           : int
    match_id     : int
    created_at   : datetime
    game_params  : dict[str, Any]
    initial_map  : dict[str, Any]
    actions      : List[ReplayAction]

    class Config:
        orm_mode = True
