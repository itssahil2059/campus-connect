from django.contrib import admin

from .models import Answer, Profile, Question


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "updated_at")
    search_fields = ("user__username", "user__school_email")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("order", "text")
    ordering = ("order",)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "choice")
    list_filter = ("question",)
