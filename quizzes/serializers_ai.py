from rest_framework import serializers


class AIQuizRequestSerializer(serializers.Serializer):
    topic = serializers.CharField()
    number_of_questions = serializers.IntegerField(min_value=1)
    difficulty = serializers.CharField()

