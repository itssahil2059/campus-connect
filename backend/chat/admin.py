from django.contrib import admin

from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("user_a", "user_b", "updated_at")
    search_fields = ("user_a__username", "user_b__username")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "created_at", "read_at")
    raw_id_fields = ("conversation", "sender")
