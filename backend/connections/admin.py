from django.contrib import admin

from .models import Connection


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ("from_user", "to_user", "status", "created_at", "responded_at")
    list_filter = ("status",)
    search_fields = ("from_user__username", "to_user__username")
