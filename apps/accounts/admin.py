from django.contrib import admin
from .models import HelpRequest, InviteFriend, User


class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'user_email', 'status', 'created_at')  # Ensure these fields exist in HelpRequest
    search_fields = ('user_name', 'user_email', 'status')
    list_filter = ('status', 'created_at')


@admin.register(InviteFriend)
class InviteFriendAdmin(admin.ModelAdmin):
    list_display = ('friend_name', 'friend_email', 'invited_by', 'date_invited', 'invitation_status')  # Updated to match model fields


