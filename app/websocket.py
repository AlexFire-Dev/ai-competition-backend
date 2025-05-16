from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict
import asyncio
from bomberman.GameTools import Game, Action
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.crud import store_match_result

connections = {}                           # user_id -> WebSocket
lobby_connections = defaultdict(set)      # lobby_id -> set of user_ids
game_instances = {}                        # lobby_id -> Game
lobby_actions = defaultdict(dict)          # lobby_id -> { user_id: Action }
player_maps = {}                           # lobby_id -> { user_id: internal_id }
reverse_player_maps = {}                   # lobby_id -> { internal_id: user_id }


async def handle_ws(websocket: WebSocket, user_id: int, lobby_id: str):
    # 1. Принимаем WebSocket
    await websocket.accept()
    print(f"[CONNECTED] User {user_id} connected to lobby {lobby_id}")

    # 2. Регистрируем подключение
    connections[user_id] = websocket
    lobby_connections[lobby_id].add(user_id)
    print(f"[LOBBY STATE] Lobby {lobby_id} WS connections: {lobby_connections[lobby_id]}")

    # 3. Считаем, сколько игроков ожидается в лобби
    db: Session = SessionLocal()
    expected_players = db.query(models.LobbyPlayer) \
                         .filter(models.LobbyPlayer.lobby_id == int(lobby_id)) \
                         .count()
    print(f"[EXPECTED] Lobby {lobby_id} expects {expected_players} players (from DB)")

    # 4. Ждём, пока все нужные игроки не подключатся по WS
    print(f"[LOBBY WAIT] {len(lobby_connections[lobby_id])}/{expected_players} connected, waiting…")
    while len(lobby_connections[lobby_id]) < expected_players:
        await asyncio.sleep(0.5)

    # 5. Создаём игру и маппинг пользователей на internal_id (один раз)
    if lobby_id not in game_instances:
        uids = list(lobby_connections[lobby_id])
        # internal ids: 0..n-1
        player_map = {uid: idx for idx, uid in enumerate(uids)}
        reverse_map = {idx: uid for uid, idx in player_map.items()}
        player_maps[lobby_id] = player_map
        reverse_player_maps[lobby_id] = reverse_map

        print(f"[INIT] Creating game for lobby {lobby_id} with players {player_map}")
        game = Game(width=13, height=11, num_players=expected_players)
        game.lobby_id = lobby_id
        game_instances[lobby_id] = game

        # Оповестим клиентов, что игра стартовала
        for uid in uids:
            ws = connections.get(uid)
            if ws:
                await ws.send_json({"event": "start_game"})
        print(f"[GAME] Lobby {lobby_id} → game started")

        # ——————————————
        # Рассылаем начальное состояние поля
        state = game.export_state()
        print(f"[INIT STATE] broadcasting initial game state")
        for uid in uids:
            ws = connections.get(uid)
            if ws:
                await ws.send_json(state)
        # ——————————————

    game = game_instances[lobby_id]

    try:
        while True:
            # 6. Принимаем ход от клиента
            data = await websocket.receive_json()
            print(f"[RECEIVED] From {user_id}: {data}")
            action_type = data.get("action")
            if action_type not in Action.__members__:
                print(f"[ERROR] Invalid action '{action_type}' from user {user_id}")
                continue

            # 7. Сохраняем действие по user_id
            lobby_actions[lobby_id][user_id] = Action[action_type]
            print(f"[ACTION] Collected {len(lobby_actions[lobby_id])}/{expected_players} actions")

            # 8. Ждём, пока все не пошлют ход
            if len(lobby_actions[lobby_id]) < expected_players:
                continue

            # 9. Все действия собраны — обрабатываем тик
            print(f"[TICK] Processing tick #{game.tick_count + 1}")
            for uid, action in lobby_actions[lobby_id].items():
                internal_id = player_maps[lobby_id][uid]
                game.set_player_action(internal_id, action)
            lobby_actions[lobby_id].clear()

            game.update()

            # 10. Лог визуализации
            print("[BOARD]")
            game.print_board()

            # 11. Экспорт и рассылка состояния всем
            state = game.export_state()
            print(f"[STATE] Tick {state['tick']}: broadcasting")
            for uid in lobby_connections[lobby_id]:
                ws = connections.get(uid)
                if ws:
                    await ws.send_json(state)

            # 12. Проверяем окончание игры
            winner_internal = game.get_winner()
            if winner_internal != -1:
                result = "draw" if winner_internal is None else "win"
                winner_user_id = None if result == "draw" else reverse_player_maps[lobby_id][winner_internal]
                print(f"[GAME OVER] Lobby {lobby_id} result={result}, winner={winner_user_id}")
                store_match_result(db, lobby_id, winner_user_id, result, game.tick_count)

                # уведомляем и закрываем все соединения
                for uid in list(lobby_connections[lobby_id]):
                    ws = connections.pop(uid, None)
                    if ws:
                        await ws.send_json({"event": "game_over", "winner": winner_user_id})
                        await ws.close()
                        print(f"[CLOSED] User {uid} disconnected after game over")

                # очистка
                del game_instances[lobby_id]
                del lobby_connections[lobby_id]
                del player_maps[lobby_id]
                del reverse_player_maps[lobby_id]
                break

    except WebSocketDisconnect:
        print(f"[DISCONNECT] User {user_id} disconnected from lobby {lobby_id}")
        lobby_connections[lobby_id].discard(user_id)
        connections.pop(user_id, None)
        # если в лобби никого не осталось — удаляем всё
        if not lobby_connections[lobby_id]:
            print(f"[CLEANUP] Lobby {lobby_id} empty — deleting game instance")
            del lobby_connections[lobby_id]
            game_instances.pop(lobby_id, None)
            lobby_actions.pop(lobby_id, None)
            player_maps.pop(lobby_id, None)
            reverse_player_maps.pop(lobby_id, None)

    finally:
        db.close()
