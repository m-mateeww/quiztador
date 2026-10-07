from django.core.exceptions import ValidationError
from django.test import TestCase

from games.models import Game, Round

from .factories import create_active_game, create_game_with_players


class GameTests(TestCase):
    def test_create_game(self):
        game = Game.objects.create()

        self.assertEqual(game.status, Game.Status.WAITING)
        self.assertIsNotNone(game.created_at)
        self.assertFalse(game.is_active())
        self.assertFalse(game.is_completed())

    def test_start_game_with_three_players(self):
        game, _ = create_game_with_players(3)

        game.start()

        game.refresh_from_db()
        self.assertEqual(game.status, Game.Status.ACTIVE)
        self.assertTrue(game.is_active())

    def test_start_requires_exactly_three_players(self):
        game, _ = create_game_with_players(2)

        with self.assertRaises(ValidationError):
            game.start()
        game.refresh_from_db()
        self.assertEqual(game.status, Game.Status.WAITING)

    def test_active_game_cannot_be_started_again(self):
        game, _ = create_active_game()

        with self.assertRaises(ValidationError):
            game.start()

    def test_complete_game(self):
        game, _ = create_active_game()

        game.complete()

        game.refresh_from_db()
        self.assertTrue(game.is_completed())

    def test_waiting_game_cannot_be_completed(self):
        game = Game.objects.create()

        with self.assertRaises(ValidationError):
            game.complete()

    def test_completed_game_rejects_new_rounds(self):
        game, _ = create_active_game()
        game.complete()

        with self.assertRaises(ValidationError):
            game.create_round(Round.Type.BATTLE)
        self.assertFalse(game.rounds.exists())

    def test_waiting_game_rejects_rounds(self):
        game, _ = create_game_with_players(3)

        with self.assertRaises(ValidationError):
            game.create_round(Round.Type.CITY_CAPTURE)
