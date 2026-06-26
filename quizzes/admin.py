from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    Quiz,
    Question,
    Option,
    QuizAttempt,
    Answer
)


admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Option)
admin.site.register(QuizAttempt)
admin.site.register(Answer)