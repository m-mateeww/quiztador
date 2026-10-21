from rest_framework import status
from rest_framework.exceptions import APIException, NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .waiting_room import WaitingRoomError, form_game, join_waiting_room, leave_waiting_room


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicts with the current state."
    default_code = "conflict"


class JoinWaitingRoomView(APIView):
    def post(self, request):
        try:
            join_waiting_room(request.user)
        except WaitingRoomError as exc:
            raise Conflict(str(exc))

        # Matchmaking is triggered by every successful join.
        game = form_game()
        if game is not None and game.players.filter(user=request.user).exists():
            return Response(
                {"status": "matched", "game": game.pk}, status=status.HTTP_201_CREATED
            )
        return Response({"status": "waiting"}, status=status.HTTP_201_CREATED)


class LeaveWaitingRoomView(APIView):
    def post(self, request):
        if not leave_waiting_room(request.user):
            raise NotFound("You are not in the waiting room.")
        return Response(status=status.HTTP_204_NO_CONTENT)
