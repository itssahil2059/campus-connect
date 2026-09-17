from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Doubles as the moderation console: review is_edu_verified /
    is_id_verified here for the MVP instead of building a custom UI.
    """
    list_display = ('username', 'school_email', 'college_name', 'is_edu_verified', 'is_id_verified', 'is_staff')
    list_filter = ('is_edu_verified', 'is_id_verified', 'college_name')
    fieldsets = UserAdmin.fieldsets + (
        ('Campus Connect', {
            'fields': ('school_email', 'college_name', 'graduation_year', 'is_edu_verified', 'is_id_verified'),
        }),
    )
