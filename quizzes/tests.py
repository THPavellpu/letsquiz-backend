from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from quizzes.models import Quiz, Question, Option, QuizAttempt, Answer

from rest_framework.test import APIRequestFactory, force_authenticate

from quizzes.views import AttemptResultView


class AttemptResultViewTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="password123",
        )
        self.participant = User.objects.create_user(
            username="participant",
            email="participant@example.com",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="password123",
        )

        self.quiz = Quiz.objects.create(
            title="Sample Quiz",
            description="",
            quiz_code="QUIZCODE1",
            creator=self.creator,
            total_time_minutes=None,
            use_quiz_timer=True,
            use_question_timer=False,
            allow_previous_question=True,
            show_realtime_leaderboard=False,
            show_result_after_finish=True,
            join_deadline=None,
            is_active=True,
        )

        self.q1 = Question.objects.create(
            quiz=self.quiz,
            question_text="Q1?",
            order=1,
            marks=1,
            time_limit_seconds=30,
        )
        self.q2 = Question.objects.create(
            quiz=self.quiz,
            question_text="Q2?",
            order=2,
            marks=1,
            time_limit_seconds=30,
        )

        # Q1 options (option2 correct)
        self.q1o1 = Option.objects.create(question=self.q1, option_text="A", is_correct=False)
        self.q1o2 = Option.objects.create(question=self.q1, option_text="B", is_correct=True)
        self.q1o3 = Option.objects.create(question=self.q1, option_text="C", is_correct=False)
        self.q1o4 = Option.objects.create(question=self.q1, option_text="D", is_correct=False)

        # Q2 options (option3 correct)
        self.q2o1 = Option.objects.create(question=self.q2, option_text="W", is_correct=False)
        self.q2o2 = Option.objects.create(question=self.q2, option_text="X", is_correct=False)
        self.q2o3 = Option.objects.create(question=self.q2, option_text="Y", is_correct=True)
        self.q2o4 = Option.objects.create(question=self.q2, option_text="Z", is_correct=False)

        self.attempt = QuizAttempt.objects.create(
            quiz=self.quiz,
            user=self.participant,
            started_at=timezone.now() - timezone.timedelta(seconds=120),
            finished_at=timezone.now(),
            completed=True,
            current_question_order=2,
            current_question_started_at=None,
        )

        # Participant answers
        Answer.objects.create(
            attempt=self.attempt,
            question=self.q1,
            selected_option=self.q1o2,
            is_correct=True,
        )
        Answer.objects.create(
            attempt=self.attempt,
            question=self.q2,
            selected_option=self.q2o4,
            is_correct=False,
        )

        # Ensure attempt.score matches answers (1 correct)
        self.attempt.score = 1
        self.attempt.save()

        self.other_attempt = QuizAttempt.objects.create(
            quiz=self.quiz,
            user=self.other_user,
            started_at=timezone.now() - timezone.timedelta(seconds=60),
            finished_at=timezone.now(),
            completed=True,
            current_question_order=1,
            current_question_started_at=None,
            score=0,
        )

    def _get(self, user, attempt_id, show_result_after_finish=None):
        if show_result_after_finish is not None:
            self.quiz.show_result_after_finish = show_result_after_finish
            self.quiz.save()

        factory = APIRequestFactory()
        request = factory.get("/api/quizzes/attempt-result/", {})
        force_authenticate(request, user=user)
        response = AttemptResultView.as_view()(request, attempt_id=attempt_id)
        return response

    def test_participant_can_view_own_attempt_detailed(self):
        response = self._get(self.participant, self.attempt.id, show_result_after_finish=True)
        self.assertEqual(response.status_code, 200)

        payload = response.data
        self.assertEqual(payload["quiz_title"], self.quiz.title)
        self.assertEqual(payload["score"], 1)
        self.assertEqual(payload["total_questions"], 2)
        self.assertEqual(payload["percentage"], 50.0)
        self.assertIn("started_at", payload)
        self.assertIn("finished_at", payload)
        self.assertIn("time_taken_seconds", payload)

        self.assertIn("questions", payload)
        self.assertEqual(len(payload["questions"]), 2)

        q1_payload = next(q for q in payload["questions"] if q["question_id"] == self.q1.id)
        self.assertEqual(q1_payload["selected_option_id"], self.q1o2.id)
        self.assertEqual(q1_payload["correct_option_id"], self.q1o2.id)
        self.assertEqual(q1_payload["is_correct"], True)

        q2_payload = next(q for q in payload["questions"] if q["question_id"] == self.q2.id)
        self.assertEqual(q2_payload["selected_option_id"], self.q2o4.id)
        self.assertEqual(q2_payload["correct_option_id"], self.q2o3.id)
        self.assertEqual(q2_payload["is_correct"], False)

    def test_other_user_gets_403_for_attempt_not_owned(self):
        response = self._get(self.other_user, self.attempt.id)
        self.assertEqual(response.status_code, 403)

    def test_quiz_creator_can_view_attempt(self):
        response = self._get(self.creator, self.attempt.id)
        self.assertEqual(response.status_code, 200)

    def test_show_result_after_finish_false_hides_detailed_review(self):
        response = self._get(self.participant, self.attempt.id, show_result_after_finish=False)
        self.assertEqual(response.status_code, 200)

        payload = response.data
        self.assertEqual(payload["quiz_title"], self.quiz.title)
        self.assertEqual(payload["score"], 1)
        self.assertEqual(payload["percentage"], 50.0)
        self.assertEqual(payload["total_questions"], 2)
        self.assertEqual(payload["show_result_after_finish"], False)
        self.assertNotIn("questions", payload)
        self.assertNotIn("started_at", payload)
        self.assertNotIn("finished_at", payload)
        self.assertNotIn("time_taken_seconds", payload)

