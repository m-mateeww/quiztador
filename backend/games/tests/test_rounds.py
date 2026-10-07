from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from games.models import Round

from .factories import create_active_game


class RoundTests(TestCase):
    def setUp(self):
        self.game, self.players = create_active_game()

    def test_create_round(self):
        round_ = self.game.create_round(Round.Type.CITY_CAPTURE)

        self.assertEqual(round_.game, self.game)
        self.assertEqual(round_.number, 1)
        self.assertEqual(round_.type, Round.Type.CITY_CAPTURE)
        self.assertEqual(round_.status, Round.Status.PENDING)
        self.assertIsNone(round_.winner)
        self.assertIsNone(round_.completed_at)

    def test_complete_round(self):
        round_ = self.game.create_round(Round.Type.BATTLE)
        round_.start()

        round_.complete(self.players[1])

        round_.refresh_from_db()
        self.assertEqual(round_.status, Round.Status.COMPLETED)
        self.assertEqual(round_.winner, self.players[1])
        self.assertIsNotNone(round_.completed_at)

    def test_winner_must_belong_to_same_game(self):
        _, other_players = create_active_game(prefix="other")
        round_ = self.game.create_round(Round.Type.BATTLE)
        round_.start()

        with self.assertRaises(ValidationError) as context:
            round_.complete(other_players[0])
        self.assertIn("winner", context.exception.message_dict)

        round_.refresh_from_db()
        self.assertEqual(round_.status, Round.Status.ACTIVE)
        self.assertIsNone(round_.winner)

    def test_get_current_round_returns_highest_number(self):
        Round.objects.create(game=self.game, number=2, type=Round.Type.BATTLE)
        Round.objects.create(game=self.game, number=5, type=Round.Type.BONUS)
        Round.objects.create(game=self.game, number=3, type=Round.Type.CITY_CAPTURE)

        self.assertEqual(self.game.get_current_round().number, 5)

    def test_rounds_are_numbered_sequentially(self):
        first = self.game.create_round(Round.Type.CITY_CAPTURE)
        first.start()
        first.complete(self.players[0])

        second = self.game.create_round(Round.Type.BATTLE)

        self.assertEqual(second.number, 2)
        self.assertEqual(self.game.get_current_round(), second)

    def test_new_round_requires_completed_current_round(self):
        self.game.create_round(Round.Type.CITY_CAPTURE)

        with self.assertRaises(ValidationError):
            self.game.create_round(Round.Type.BATTLE)

    def test_round_number_is_unique_per_game(self):
        Round.objects.create(game=self.game, number=1, type=Round.Type.BATTLE)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Round.objects.create(game=self.game, number=1, type=Round.Type.BONUS)

    def test_only_one_active_round_per_game(self):
        Round.objects.create(game=self.game, number=1, type=Round.Type.BATTLE, status="active")
        second = Round.objects.create(game=self.game, number=2, type=Round.Type.BONUS)

        with self.assertRaises(ValidationError):
            second.start()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Round.objects.filter(pk=second.pk).update(status=Round.Status.ACTIVE)

    def test_completed_round_requires_completed_at(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Round.objects.create(
                game=self.game, number=1, type=Round.Type.BATTLE, status=Round.Status.COMPLETED
            )

    def test_pending_round_cannot_be_completed(self):
        round_ = self.game.create_round(Round.Type.BONUS)

        with self.assertRaises(ValidationError):
            round_.complete(self.players[0])

    def test_invalid_type_is_rejected(self):
        round_ = Round(game=self.game, number=1, type="duel")

        with self.assertRaises(ValidationError):
            round_.full_clean()
