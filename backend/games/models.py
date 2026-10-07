from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class Game(models.Model):
    REQUIRED_PLAYERS = 3

    class Status(models.TextChoices):
        WAITING = "waiting", "Waiting"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Game #{self.pk} ({self.status})"

    def get_current_round(self):
        return self.rounds.order_by("-number").first()

    def is_active(self):
        return self.status == self.Status.ACTIVE

    def is_completed(self):
        return self.status == self.Status.COMPLETED

    @transaction.atomic
    def add_player(self, user, color):
        player = Player(game=self, user=user, color=color)
        player.full_clean()
        player.save()
        return player

    def start(self):
        if self.status != self.Status.WAITING:
            raise ValidationError("Only a waiting game can be started.")
        if self.players.count() != self.REQUIRED_PLAYERS:
            raise ValidationError(
                "A game needs exactly %(count)d players to start.",
                params={"count": self.REQUIRED_PLAYERS},
            )
        self.status = self.Status.ACTIVE
        self.save(update_fields=["status"])

    def complete(self):
        if self.status != self.Status.ACTIVE:
            raise ValidationError("Only an active game can be completed.")
        self.status = self.Status.COMPLETED
        self.save(update_fields=["status"])

    @transaction.atomic
    def create_round(self, round_type):
        if not self.is_active():
            raise ValidationError("Rounds can be created only in an active game.")

        current = self.get_current_round()
        if current is not None and current.status != Round.Status.COMPLETED:
            raise ValidationError("The current round must be completed first.")

        next_number = current.number + 1 if current else 1
        round_ = Round(game=self, number=next_number, type=round_type)
        round_.full_clean()
        round_.save()
        return round_


class Player(models.Model):
    class Color(models.TextChoices):
        RED = "red", "Red"
        GREEN = "green", "Green"
        BLUE = "blue", "Blue"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="players",
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="players",
    )
    score = models.IntegerField(default=0)
    color = models.CharField(max_length=10, choices=Color.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "game"],
                name="unique_user_per_game",
                violation_error_message="This user already plays in this game.",
            ),
            models.UniqueConstraint(
                fields=["game", "color"],
                name="unique_color_per_game",
                violation_error_message="This color is already taken in this game.",
            ),
            models.CheckConstraint(
                condition=models.Q(score__gte=0),
                name="player_score_gte_0",
                violation_error_message="Score cannot be negative.",
            ),
        ]

    def __str__(self):
        return f"{self.user} ({self.color}) in game #{self.game_id}"

    def clean(self):
        super().clean()
        if self.pk or not self.game_id:
            return

        # Joining rules apply only to new players.
        if self.game.status != Game.Status.WAITING:
            raise ValidationError("Players can join only a waiting game.")
        if self.game.players.count() >= Game.REQUIRED_PLAYERS:
            raise ValidationError(
                "A game cannot have more than %(count)d players.",
                params={"count": Game.REQUIRED_PLAYERS},
            )


class Round(models.Model):
    class Type(models.TextChoices):
        CITY_CAPTURE = "city_capture", "City capture"
        BATTLE = "battle", "Battle"
        CAPITAL_ATTACK = "capital_attack", "Capital attack"
        BONUS = "bonus", "Bonus"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="rounds",
    )
    number = models.PositiveIntegerField()
    type = models.CharField(max_length=20, choices=Type.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    winner = models.ForeignKey(
        Player,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="won_rounds",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["game", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["game", "number"],
                name="unique_round_number_per_game",
                violation_error_message="This round number already exists in the game.",
            ),
            models.UniqueConstraint(
                fields=["game"],
                condition=models.Q(status="active"),
                name="one_active_round_per_game",
                violation_error_message="The game already has an active round.",
            ),
            models.CheckConstraint(
                condition=~models.Q(status="completed") | models.Q(completed_at__isnull=False),
                name="completed_round_has_completed_at",
                violation_error_message="A completed round must have a completion time.",
            ),
        ]

    def __str__(self):
        return f"Round {self.number} ({self.type}) of game #{self.game_id}"

    def clean(self):
        super().clean()
        if self.winner_id and self.game_id and self.winner.game_id != self.game_id:
            raise ValidationError({"winner": "The winner must be a player in this game."})

    def start(self):
        if self.status != self.Status.PENDING:
            raise ValidationError("Only a pending round can be started.")
        if not self.game.is_active():
            raise ValidationError("Rounds can be played only in an active game.")
        self.status = self.Status.ACTIVE
        self.full_clean()
        self.save(update_fields=["status"])

    def complete(self, winner):
        if self.status != self.Status.ACTIVE:
            raise ValidationError("Only an active round can be completed.")
        self.winner = winner
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.full_clean()
        self.save(update_fields=["winner", "status", "completed_at"])
