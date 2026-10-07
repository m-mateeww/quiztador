from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from games.models import Game, Player

from .factories import create_active_game, create_game_with_players, create_user


class PlayerTests(TestCase):
    def test_add_three_players(self):
        game, players = create_game_with_players(3)

        self.assertEqual(game.players.count(), 3)
        self.assertEqual(len({player.user_id for player in players}), 3)
        self.assertEqual(
            {player.color for player in players},
            {Player.Color.RED, Player.Color.GREEN, Player.Color.BLUE},
        )
        self.assertTrue(all(player.score == 0 for player in players))

    def test_user_cannot_join_same_game_twice(self):
        game, players = create_game_with_players(1)

        with self.assertRaises(ValidationError):
            game.add_player(players[0].user, Player.Color.BLUE)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Player.objects.create(game=game, user=players[0].user, color=Player.Color.BLUE)

    def test_color_is_unique_per_game(self):
        game, _ = create_game_with_players(1)
        user = create_user("newcomer")

        with self.assertRaises(ValidationError):
            game.add_player(user, Player.Color.RED)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Player.objects.create(game=game, user=user, color=Player.Color.RED)

    def test_same_color_allowed_in_different_games(self):
        first, _ = create_game_with_players(1, prefix="first")
        second, _ = create_game_with_players(1, prefix="second")

        self.assertEqual(
            first.players.get().color, second.players.get().color
        )

    def test_score_cannot_be_negative(self):
        game, players = create_game_with_players(1)
        player = players[0]
        player.score = -1

        with self.assertRaises(ValidationError):
            player.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            player.save()

    def test_game_accepts_at_most_three_players(self):
        game, _ = create_game_with_players(3)

        with self.assertRaises(ValidationError):
            game.add_player(create_user("fourth"), Player.Color.RED)
        self.assertEqual(game.players.count(), 3)

    def test_players_cannot_join_active_game(self):
        game, players = create_active_game()
        players[0].delete()

        with self.assertRaises(ValidationError):
            game.add_player(create_user("late"), Player.Color.RED)

    def test_invalid_color_is_rejected(self):
        game = Game.objects.create()

        with self.assertRaises(ValidationError):
            game.add_player(create_user("purple"), "purple")
