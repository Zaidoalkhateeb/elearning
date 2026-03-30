from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
	fieldsets = UserAdmin.fieldsets + (
		('Role & Sessions', {'fields': ('role', 'token_version')}),
	)
	list_display = (*UserAdmin.list_display, 'role', 'token_version')

# Register your models here.
