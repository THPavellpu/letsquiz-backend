from rest_framework import serializers
from .models import Quiz, Question, Option


class QuizSerializer(serializers.ModelSerializer):
    # Make join_deadline optional for quiz creation.
    # Frontend may send "join_deadline": null.
    join_deadline = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )

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

    def validate(self, attrs):
        # Keep existing manual quiz-creation validation:
        # For a given question, exactly one option must be marked correct.
        # This is required by the existing test suite.
        question = attrs.get("question")
        is_correct = attrs.get("is_correct")

        if question is None or is_correct is None:
            return attrs

        # Count existing correct options for this question.
        # If updating an existing option (id provided), exclude it.
        queryset = Option.objects.filter(question=question, is_correct=True)
        option_id = getattr(self.instance, "id", None)
        if option_id is not None:
            queryset = queryset.exclude(id=option_id)

        correct_count_existing = queryset.count()

        # If this option is correct, it would become the first correct
        # option. Therefore it must not already be one.
        if is_correct is True:
            if correct_count_existing != 0:
                raise serializers.ValidationError(
                    "Exactly one correct option must be selected for the question."
                )
        else:
            # If this option is incorrect, there must remain exactly one correct
            # option after creation.
            # That means there must already be exactly one correct option.
            if correct_count_existing != 1:
                raise serializers.ValidationError(
                    "Exactly one correct option must be selected for the question."
                )

        return attrs




class OptionPublicSerializer(serializers.ModelSerializer):

    class Meta:

        model = Option

        fields = [
            "id",
            "option_text"
        ]


class QuestionPublicSerializer(serializers.ModelSerializer):

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


class QuizDetailSerializer(serializers.ModelSerializer):

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
            "use_quiz_timer",
            "use_question_timer",
            "allow_previous_question",
            "show_realtime_leaderboard",
            "show_result_after_finish",
            "questions"
        ]


class JoinQuizSerializer(serializers.Serializer):

    quiz_code = serializers.CharField()


class SubmitAnswerSerializer(serializers.Serializer):

    attempt_id = serializers.IntegerField()

    question_id = serializers.IntegerField()

    option_id = serializers.IntegerField()


class FinishQuizSerializer(serializers.Serializer):

    attempt_id = serializers.IntegerField()


class LeaderboardEntrySerializer(serializers.Serializer):

    rank = serializers.IntegerField()

    username = serializers.CharField()

    score = serializers.IntegerField()


class CurrentQuestionSerializer(serializers.ModelSerializer):

    options = OptionPublicSerializer(
        many=True,
        read_only=True
    )

    time_elapsed_seconds = serializers.SerializerMethodField()

    time_remaining_seconds = serializers.SerializerMethodField()

    class Meta:

        model = Question

        fields = [
            "id",
            "question_text",
            "order",
            "marks",
            "time_limit_seconds",
            "options",
            "time_elapsed_seconds",
            "time_remaining_seconds"
        ]

    def get_time_elapsed_seconds(self, obj):

        from django.utils import timezone

        attempt = self.context.get('attempt')

        if not attempt or not attempt.current_question_started_at:
            return 0

        elapsed = timezone.now() - attempt.current_question_started_at

        return int(elapsed.total_seconds())

    def get_time_remaining_seconds(self, obj):

        time_elapsed = self.get_time_elapsed_seconds(obj)

        time_remaining = obj.time_limit_seconds - time_elapsed

        return max(0, time_remaining)


class SkipQuestionSerializer(serializers.Serializer):

    attempt_id = serializers.IntegerField()


class QuestionOptionCreateSerializer(serializers.Serializer):

    option_text = serializers.CharField()

    is_correct = serializers.BooleanField()


class QuestionWithOptionsCreateSerializer(serializers.Serializer):

    quiz = serializers.IntegerField()

    question_text = serializers.CharField()

    order = serializers.IntegerField()

    marks = serializers.IntegerField()

    time_limit_seconds = serializers.IntegerField(
        required=False,
        default=30
    )

    # Support both formats:
    # AI format: options as list of strings + correct_answer as index
    # Manual format: options as list of dicts with option_text/is_correct
    options = serializers.ListField(
        child=serializers.JSONField(),
        required=False
    )
    correct_answer = serializers.IntegerField(
        min_value=0,
        max_value=3,
        required=False
    )

    def validate(self, attrs):
        options = attrs.get("options")
        correct_answer = attrs.get("correct_answer")

        if not options:
            return attrs

        if not isinstance(options, list):
            raise serializers.ValidationError({
                "options": ["Invalid options format."]
            })

        if len(options) != 4:
            raise serializers.ValidationError({
                "options": ["Exactly 4 options are required."]
            })

        first_option = options[0]

        # Normalize into manual format: [{"option_text": ..., "is_correct": ...}, ...]
        if isinstance(first_option, str):
            if correct_answer is None:
                raise serializers.ValidationError({
                    "correct_answer": ["correct_answer is required when options are strings."]
                })

            normalized_options = []
            for idx, opt_text in enumerate(options):
                normalized_options.append({
                    "option_text": opt_text,
                    "is_correct": (idx == correct_answer),
                })
            attrs["options"] = normalized_options
            attrs.pop("correct_answer", None)
        else:
            attrs["options"] = options

        normalized_options = attrs["options"]

        # Validate no blank option text + uniqueness (case-insensitive)
        option_texts = []
        option_texts_normalized = []
        for i, opt in enumerate(normalized_options):
            opt_text = opt.get("option_text")
            if opt_text is None:
                raise serializers.ValidationError({
                    "options": ["Option texts cannot be blank."]
                })

            opt_text = str(opt_text).strip()
            if opt_text == "":
                raise serializers.ValidationError({
                    "options": ["Option texts cannot be blank."]
                })

            option_texts.append(opt_text)
            option_texts_normalized.append(opt_text.lower())
            normalized_options[i]["option_text"] = opt_text

        if len(set(option_texts_normalized)) != 4:
            raise serializers.ValidationError({
                "options": ["Duplicate options are not allowed."]
            })

        # Exactly one option marked correct
        correct_options_count = sum(
            1 for option in normalized_options
            if option.get("is_correct") is True
        )
        if correct_options_count != 1:
            raise serializers.ValidationError({
                "options": ["Exactly one correct option must be selected."]
            })

        attrs["options"] = normalized_options
        return attrs





class NextQuestionResponseSerializer(serializers.Serializer):

    message = serializers.CharField()

    has_next_question = serializers.BooleanField()

    question = CurrentQuestionSerializer(required=False)

    total_questions = serializers.IntegerField()


class QuizSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    quiz_code = serializers.CharField()
    created_at = serializers.DateTimeField()
    creator = serializers.CharField()
    total_questions = serializers.IntegerField()
    total_marks = serializers.IntegerField()
    average_marks_per_question = serializers.FloatField()


class CreatorDashboardSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    quiz_code = serializers.CharField()
    created_at = serializers.DateTimeField()
    total_questions = serializers.IntegerField()
    total_participants = serializers.IntegerField()
    completed_participants = serializers.IntegerField()
    highest_score = serializers.IntegerField()
    average_score = serializers.FloatField()


class MyPerformanceSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    quiz_title = serializers.CharField()
    score = serializers.IntegerField()
    percentage = serializers.FloatField()
    completed = serializers.BooleanField()
    started_at = serializers.DateTimeField()
    finished_at = serializers.DateTimeField(allow_null=True)


class LeaderboardParticipantSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    username = serializers.CharField()
    score = serializers.IntegerField()


class CreatorLeaderboardsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    quiz_code = serializers.CharField()
    top_participants = LeaderboardParticipantSerializer(many=True)


class AIQuizRequestSerializer(serializers.Serializer):
    topic = serializers.CharField()
    number_of_questions = serializers.IntegerField(min_value=1)
    difficulty = serializers.CharField()



