from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .serializers_ai import AIQuizRequestSerializer
from .ai_quiz import generate_ai_quiz


class GenerateAIQuizView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AIQuizRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            questions = generate_ai_quiz(
                topic=serializer.validated_data["topic"],
                number_of_questions=serializer.validated_data[
                    "number_of_questions"
                ],
                difficulty=serializer.validated_data["difficulty"],
            )

            return Response({"questions": questions}, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {"detail": "Failed to generate quiz."},
                status=status.HTTP_400_BAD_REQUEST,
            )


