from django.shortcuts import render

import random

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .serializers import QuizSerializer
from .models import Quiz, Question, Option, QuizAttempt,Answer
from .serializers import (
    QuizSerializer,
    QuestionSerializer,
    OptionSerializer,
    QuizDetailSerializer,
    JoinQuizSerializer,
    SubmitAnswerSerializer,
    FinishQuizSerializer,
    LeaderboardEntrySerializer
)
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import RetrieveAPIView

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import RefreshToken

class QuizCreateView(
    generics.CreateAPIView
):

    serializer_class = QuizSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def perform_create(
        self,
        serializer
    ):

        quiz_code = f"QZ{random.randint(100000, 999999)}"

        serializer.save(
            creator=self.request.user,
            quiz_code=quiz_code
        )
class QuestionCreateView(
    generics.CreateAPIView
):

    serializer_class = QuestionSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def perform_create(
        self,
        serializer
    ):

        quiz = serializer.validated_data["quiz"]

        if quiz.creator != self.request.user:

            raise PermissionDenied(
                "Only quiz creator can add questions."
            )

        serializer.save()

class OptionCreateView(
    generics.CreateAPIView
):

    serializer_class = OptionSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def perform_create(
        self,
        serializer
    ):

        question = serializer.validated_data[
            "question"
        ]

        if (
            question.quiz.creator
            != self.request.user
        ):

            raise PermissionDenied(
                "Only quiz creator can add options."
            )

        serializer.save()
class QuizByCodeView(
    generics.RetrieveAPIView
):

    serializer_class = QuizDetailSerializer

    lookup_field = "quiz_code"

    queryset = Quiz.objects.all()


class JoinQuizView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        serializer = JoinQuizSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        quiz_code = serializer.validated_data[
            "quiz_code"
        ]

        try:

            quiz = Quiz.objects.get(
                quiz_code=quiz_code
            )

        except Quiz.DoesNotExist:

            return Response(
                {
                    "error": "Quiz not found"
                },
                status=404
            )

        if timezone.now() > quiz.join_deadline:

            return Response(
                {
                    "error": "Joining deadline passed"
                },
                status=400
            )

        if QuizAttempt.objects.filter(
            quiz=quiz,
            user=request.user
        ).exists():

            return Response(
                {
                    "error":
                    "You already joined this quiz"
                },
                status=400
            )

        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=request.user
        )

        return Response({

            "message":
            "Quiz joined successfully",

            "attempt_id":
            attempt.id

        })
class SubmitAnswerView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        serializer = SubmitAnswerSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        attempt_id = serializer.validated_data[
            "attempt_id"
        ]

        question_id = serializer.validated_data[
            "question_id"
        ]

        option_id = serializer.validated_data[
            "option_id"
        ]

        try:

            attempt = QuizAttempt.objects.get(
                id=attempt_id,
                user=request.user
            )

        except QuizAttempt.DoesNotExist:

            return Response(
                {
                    "error": "Attempt not found"
                },
                status=404
            )

        if attempt.completed:

            return Response(
                {
                    "error": "Quiz already finished"
                },
                status=400
            )

        quiz = attempt.quiz

        allowed_until = (
            attempt.started_at +
            timedelta(
                minutes=quiz.total_time_minutes
            )
        )

        if timezone.now() > allowed_until:

            total_score = 0

            answers = Answer.objects.filter(
                attempt=attempt,
                is_correct=True
            )

            for answer in answers:
                total_score += answer.question.marks

            attempt.score = total_score
            attempt.completed = True
            attempt.finished_at = timezone.now()
            attempt.save()

            return Response(
                {
                    "error":
                    "Quiz auto-submitted due to timeout",
                    "score": total_score
                },
                status=400
            )

        try:

            question = Question.objects.get(
                id=question_id
            )

        except Question.DoesNotExist:

            return Response(
                {
                    "error": "Question not found"
                },
                status=404
            )

        try:

            option = Option.objects.get(
                id=option_id,
                question=question
            )

        except Option.DoesNotExist:

            return Response(
                {
                    "error":
                    "Option does not belong to this question"
                },
                status=404
            )

        answer, created = (
            Answer.objects.update_or_create(

                attempt=attempt,

                question=question,

                defaults={
                    "selected_option": option,
                    "is_correct": option.is_correct
                }
            )
        )
        channel_layer = get_channel_layer()

        async_to_sync(
            channel_layer.group_send
        )(
            f"leaderboard_{quiz.id}",
            {
                "type":
                "leaderboard_update",

                "message":
                f"{request.user.username} submitted an answer"
            }
        )
        score = Answer.objects.filter(
            attempt=attempt,
            is_correct=True
        ).count()

        return Response({

            "message": "Answer saved",

            "is_correct": option.is_correct,

            "current_score": score

        })


class FinishQuizView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        serializer = FinishQuizSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        attempt_id = serializer.validated_data[
            "attempt_id"
        ]

        try:

            attempt = QuizAttempt.objects.get(
                id=attempt_id,
                user=request.user
            )
            if attempt.completed:

                return Response(
        {
            "error":
            "Quiz already finished"
        },
        status=400
    )

        except QuizAttempt.DoesNotExist:

            return Response(
                {
                    "error": "Attempt not found"
                },
                status=404
            )

        total_score = 0

        answers = Answer.objects.filter(
            attempt=attempt,
            is_correct=True
        )

        for answer in answers:

            total_score += (
                answer.question.marks
            )

        attempt.score = total_score

        attempt.completed = True

        attempt.finished_at = (
            timezone.now()
        )

        attempt.save()

        return Response({

            "message":
            "Quiz finished",

            "score":
            total_score

        })
class LeaderboardView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request, quiz_id):

        try:

            quiz = Quiz.objects.get(
                id=quiz_id
            )
            if (
    not quiz.show_realtime_leaderboard
    and quiz.creator != request.user
):

                attempt = QuizAttempt.objects.filter(
        quiz=quiz,
        user=request.user
    ).first()

            if not attempt or not attempt.completed:

                return Response(
            {
                "error":
                "Leaderboard is hidden during the quiz"
            },
            status=403
        )

        except Quiz.DoesNotExist:

            return Response(
                {
                    "error": "Quiz not found"
                },
                status=404
            )

        attempts = QuizAttempt.objects.filter(
            quiz=quiz
        )

        leaderboard = []

        for attempt in attempts:

            score = 0

            answers = Answer.objects.filter(
                attempt=attempt,
                is_correct=True
            )

            for answer in answers:

                score += answer.question.marks

            leaderboard.append({

    "username":
    attempt.user.username,

    "score":
    score,

    "finished_at":
    attempt.finished_at

})

        leaderboard.sort(
    key=lambda x: (
        -x["score"],
        x["finished_at"]
        if x["finished_at"]
        else datetime.max
    )
)

        ranked_data = []

        for index, entry in enumerate(
            leaderboard,
            start=1
        ):

            ranked_data.append({

                "rank": index,

                "username":
                entry["username"],

                "score":
                entry["score"]

            })

        return Response(
            ranked_data
        )
class QuizDashboardView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request, quiz_id):

        try:

            quiz = Quiz.objects.get(
                id=quiz_id
            )

        except Quiz.DoesNotExist:

            return Response(
                {
                    "error": "Quiz not found"
                },
                status=404
            )

        if quiz.creator != request.user:

            return Response(
                {
                    "error":
                    "Only quiz creator can view dashboard"
                },
                status=403
            )

        attempts = QuizAttempt.objects.filter(
            quiz=quiz
        )

        total_participants = attempts.count()

        completed_participants = attempts.filter(
            completed=True
        ).count()

        highest_score = 0

        if attempts.exists():

            highest_attempt = attempts.order_by(
                "-score"
            ).first()

            highest_score = (
                highest_attempt.score
            )

        average_score = 0

        if attempts.exists():

            total_score = sum(
                attempt.score
                for attempt in attempts
            )

            average_score = (
                total_score /
                total_participants
            )

        return Response({

            "quiz_title":
            quiz.title,

            "total_participants":
            total_participants,

            "completed_participants":
            completed_participants,

            "highest_score":
            highest_score,

            "average_score":
            round(
                average_score,
                2
            )

        })
class AttemptStatusView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        attempt_id
    ):

        try:

            attempt = QuizAttempt.objects.get(
                id=attempt_id,
                user=request.user
            )

        except QuizAttempt.DoesNotExist:

            return Response(
                {
                    "error":
                    "Attempt not found"
                },
                status=404
            )

        allowed_until = (

            attempt.started_at +

            timedelta(
                minutes=
                attempt.quiz.total_time_minutes
            )
        )

        remaining = (

            allowed_until -

            timezone.now()

        ).total_seconds()

        if remaining <= 0:
          if not attempt.completed:

            total_score = 0

            answers = Answer.objects.filter(
                attempt=attempt,
                is_correct=True
            )

            for answer in answers:
                total_score += answer.question.marks

            attempt.score = total_score
            attempt.completed = True
            attempt.finished_at = timezone.now()
            attempt.save()

            remaining = 0

        return Response({

            "remaining_seconds":
            int(remaining),

            "expired":
            remaining == 0,

            "completed":
            attempt.completed

        })
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        try:
            refresh_token = request.data["refresh"]

            token = RefreshToken(refresh_token)

            token.blacklist()

            return Response(
                {"message": "Logged out successfully"},
                status=status.HTTP_205_RESET_CONTENT
            )

        except Exception:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )