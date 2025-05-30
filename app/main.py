from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, users, lobbies, matches, replays, files, websocket


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, tags=["auth"])
app.include_router(users.router, tags=["users"])
app.include_router(lobbies.router, tags=["lobbies"])
app.include_router(matches.router, tags=["matches"])
app.include_router(replays.router, tags=["replays"])
app.include_router(files.router, tags=["files"])

app.include_router(websocket.router, tags=["websocket"])
