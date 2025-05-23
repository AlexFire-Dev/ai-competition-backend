import random
from enum import Enum
from collections import defaultdict


class Tile(Enum):
    EMPTY = 0
    WALL = 1
    DESTRUCTIBLE = 2
    BOMB = 3
    FIRE = 4


class Action(Enum):
    STAY = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    BOMB = 5


class Player:
    def __init__(self, player_id, x, y):
        self.id = player_id
        self.x = x
        self.y = y
        self.alive = True


class Bomb:
    def __init__(self, owner_id, x, y, timer=3, radius=2):
        self.owner_id = owner_id
        self.x = x
        self.y = y
        self.timer = timer
        self.radius = radius


class Game:
    def __init__(self, width, height, num_players):
        self.num_players = num_players

        self.width = width
        self.height = height
        self.grid = [[Tile.EMPTY for _ in range(width)] for _ in range(height)]
        self.players = {}
        self.bombs = []
        self.fire = []
        self.actions = defaultdict(lambda: Action.STAY)
        self.tick_count = 0
        self._place_walls()
        self._spawn_players(num_players)

    def _place_walls(self):
        for y in range(self.height):
            for x in range(self.width):
                if x == 0 or y == 0 or x == self.width-1 or y == self.height-1:
                    self.grid[y][x] = Tile.WALL
                elif (x % 2 == 0 and y % 2 == 0):
                    self.grid[y][x] = Tile.WALL
                elif random.random() < 0.2:
                    self.grid[y][x] = Tile.DESTRUCTIBLE

    def _spawn_players(self, num_players):
        positions = [(1,1), (self.width-2,1), (1,self.height-2), (self.width-2,self.height-2)]
        for i in range(num_players):
            x, y = positions[i]
            self.players[i] = Player(i, x, y)
            self.grid[y][x] = Tile.EMPTY  # ensure spawn area is clear

    def set_player_action(self, player_id, action):
        if player_id in self.players and self.players[player_id].alive:
            self.actions[player_id] = action

    def update(self):
        self.tick_count += 1
        self._move_players()
        self._update_bombs()
        self._clear_fire()
        self.actions = defaultdict(lambda: Action.STAY)  # reset actions

    def _move_players(self):
        for pid, action in self.actions.items():
            player = self.players[pid]
            if not player.alive:
                continue

            dx, dy = 0, 0
            if action == Action.UP: dy = -1
            elif action == Action.DOWN: dy = 1
            elif action == Action.LEFT: dx = -1
            elif action == Action.RIGHT: dx = 1
            elif action == Action.BOMB:
                if self.grid[player.y][player.x] != Tile.BOMB:
                    self.bombs.append(Bomb(pid, player.x, player.y))
                    self.grid[player.y][player.x] = Tile.BOMB
                continue

            nx, ny = player.x + dx, player.y + dy
            if self._is_walkable(nx, ny):
                player.x, player.y = nx, ny

    def _is_walkable(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.grid[y][x] in (Tile.EMPTY, Tile.FIRE)

    def _update_bombs(self):
        for bomb in self.bombs[:]:
            bomb.timer -= 1
            if bomb.timer <= 0:
                self._explode_bomb(bomb)
                self.bombs.remove(bomb)

    def _explode_bomb(self, bomb):
        x, y = bomb.x, bomb.y
        self.grid[y][x] = Tile.FIRE
        self.fire.append((x, y, 2))

        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            for i in range(1, bomb.radius+1):
                nx, ny = x + dx*i, y + dy*i
                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    break
                tile = self.grid[ny][nx]
                if tile == Tile.WALL:
                    break
                if tile == Tile.DESTRUCTIBLE:
                    self.grid[ny][nx] = Tile.FIRE
                    self.fire.append((nx, ny, 2))
                    break
                self.grid[ny][nx] = Tile.FIRE
                self.fire.append((nx, ny, 2))

        # Check for players caught in explosion
        for pid, player in self.players.items():
            if (player.x, player.y) in [(fx, fy) for fx, fy, _ in self.fire]:
                player.alive = False

    def _clear_fire(self):
        new_fire = []
        for x, y, ttl in self.fire:
            if ttl > 1:
                new_fire.append((x, y, ttl-1))
            else:
                if self.grid[y][x] == Tile.FIRE:
                    self.grid[y][x] = Tile.EMPTY
        self.fire = new_fire

    def export_state(self):
        return {
            "tick": self.tick_count,
            "width": self.width,
            "height": self.height,
            "grid": [[tile.name for tile in row] for row in self.grid],
            "players": {
                pid: {
                    "x": player.x,
                    "y": player.y,
                    "alive": player.alive
                } for pid, player in self.players.items()
            },
            "bombs": [
                {
                    "owner_id": bomb.owner_id,
                    "x": bomb.x,
                    "y": bomb.y,
                    "timer": bomb.timer,
                    "radius": bomb.radius
                } for bomb in self.bombs
            ],
            "fire": [
                {
                    "x": x,
                    "y": y,
                    "ttl": ttl
                } for x, y, ttl in self.fire
            ]
        }

    def import_state(self, state: dict):
        self.tick_count = state["tick"]
        self.width      = state["width"]
        self.height     = state["height"]

        self.grid = [
            [Tile[cell_name] for cell_name in row]
            for row in state["grid"]
        ]

        self.players = {}
        for pid_str, pdata in state["players"].items():
            pid = int(pid_str)
            p = Player(pid, pdata["x"], pdata["y"])
            p.alive = pdata["alive"]
            self.players[pid] = p

        self.bombs = []
        for bd in state["bombs"]:
            bomb = Bomb(bd["owner_id"], bd["x"], bd["y"], bd["timer"], bd["radius"])
            self.bombs.append(bomb)
            self.grid[bomb.y][bomb.x] = Tile.BOMB

        self.fire = []
        for fd in state["fire"]:
            x, y, ttl = fd["x"], fd["y"], fd["ttl"]
            self.fire.append((x, y, ttl))
            self.grid[y][x] = Tile.FIRE

        self.actions = defaultdict(lambda: Action.STAY)


    def print_board(self, id_map: dict[int, int] | None = None):
        board = [[self._tile_char(x, y) for x in range(self.width)] for y in range(self.height)]

        for pid, player in self.players.items():
            if player.alive:
                label = str(id_map.get(pid, pid)) if id_map else str(pid)
                board[player.y][player.x] = label

        print(f"\nTick: {self.tick_count}")
        for row in board:
            print("".join(row))

    def _tile_char(self, x, y):
        tile = self.grid[y][x]
        if any((bx == x and by == y) for bx, by, _ in self.fire):
            return '*'
        elif tile == Tile.WALL:
            return '#'
        elif tile == Tile.DESTRUCTIBLE:
            return '+'
        elif tile == Tile.BOMB:
            return 'B'
        elif tile == Tile.EMPTY:
            return '.'
        else:
            return '?'

    def get_winner(self):
        alive_players = [p.id for p in self.players.values() if p.alive]
        if len(alive_players) == 1:
            return alive_players[0]
        elif len(alive_players) == 0:
            return None  # No one wins (draw)
        else:
            return -1  # Game still ongoing
