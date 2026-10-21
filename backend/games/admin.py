from django.contrib import admin
from django.db.models import Count

from .models import Game, Player, Round, WaitingRoomEntry


class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0
    max_num = Game.REQUIRED_PLAYERS


class RoundInline(admin.TabularInline):
    model = Round
    extra = 0
    fields = ("number", "type", "status", "winner", "completed_at")


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "status", "player_count")
    list_filter = ("status",)
    inlines = [PlayerInline, RoundInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(player_count=Count("players"))

    @admin.display(description="Players", ordering="player_count")
    def player_count(self, obj):
        return obj.player_count


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("user", "game", "color", "score")
    list_filter = ("game", "color")
    search_fields = ("user__username",)
    list_select_related = ("user", "game")


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ("game", "number", "type", "status", "winner", "created_at", "completed_at")
    list_filter = ("game", "type", "status")
    list_select_related = ("game", "winner__user")


@admin.register(WaitingRoomEntry)
class WaitingRoomEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__username",)
    list_select_related = ("user",)
