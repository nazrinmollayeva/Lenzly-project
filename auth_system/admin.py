#auth_system/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerification

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ['id', 'username', 'email', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email']
    ordering = ['id']
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'is_email_verified')}),
    )

@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'created_at']

