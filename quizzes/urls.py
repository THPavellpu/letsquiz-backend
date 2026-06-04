from django.urls import path
from .views import AttemptStatusView, LogoutView, QuizByCodeView, QuizCreateView
from .views import (
    QuizCreateView,
    QuestionCreateView,
    OptionCreateView,
    QuizByCodeView,
    JoinQuizView,
    SubmitAnswerView,
    FinishQuizView,
    LeaderboardView,
    QuizDashboardView
)

urlpatterns = [

    path(
        "",
        QuizCreateView.as_view(),
        name="quiz-create"
    ),
    path(
        "questions/",
        QuestionCreateView.as_view(),
        name="question-create"
    ),
    path(
    "options/",
    OptionCreateView.as_view(),
    name="option-create"
    ),
    path(
    "code/<str:quiz_code>/",
    QuizByCodeView.as_view(),
    name="quiz-by-code"
),
    path(
    "code/<str:quiz_code>/",
    QuizByCodeView.as_view(),
    name="quiz-by-code"
),
    path(
    "join/",
    JoinQuizView.as_view(),
    name="join-quiz"
),
    path(
    "submit-answer/",
    SubmitAnswerView.as_view(),
    name="submit-answer"
),
path(
    "finish/",
    FinishQuizView.as_view(),
    name="finish-quiz"
),
path(
    "<int:quiz_id>/leaderboard/",
    LeaderboardView.as_view(),
    name="leaderboard"
),
path(
    "<int:quiz_id>/dashboard/",
    QuizDashboardView.as_view(),
    name="quiz-dashboard"
),
path(
    "attempt/<int:attempt_id>/status/",
    AttemptStatusView.as_view(),
    name="attempt-status"
),
path("logout/", LogoutView.as_view(), name="logout"),
]