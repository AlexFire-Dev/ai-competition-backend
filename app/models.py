from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

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
    result = Column(String)  # win, draw
    ticks = Column(Integer)

    lobby = relationship("Lobby")
    winner = relationship("User")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    username = Column(String, unique=True, index=True)
    theme = Column(String, default="light")  # Тема интерфейса (light/dark)
    avatar = Column(String, nullable=True)  # URL аватара
