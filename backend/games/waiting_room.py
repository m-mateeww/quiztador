import random

from django.db import IntegrityError, transaction

from .models import Game, Player, WaitingRoomEntry

# A user who plays in a game with one of these statuses cannot wait or be matched.
BUSY_GAME_STATUSES = [Game.Status.WAITING, Game.Status.ACTIVE]


class WaitingRoomError(Exception):
    pass


class AlreadyWaiting(WaitingRoomError):
    def __init__(self):
        super().__init__("You are already in the waiting room.")


class NotEligible(WaitingRoomError):
    def __init__(self):
        super().__init__("You already play in a game that is not completed.")


def is_eligible(user):
    return not Player.objects.filter(user=user, game__status__in=BUSY_GAME_STATUSES).exists()


def eligible_entries():
    busy_users = Player.objects.filter(game__status__in=BUSY_GAME_STATUSES).values("user_id")
    return WaitingRoomEntry.objects.exclude(user_id__in=busy_users)


def join_waiting_room(user):
    """Adds the user to the waiting room or raises without changing anything."""
    if WaitingRoomEntry.objects.filter(user=user).exists():
        raise AlreadyWaiting()
    if not is_eligible(user):
        raise NotEligible()

    try:
        with transaction.atomic():
            return WaitingRoomEntry.objects.create(user=user)
    except IntegrityError:
        raise AlreadyWaiting() from None


def leave_waiting_room(user):
    """Removes the user's own request. Returns False when the user was not waiting."""
    deleted, _ = WaitingRoomEntry.objects.filter(user=user).delete()
    return deleted > 0


@transaction.atomic
def form_game(rng=random):
    """
    Matches three random eligible waiting users into a new waiting game.

    Returns the game, or None when fewer than three eligible users wait.
    Everything runs in one transaction, so a failure leaves no partial
    game, players or lost requests behind.
    """
    entries = list(eligible_entries().select_for_update().select_related("user"))
    if len(entries) < Game.REQUIRED_PLAYERS:
        return None

    chosen = rng.sample(entries, Game.REQUIRED_PLAYERS)
    colors = rng.sample(list(Player.Color.values), Game.REQUIRED_PLAYERS)

    game = Game.objects.create()
    for entry, color in zip(chosen, colors):
        game.add_player(entry.user, color)

    WaitingRoomEntry.objects.filter(pk__in=[entry.pk for entry in chosen]).delete()
    return game
