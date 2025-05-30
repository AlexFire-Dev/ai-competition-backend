from datetime import datetime, timedelta
from celery import shared_task
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app import models


LOBBY_TIMEOUT_MINUTES = 5


@shared_task(name="app.tasks.expire_old_lobbies")
def expire_old_lobbies():
    """
    Меняет статус всех waiting-лобби старше LOBBY_TIMEOUT_MINUTES на finished.
    """
    db: Session = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=LOBBY_TIMEOUT_MINUTES)
        updated = (
            db.query(models.Lobby)
              .filter(
                  models.Lobby.status == models.LobbyStatus.waiting,
                  models.Lobby.created_at < cutoff
              )
              .update(
                  {models.Lobby.status: models.LobbyStatus.finished},
                  synchronize_session=False
              )
        )
        db.commit()
        if updated:
            print(f"[Celery] Expired {updated} lobbies older than {LOBBY_TIMEOUT_MINUTES}m")
    finally:
        db.close()
