from GameTools import *

# 1. Create smaller game
game = Game(width=7, height=5, num_players=2)

# Override spawn positions for clarity
game.players[0].x, game.players[0].y = 1, 1
game.players[1].x, game.players[1].y = 5, 3

# Clear the grid manually for predictable output
for y in range(game.height):
    for x in range(game.width):
        game.grid[y][x] = Tile.EMPTY if x not in [0, 6] and y not in [0, 4] else Tile.WALL

game.print_board()

# 2. Turn 1: Players move
game.set_player_action(0, Action.RIGHT)  # Player 0 moves right
game.set_player_action(1, Action.LEFT)   # Player 1 moves left
game.update()
game.print_board()

# 3. Turn 2: Player 0 drops bomb, Player 1 moves again
game.set_player_action(0, Action.BOMB)
game.set_player_action(1, Action.LEFT)
game.update()
game.print_board()

# 4. Turn 3: No actions, bomb timer ticking
game.update()
game.print_board()

# 5. Turn 4: No actions, bomb explodes
game.update()
game.print_board()

# 5. Turn 4: No actions, bomb explodes
game.update()
game.print_board()
print(game.export_state())
