from fastapi import APIRouter, WebSocket, Depends
from app.core import database, auth
from sqlalchemy.orm import Session
import app.services.websocket as ws_handler

router = APIRouter()


@router.websocket("/ws/{lobby_id}")
async def websocket_endpoint(websocket: WebSocket, lobby_id: str, db: Session = Depends(database.get_db)):
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    # try:
    #     user = auth.get_current_user(token, db)
    # except Exception:
    #     await websocket.close(code=1008)
    #     return

    try:
        user = auth.get_current_user(token, db)
    except Exception as e:
        print("Token decode failed:", e)
        await websocket.close(code=1008)
        return

    await ws_handler.handle_ws(websocket, user.id, lobby_id, db)
