from django.db import models
from accounts.models import User


class Quiz(models.Model):

    title = models.CharField(max_length=255)

    description = models.TextField(
        blank=True
    )

    quiz_code = models.CharField(
        max_length=20,
        unique=True
    )

    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="quizzes"
    )

    total_time_minutes = models.PositiveIntegerField()

    question_time_seconds = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    use_question_timer = models.BooleanField(
        default=False
    )

    allow_previous_question = models.BooleanField(
        default=True
    )

    show_realtime_leaderboard = models.BooleanField(
        default=False
    )

    show_result_after_finish = models.BooleanField(
        default=True
    )

    join_deadline = models.DateTimeField()

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title

class Question(models.Model):

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    question_text = models.TextField()

    order = models.PositiveIntegerField()

    marks = models.PositiveIntegerField(
        default=1
    )

    def __str__(self):
        return self.question_text
    
class Option(models.Model):

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options"
    )

    option_text = models.CharField(
        max_length=255
    )

    is_correct = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.option_text
class QuizAttempt(models.Model):

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="attempts"
    )

    started_at = models.DateTimeField(
        auto_now_add=True
    )

    finished_at = models.DateTimeField(
        null=True,
        blank=True
    )

    score = models.PositiveIntegerField(
        default=0
    )

    completed = models.BooleanField(
        default=False
    )

    class Meta:

        unique_together = (
            "quiz",
            "user"
        )
class Answer(models.Model):

    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers"
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )

    selected_option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE
    )

    is_correct = models.BooleanField(
        default=False
    )
    class Meta:

        unique_together = (
        "attempt",
        "question"
    )
