from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import HelpRequest, InviteFriend


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = (
        'email', 'first_name', 'last_name', 'phone', 'is_staff'
    )
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),  # keeps email and password fields
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone', 'gender', 'date_of_birth')
        }),  # updated personal info to reflect current fields
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'first_name', 'last_name', 'phone', 'password1', 'password2'
            ),
        }),
    )


@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ('get_user_name', 'get_user_email', 'status', 'created_at')
    search_fields = ('user__first_name', 'user__surname', 'user__email', 'status')
    list_filter = ('status', 'created_at')

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.surname}"
    get_user_name.short_description = 'User Name'

    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'User Email'


@admin.register(InviteFriend)
class InviteFriendAdmin(admin.ModelAdmin):
    list_display = ('friend_name', 'friend_email', 'invited_by', 'date_invited', 'invitation_status')
    search_fields = ('friend_name', 'friend_email', 'invited_by__email')
    list_filter = ('invitation_status', 'date_invited')
