from django.contrib.auth import get_user_model

from games.models import Game, Player

COLORS = [Player.Color.RED, Player.Color.GREEN, Player.Color.BLUE]


def create_user(username):
    return get_user_model().objects.create_user(
        username=username, email=f"{username}@example.com", password="test-pass-123"
    )


def create_game_with_players(count=3, prefix="player"):
    game = Game.objects.create()
    players = [
        game.add_player(create_user(f"{prefix}_{index}"), COLORS[index])
        for index in range(count)
    ]
    return game, players


def create_active_game(prefix="player"):
    game, players = create_game_with_players(prefix=prefix)
    game.start()
    return game, players
