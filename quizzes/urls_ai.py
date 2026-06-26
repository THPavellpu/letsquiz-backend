from django.urls import path

from .views_ai import GenerateAIQuizView


urlpatterns = [
    path(
        "generate-ai/",
        GenerateAIQuizView.as_view(),
        name="generate-ai",
    ),
]

