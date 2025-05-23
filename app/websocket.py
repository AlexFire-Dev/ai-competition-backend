import os
import json
import asyncio
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect, Depends
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from bomberman.GameTools import Game, Action
from app.database import SessionLocal
from app import models, database
from app.crud import store_match_result, store_replay

# Redis client (adjust host/port via environment or here)
redis_client = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# In-memory mappings
connections = {}                           # user_id -> WebSocket
lobby_connections = defaultdict(set)      # lobby_id -> set of user_ids
game_instances = {}                        # lobby_id -> Game
lobby_actions = defaultdict(dict)          # lobby_id -> { user_id: Action }
player_maps = {}                           # lobby_id -> { user_id: internal_id }
reverse_player_maps = {}                   # lobby_id -> { internal_id: user_id }
replay_data = {}


async def handle_ws(websocket: WebSocket, user_id: int, lobby_id: str, db: Session):
    # 1) Accept the WebSocket connection
    await websocket.accept()
    print(f"[CONNECTED] User {user_id} connected to lobby {lobby_id}")

    # 2) Register the connection
    connections[user_id] = websocket
    lobby_connections[lobby_id].add(user_id)
    print(f"[LOBBY STATE] Lobby {lobby_id}: {lobby_connections[lobby_id]}")

    # 3) Determine how many players should join (from DB)
    # db: Session = SessionLocal()
    expected_players = (
        db.query(models.LobbyPlayer)
          .filter(models.LobbyPlayer.lobby_id == int(lobby_id))
          .count()
    )
    print(f"[EXPECTED] Lobby {lobby_id} expects {expected_players} players")

    # 4) Wait until all expected players connect via WS
    print(f"[LOBBY WAIT] {len(lobby_connections[lobby_id])}/{expected_players} connected, waiting…")
    while len(lobby_connections[lobby_id]) < expected_players:
        await asyncio.sleep(0.5)

    # 5) Initialize the game and mappings once
    if lobby_id not in game_instances:
        uids = list(lobby_connections[lobby_id])
        player_map = {uid: idx for idx, uid in enumerate(uids)}
        reverse_map = {idx: uid for uid, idx in player_map.items()}
        player_maps[lobby_id] = player_map
        reverse_player_maps[lobby_id] = reverse_map

        print(f"[INIT] Creating game {lobby_id} for players {player_map}")
        game = Game(width=13, height=11, num_players=expected_players)
        game.lobby_id = lobby_id
        game_instances[lobby_id] = game

        # Сохраняем параметры игры
        replay_data[lobby_id] = {
            "game_params": {
                "width": 13,
                "height": 11,
            },
            "initial_map": game.export_state(),
            "actions": []
        }

        # 5a) Notify clients that the game is starting
        for uid in uids:
            ws = connections.get(uid)
            if ws:
                await ws.send_json({"event": "start_game"})
                await ws.send_json({
                    "event": "start_game",
                    "user_id": uid
                })
        print(f"[GAME] Lobby {lobby_id} → start_game sent to {len(uids)} clients")

        # 5b) Broadcast the initial game state
        init = game.export_state()
        players_int = init.pop("players")
        remapped = {}
        for internal, info in players_int.items():
            uid = reverse_player_maps[lobby_id][int(internal)]
            remapped[str(uid)] = info
        init["players"] = remapped

        for uid in uids:
            ws = connections.get(uid)
            if ws:
                await ws.send_json({"event": "init_state", **init})
        print(f"[INIT STATE] {init['tick']}")

        # 5c) Store initial state in Redis
        await redis_client.set(f"game:{lobby_id}:state", json.dumps(init))
        print(f"[REDIS] Initial state stored for lobby {lobby_id}")
    else:
        # 5x) Reconnection handling
        if user_id in player_maps[lobby_id]:
            print(f"[RECONNECT] User {user_id} rejoined lobby {lobby_id}")
            # send "start_game" again to re-sync
            await websocket.send_json({
                "event": "start_game",
                "user_id": user_id
            })
            # load last known game state from Redis
            saved = await redis_client.get(f"game:{lobby_id}:state")
            if saved:
                state = json.loads(saved)
                await websocket.send_json({"event": "reconnect_state", **state})

    game = game_instances[lobby_id]

    try:
        while True:
            # 6) Receive action from a client
            data = await websocket.receive_json()
            action_type = data.get("action")
            print(f"[RECEIVED] From {user_id}: {action_type}")

            if action_type not in Action.__members__:
                print(f"[ERROR] Invalid action '{action_type}' from user {user_id}")
                continue

            # 7) Store the action
            lobby_actions[lobby_id][user_id] = Action[action_type]
            replay_data[lobby_id]["actions"].append({
                "tick": game.tick_count,
                "player_int_id": player_maps[lobby_id][user_id],
                "action": action_type,
                **{k: v for k, v in data.items() if k != "action"}
            })
            print(f"[ACTION] Collected {len(lobby_actions[lobby_id])}/{expected_players} actions")

            # 8) Wait until all players have sent their action
            if len(lobby_actions[lobby_id]) < expected_players:
                continue

            # 9) Process the tick
            print(f"[TICK] Processing tick #{game.tick_count + 1}")
            for uid, action in lobby_actions[lobby_id].items():
                internal_id = player_maps[lobby_id][uid]
                game.set_player_action(internal_id, action)
            lobby_actions[lobby_id].clear()

            game.update()

            # 10) Log the board for debugging
            print("[BOARD]")
            game.print_board(id_map=reverse_player_maps[lobby_id])

            # 11) Export, broadcast, and save state
            st = game.export_state()
            # remap players → user_ids
            pi = st.pop("players")
            mp = {}
            for internal, info in pi.items():
                mp[str(reverse_player_maps[lobby_id][int(internal)])] = info
            st["players"] = mp

            # save and broadcast
            await redis_client.set(f"game:{lobby_id}:state", json.dumps(st))
            for uid in lobby_connections[lobby_id]:
                ws = connections.get(uid)
                if ws:
                    await ws.send_json(st)

            # 12) Check for game over
            winner_internal = game.get_winner()
            if winner_internal != -1:
                result = "draw" if winner_internal is None else "win"

                winner_user_id = reverse_player_maps[lobby_id][winner_internal]
                loser_user_id = next(
                    uid for internal, uid in reverse_player_maps[lobby_id].items()
                    if internal != winner_internal
                )

                print(f"[GAME OVER] Lobby {lobby_id} result={result}, winner={winner_user_id}")
                match = store_match_result(
                    db,
                    lobby_id=int(lobby_id),
                    winner_id=winner_user_id,
                    loser_id=loser_user_id,
                    result=result,  # "win" | "draw"
                    ticks=game.tick_count
                )

                rd = replay_data[lobby_id]
                store_replay(
                    db,
                    match.id,
                    rd["game_params"],
                    rd["initial_map"],
                    rd["actions"]
                )

                # Remove state from Redis
                await redis_client.delete(f"game:{lobby_id}:state")
                print(f"[REDIS] Deleted state for lobby {lobby_id}")

                # Notify clients and close connections
                for uid in list(lobby_connections[lobby_id]):
                    ws = connections.pop(uid, None)
                    if ws:
                        await ws.send_json({"event": "game_over", "winner": winner_user_id})
                        await ws.close()
                        print(f"[CLOSED] User {uid} disconnected after game over")

                # Cleanup
                del game_instances[lobby_id]
                del lobby_connections[lobby_id]
                del player_maps[lobby_id]
                del reverse_player_maps[lobby_id]
                del replay_data[lobby_id]
                break

    except WebSocketDisconnect:
        print(f"[DISCONNECT] User {user_id} left lobby {lobby_id}")
        lobby_connections[lobby_id].discard(user_id)
        connections.pop(user_id, None)

        # If lobby empty, clean up all data
        if not lobby_connections[lobby_id]:
            await redis_client.delete(f"game:{lobby_id}:state")
            print(f"[REDIS] Cleaned state for empty lobby {lobby_id}")
            game_instances.pop(lobby_id, None)
            lobby_actions.pop(lobby_id, None)
            player_maps.pop(lobby_id, None)
            reverse_player_maps.pop(lobby_id, None)
            replay_data.pop(lobby_id, None)

    finally:
        db.close()
