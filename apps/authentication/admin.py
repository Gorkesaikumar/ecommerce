from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('mobile_number', 'email', 'name', 'role', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('mobile_number', 'email', 'name')
    ordering = ('-date_joined',)

