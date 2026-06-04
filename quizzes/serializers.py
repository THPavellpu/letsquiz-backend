from rest_framework import serializers
from .models import Quiz, Question, Option


class QuizSerializer(serializers.ModelSerializer):

    class Meta:

        model = Quiz

        fields = "__all__"

        read_only_fields = [
            "creator",
            "quiz_code",
            "created_at",
            "updated_at"
        ]


class QuestionSerializer(serializers.ModelSerializer):

    class Meta:

        model = Question

        fields = "__all__"


class OptionSerializer(serializers.ModelSerializer):

    class Meta:

        model = Option

        fields = "__all__"

class OptionPublicSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = Option

        fields = [
            "id",
            "option_text"
        ]
class QuestionPublicSerializer(
    serializers.ModelSerializer
):

    options = OptionPublicSerializer(
        many=True,
        read_only=True
    )

    class Meta:

        model = Question

        fields = [
            "id",
            "question_text",
            "order",
            "marks",
            "options"
        ]
class QuizDetailSerializer(
    serializers.ModelSerializer
):

    questions = QuestionPublicSerializer(
        many=True,
        read_only=True
    )

    class Meta:

        model = Quiz

        fields = [
            "id",
            "title",
            "description",
            "quiz_code",
            "total_time_minutes",
            "question_time_seconds",
            "use_question_timer",
            "allow_previous_question",
            "show_realtime_leaderboard",
            "show_result_after_finish",
            "questions"
        ]

class JoinQuizSerializer(
    serializers.Serializer
):

    quiz_code = serializers.CharField()
class SubmitAnswerSerializer(
    serializers.Serializer
):

    attempt_id = serializers.IntegerField()

    question_id = serializers.IntegerField()

    option_id = serializers.IntegerField()

class FinishQuizSerializer(
    serializers.Serializer
):

    attempt_id = serializers.IntegerField()

class LeaderboardEntrySerializer(
    serializers.Serializer
):

    rank = serializers.IntegerField()

    username = serializers.CharField()

    score = serializers.IntegerField()