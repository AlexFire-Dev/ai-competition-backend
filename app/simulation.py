from bomberman.GameTools import Game, Action
from collections import defaultdict
from typing import List, Dict, Any


def simulate_replay(
    game_params: Dict[str, Any],
    initial_map: Dict[str, Any],
    actions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """ Возвращает список состояний (кадров) игры """

    width       = game_params["width"]
    height      = game_params["height"]
    radius      = game_params.get("radius")
    num_players = len(initial_map["players"])

    game = Game(width=width, height=height, num_players=num_players)
    game._state = initial_map

    frames = [initial_map]

    ticks: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for a in actions:
        ticks[a["tick"]].append(a)

    for tick in sorted(ticks):
        for a in ticks[tick]:
            pid = a["player_int_id"]
            act = Action[a["action"]]
            game.set_player_action(pid, act)
        game.update()
        frames.append(game.export_state())

    return frames
