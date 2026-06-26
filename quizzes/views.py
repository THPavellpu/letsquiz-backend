from django.shortcuts import render

import logging
import random
import uuid

logger = logging.getLogger(__name__)

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .serializers import QuizSerializer
from .models import Quiz, Question, Option, QuizAttempt, Answer
from .serializers import (
    QuizSerializer,
    QuestionSerializer,
    OptionSerializer,
    QuizDetailSerializer,
    JoinQuizSerializer,
    SubmitAnswerSerializer,
    FinishQuizSerializer,
    LeaderboardEntrySerializer,
    CurrentQuestionSerializer,
    SkipQuestionSerializer,
    NextQuestionResponseSerializer,
    QuestionWithOptionsCreateSerializer,
    QuizSummarySerializer,
    CreatorDashboardSerializer,
    MyPerformanceSerializer,
    CreatorLeaderboardsSerializer,
)

from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import RetrieveAPIView
from django.db import transaction
from django.db import IntegrityError



from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import RefreshToken

import os
import json
import re
import google.generativeai as genai

from rest_framework import status


class QuizAnalyticsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_id):
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response(
                {"error": "Quiz not found"},
                status=404,
            )

        if quiz.creator != request.user:
            return Response(
                {"error": "Only quiz creator can access analytics."},
                status=403,
            )

        attempts = QuizAttempt.objects.filter(
            quiz=quiz,
            completed=True,
        )

        total_participants = attempts.count()
        completed_participants = attempts.count()

        highest_score = 0
        lowest_score = 0
        average_score = 0

        if attempts.exists():
            highest_score = attempts.order_by("-score").first().score
            lowest_score = attempts.order_by("score").first().score

            total_score = sum(attempt.score for attempt in attempts)
            average_score = round(
                total_score / total_participants,
                2,
            )

        question_analytics = []
        for question in quiz.questions.all():
            correct_count = Answer.objects.filter(
                question=question,
                is_correct=True,
            ).count()

            total_answers = Answer.objects.filter(
                question=question).count()

            wrong_count = total_answers - correct_count

            accuracy = round((correct_count / total_answers) * 100, 2) if total_answers > 0 else 0

            if accuracy > 80:
                difficulty = "Easy"
            elif 50 <= accuracy <= 80:
                difficulty = "Medium"
            else:
                difficulty = "Hard"

            question_analytics.append(
                {
                    "question_id": question.id,
                    "question_text": question.question_text,
                    "correct_count": correct_count,
                    "wrong_count": wrong_count,
                    "accuracy": accuracy,
                    "difficulty": difficulty,
                }
            )

        return Response(
            {
                "quiz_title": quiz.title,
                "total_participants": total_participants,
                "completed_participants": completed_participants,
                "highest_score": highest_score,
                "lowest_score": lowest_score,
                "average_score": average_score,
                "question_analytics": question_analytics,
            }
        )


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

        quiz_code = (
            str(uuid.uuid4())
            .replace("-", "")
            [:8]
            .upper()
        )

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

        if quiz.join_deadline is not None:
            if timezone.now() > quiz.join_deadline:
                return Response(
                    {
                        "detail": "This quiz is no longer accepting participants because the join deadline has passed."
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

        if quiz.use_question_timer:

            if not attempt.current_question_started_at:

                return Response(
                    {
                        "error":
                        "Question timer not started. Call get-current-question first"
                    },
                    status=400
                )

            time_spent = (
                timezone.now() -
                attempt.current_question_started_at
            )

            if (
                time_spent.total_seconds() >
                question.time_limit_seconds
            ):

                return Response(
                    {
                        "error":
                        "Question time limit exceeded",
                        "time_spent_seconds":
                        int(time_spent.total_seconds()),
                        "time_limit_seconds":
                        question.time_limit_seconds
                    },
                    status=400
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

        Answer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={
                "selected_option": option,
                "is_correct": option.is_correct
            },
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

        except Quiz.DoesNotExist:

            return Response(
                {
                    "error": "Quiz not found"
                },
                status=404
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

        attempts = QuizAttempt.objects.filter(
            quiz=quiz,
            completed=True
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

            leaderboard.append(
                {
                    "username":
                    attempt.user.username,

                    "score":
                    score,

                    "finished_at":
                    attempt.finished_at

                }
            )

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

            ranked_data.append(
                {
                    "rank":
                    index,

                    "username":
                    entry["username"],

                    "score":
                    entry["score"]

                }
            )

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
        lowest_score = 0

        if attempts.exists():
            highest_score = attempts.order_by(
                "-score"
            ).first().score

            lowest_score = attempts.order_by(
                "score"
            ).first().score

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
            "lowest_score":
            lowest_score,

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
                minutes=attempt.quiz.total_time_minutes
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

        total_questions = attempt.quiz.questions.count()

        percentage = (
            round(
                (attempt.score / total_questions) * 100,
                2
            )
            if total_questions > 0
            else 0
        )

        return Response({
            "completed": attempt.completed,
            "score": attempt.score,
            "percentage": percentage,
            "started_at": attempt.started_at,
            "finished_at": attempt.finished_at,
            "remaining_seconds": int(remaining),
            "expired": remaining == 0,
            "quiz_id": attempt.quiz.id,
            "total_questions": attempt.quiz.questions.count(),
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


class GetCurrentQuestionView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):

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

        if quiz.total_time_minutes:

            allowed_until = (
                attempt.started_at +
                timedelta(
                    minutes=quiz.total_time_minutes
                )
            )

            if timezone.now() > allowed_until:

                return Response(
                    {
                        "error":
                        "Quiz time limit exceeded"
                    },
                    status=400
                )

        try:

            current_question = (
                quiz.questions.get(
                    order=attempt.current_question_order
                )
            )

        except Question.DoesNotExist:

            return Response(
                {
                    "error": "No more questions"
                },
                status=400
            )

        if (
            quiz.use_question_timer and
            not attempt.current_question_started_at
        ):

            attempt.current_question_started_at = (
                timezone.now()
            )

            attempt.save()

        total_questions = (
            quiz.questions.count()
        )

        serializer = (
            CurrentQuestionSerializer(
                current_question,
                context={'attempt': attempt}
            )
        )

        return Response({

            "current_question_number":
            attempt.current_question_order,

            "total_questions":
            total_questions,

            "question":
            serializer.data,

            "quiz_settings": {
                "use_question_timer":
                quiz.use_question_timer,
                "use_quiz_timer":
                quiz.use_quiz_timer,
                "total_time_minutes":
                quiz.total_time_minutes,
                "allow_previous_question":
                quiz.allow_previous_question
            }

        })


class NextQuestionView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        try:

            attempt_id = request.data.get(
                "attempt_id"
            )

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

        total_questions = (
            quiz.questions.count()
        )

        next_question_order = (
            attempt.current_question_order + 1
        )

        if (
            next_question_order >
            total_questions
        ):

            return Response({

                "message":
                "No more questions",

                "has_next_question":
                False,

                "total_questions":
                total_questions

            })

        attempt.current_question_order = (
            next_question_order
        )

        attempt.current_question_started_at = (
            timezone.now()
        )

        attempt.save()

        try:

            next_question = (
                quiz.questions.get(
                    order=next_question_order
                )
            )

        except Question.DoesNotExist:

            return Response(
                {
                    "error": "Question not found"
                },
                status=404
            )

        serializer = (
            CurrentQuestionSerializer(
                next_question,
                context={'attempt': attempt}
            )
        )

        return Response({

            "message":
            "Moved to next question",

            "has_next_question":
            True,

            "current_question_number":
            next_question_order,

            "total_questions":
            total_questions,

            "question":
            serializer.data

        })


class CreateQuestionWithOptionsView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = QuestionWithOptionsCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        quiz_id = serializer.validated_data["quiz"]

        quiz = Quiz.objects.get(id=quiz_id)

        if quiz.creator != request.user:

            raise PermissionDenied(
                "Only quiz creator can add questions."
            )

        try:
            with transaction.atomic():
                question = Question.objects.create(
                    quiz=quiz,
                    question_text=serializer.validated_data["question_text"],
                    order=serializer.validated_data["order"],
                    marks=serializer.validated_data["marks"],
                    time_limit_seconds=serializer.validated_data.get(
                        "time_limit_seconds",
                        30  # Default matches serializer default
                    ),
                )

                for option_data in serializer.validated_data["options"]:
                    Option.objects.create(
                        question=question,
                        option_text=option_data["option_text"],
                        is_correct=option_data["is_correct"],
                    )
        except IntegrityError as e:
            logger.error(
                "Integrity error creating quiz",
                extra={"error": str(e)},
                exc_info=True
            )

            return Response(
                {
                    "detail": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(

            {
                "message": "Question and options created successfully",
                "question_id": question.id,
            },
            status=status.HTTP_201_CREATED,
        )


class SkipQuestionView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = SkipQuestionSerializer(
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

        if not quiz.use_question_timer:

            return Response(
                {
                    "error":
                    "Cannot skip question when question timer is disabled"
                },
                status=400
            )

        if attempt.current_question_started_at:

            time_spent = (
                timezone.now() -
                attempt.current_question_started_at
            )

            try:

                current_question = (
                    quiz.questions.get(
                        order=attempt.current_question_order
                    )
                )

            except Question.DoesNotExist:

                return Response(
                    {
                        "error":
                        "Question not found"
                    },
                    status=404
                )

            if (
                time_spent.total_seconds() <=
                current_question.time_limit_seconds
            ):

                return Response(
                    {
                        "error":
                        "Cannot skip question before time limit."
                    },
                    status=400
                )

        total_questions = (
            quiz.questions.count()
        )

        next_question_order = (
            attempt.current_question_order + 1
        )

        if (
            next_question_order >
            total_questions
        ):

            return Response({

                "message":
                "Skipped question. No more questions",

                "has_next_question":
                False,

                "total_questions":
                total_questions

            })

        attempt.current_question_order = (
            next_question_order
        )

        attempt.current_question_started_at = (
            timezone.now()
        )

        attempt.save()

        try:

            next_question = (
                quiz.questions.get(
                    order=next_question_order
                )
            )

        except Question.DoesNotExist:

            return Response(
                {
                    "error": "Question not found"
                },
                status=404
            )

        serializer = (
            CurrentQuestionSerializer(
                next_question,
                context={'attempt': attempt}
            )
        )

        return Response({

            "message":
            "Question skipped. Moving to next",

            "has_next_question":
            True,

            "skipped_question_order":
            attempt.current_question_order - 1,

            "current_question_number":
            next_question_order,

            "total_questions":
            total_questions,

            "question":
            serializer.data

        })


class QuizSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_id):
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response(
                {"error": "Quiz not found"},
                status=404,
            )

        total_questions = quiz.questions.count()
        total_marks = sum(question.marks for question in quiz.questions.all())
        average_marks_per_question = (
            round(total_marks / total_questions, 2)
            if total_questions != 0
            else 0
        )

        return Response({
            "id": quiz.id,
            "title": quiz.title,
            "quiz_code": quiz.quiz_code,
            "created_at": quiz.created_at,
            "creator": quiz.creator.username,
            "total_questions": total_questions,
            "total_marks": total_marks,
            "average_marks_per_question": average_marks_per_question,
        })


class CreatorDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        quizzes = Quiz.objects.filter(creator=request.user)

        data = []
        for quiz in quizzes:
            total_questions = quiz.questions.count()

            attempts = QuizAttempt.objects.filter(quiz=quiz)
            total_participants = attempts.count()
            completed_participants = attempts.filter(completed=True).count()

            highest_score = 0
            average_score = 0

            if attempts.exists():
                highest_score = attempts.order_by("-score").first().score

                total_score = sum(attempt.score for attempt in attempts)
                if total_participants > 0:
                    average_score = round(total_score / total_participants, 2)

            data.append(
                {
                    "id": quiz.id,
                    "title": quiz.title,
                    "quiz_code": quiz.quiz_code,
                    "created_at": quiz.created_at,
                    "total_questions": total_questions,
                    "total_participants": total_participants,
                    "completed_participants": completed_participants,
                    "highest_score": highest_score,
                    "average_score": average_score,
                }
            )

        return Response(data)


class MyPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        attempts = QuizAttempt.objects.filter(
            user=request.user
        ).select_related('quiz').order_by('-started_at')

        data = []
        for attempt in attempts:
            total_questions = attempt.quiz.questions.count()

            percentage = (
                round((attempt.score / total_questions) * 100, 2)
                if total_questions > 0
                else 0
            )

            data.append(
                {
                    "attempt_id": attempt.id,
                    "quiz_id": attempt.quiz.id,
                    "quiz_title": attempt.quiz.title,
                    "score": attempt.score,
                    "percentage": percentage,
                    "completed": attempt.completed,
                    "started_at": attempt.started_at,
                    "finished_at": attempt.finished_at,
                }
            )


        return Response(data)


class AttemptResultView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):
        try:
            attempt = (
                QuizAttempt.objects.select_related(
                    "quiz",
                    "user",
                )
                .prefetch_related(
                    "quiz__questions__options",
                )
                .get(id=attempt_id)
            )
        except QuizAttempt.DoesNotExist:
            return Response({"error": "Attempt not found"}, status=403)

        quiz = attempt.quiz

        is_participant = attempt.user_id == request.user.id
        is_creator = quiz.creator_id == request.user.id

        if not (is_participant or is_creator):
            return Response({"error": "Forbidden"}, status=403)

        total_questions = quiz.questions.count()
        score = attempt.score
        percentage = round((score / total_questions) * 100, 2) if total_questions > 0 else 0

        show_result_after_finish = bool(
            getattr(quiz, "show_result_after_finish", True)
        )

        base = {
            "quiz_title": quiz.title,
            "score": score,
            "percentage": percentage,
            "total_questions": total_questions,
        }

        if not show_result_after_finish:
            base["show_result_after_finish"] = False
            return Response(base)

        started_at = attempt.started_at
        finished_at = attempt.finished_at
        time_taken_seconds = (
            int((finished_at - started_at).total_seconds())
            if started_at and finished_at
            else 0
        )

        # Pull all answers for this attempt, keyed by question id.
        answers_qs = (
            Answer.objects.filter(attempt=attempt)
            .select_related("question", "selected_option")
            .prefetch_related("question__options")
        )
        answer_by_question_id = {a.question_id: a for a in answers_qs}

        correct_answers = answers_qs.filter(is_correct=True).count()
        wrong_answers = max(0, total_questions - correct_answers)

        questions_payload = []
        for question in quiz.questions.all():
            answer = answer_by_question_id.get(question.id)

            selected_option_id = (
                answer.selected_option_id if answer else None
            )
            is_correct = bool(answer.is_correct) if answer else False

            correct_option_id = None
            options_payload = []
            for option in question.options.all():
                if option.is_correct:
                    correct_option_id = option.id

                options_payload.append(
                    {
                        "id": option.id,
                        "option_text": option.option_text,
                        "is_correct": option.is_correct,
                    }
                )

            questions_payload.append(
                {
                    "question_id": question.id,
                    "question_text": question.question_text,
                    "marks": question.marks,
                    "selected_option_id": selected_option_id,
                    "correct_option_id": correct_option_id,
                    "is_correct": is_correct,
                    "options": options_payload,
                }
            )

        return Response(
            {
                "quiz_title": quiz.title,
                "score": score,
                "percentage": percentage,
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "wrong_answers": wrong_answers,
                "started_at": started_at,
                "finished_at": finished_at,
                "time_taken_seconds": time_taken_seconds,
                "questions": questions_payload,
            }
        )




class CreatorLeaderboardsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        quizzes = Quiz.objects.filter(
            creator=request.user
        ).prefetch_related('questions')

        data = []
        for quiz in quizzes:
            attempts = QuizAttempt.objects.filter(
                quiz=quiz,
                completed=True
            ).order_by('-score', 'finished_at')

            leaderboard = []
            for index, attempt in enumerate(attempts[:3], start=1):
                leaderboard.append(
                    {
                        "rank": index,
                        "username": attempt.user.username,
                        "score": attempt.score,
                    }
                )

            data.append(
                {
                    "id": quiz.id,
                    "title": quiz.title,
                    "quiz_code": quiz.quiz_code,
                    "top_participants": leaderboard,
                }
            )

        return Response(data)


from .serializers import AIQuizRequestSerializer


class GenerateAIQuizView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AIQuizRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        topic = serializer.validated_data["topic"]
        number_of_questions = serializer.validated_data["number_of_questions"]
        difficulty = serializer.validated_data["difficulty"]

        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return Response(
                    {"detail": "Failed to generate quiz."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")


            prompt = (
                f"Generate exactly {number_of_questions} multiple-choice questions about:\n\n"
                f'"{topic}"\n\n'
                f"Difficulty:\n{difficulty}\n\n"
                "Return ONLY valid JSON."
                "Format:[\n"
                "{\n"
                '"question_text":"...",\n'
                '"options":["Option A","Option B","Option C","Option D"],\n'
                '"correct_answer":2,\n'
                '"difficulty":"medium",\n'
                '"marks":1\n'
                "}\n"
                "]\n\n"
                "Rules:\n"
                "- Exactly four options.\n"
                "- One correct answer.\n"
                "- No explanations.\n"
                "- No markdown.\n"
                "- JSON only.\n"
                "- University level.\n"
                "- Questions must not repeat."
            )

            response = model.generate_content(prompt)
            text = getattr(response, "text", None) or getattr(response, "result", None) or str(response)


            # Remove markdown fences if Gemini returns them.
            text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text.strip())

            data = json.loads(text)

            if not isinstance(data, list):
                raise ValueError("Expected JSON array")

            def _normalize_options(item_options):
                # Supported formats:
                # A) ["A","B","C","D"]
                # B) [{"text":"A"}, ...]
                # C) [{"option_text":"A"}, ...]
                # D) [{"label":"A"}, ...]
                if not isinstance(item_options, list):
                    raise ValueError("options must be a list")

                normalized = []
                for opt in item_options:
                    if isinstance(opt, str):
                        normalized.append(opt)
                    elif isinstance(opt, dict):
                        val = (
                            opt.get("text")
                            if "text" in opt
                            else opt.get("option_text")
                            if "option_text" in opt
                            else opt.get("label")
                            if "label" in opt
                            else None
                        )
                        normalized.append(val)
                    else:
                        normalized.append(None)

                # Clean/validate
                cleaned = []
                for v in normalized:
                    if v is None:
                        cleaned.append("")
                    else:
                        cleaned.append(str(v).strip())

                # Guarantee exactly 4 option strings (no empty strings)
                if len(cleaned) != 4:
                    raise ValueError("Each question must have exactly 4 options")
                if any(not s for s in cleaned):
                    raise ValueError("Options must be non-empty strings")

                return cleaned

            questions = []
            for item in data:
                normalized_options = _normalize_options(item.get("options"))

                correct_answer = item.get("correct_answer")
                if not isinstance(correct_answer, int) or correct_answer not in (0, 1, 2, 3):
                    raise ValueError("correct_answer must be an index from 0 to 3")

                questions.append(
                    {
                        "question_text": item.get("question_text"),
                        "options": normalized_options,
                        "correct_answer": correct_answer,
                        "difficulty": item.get("difficulty"),
                        "marks": item.get("marks", 1),
                    }
                )

            if len(questions) != number_of_questions:
                raise ValueError("Unexpected number of questions")

            return Response({"questions": questions}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(
                "Gemini quiz generation failed",
                extra={"error": str(e)},
                exc_info=True
            )
            return Response(
                {"detail": "Failed to generate quiz."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )





