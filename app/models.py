from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class Lobby(Base):
    __tablename__ = "lobbies"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, unique=True, index=True)
    host_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="waiting")  # waiting, started, finished

    players = relationship("LobbyPlayer", back_populates="lobby")


class LobbyPlayer(Base):
    __tablename__ = "lobby_players"

    id = Column(Integer, primary_key=True)
    lobby_id = Column(Integer, ForeignKey("lobbies.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    slot = Column(Integer)

    lobby = relationship("Lobby", back_populates="players")


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True)
    lobby_id = Column(Integer, ForeignKey("lobbies.id"))
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    loser_id  = Column(Integer, ForeignKey("users.id"), nullable=True)
    result = Column(String)  # win, draw
    ticks = Column(Integer)

    winner_elo_change = Column(Integer, nullable=False, default=0)
    loser_elo_change  = Column(Integer, nullable=False, default=0)

    lobby = relationship("Lobby")
    winner = relationship("User",  foreign_keys=[winner_id])
    loser = relationship("User", foreign_keys=[loser_id])

    replay = relationship("Replay", uselist=False, back_populates="match")


class Replay(Base):
    __tablename__ = "replays"

    id            = Column(Integer, primary_key=True, index=True)
    match_id      = Column(Integer, ForeignKey("match_results.id"), unique=True, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow, nullable=False)
    game_params   = Column(JSONB, nullable=False)
    initial_map   = Column(JSONB, nullable=False)
    actions       = Column(JSONB, nullable=False)

    match         = relationship("MatchResult", back_populates="replay")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    username = Column(String, unique=True, index=True)
    theme = Column(String, default="light")  # Тема интерфейса (light/dark)
    avatar = Column(String, nullable=True)  # URL аватара

    # rating params
    rating = Column(Integer, default=1500, nullable=False)
    games_played = Column(Integer, default=0, nullable=False)
