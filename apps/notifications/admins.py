# notifications/admin.py
from django.contrib import admin
from .models import Notification, UserOTP, FacialVerificationLog
from django import forms  # Added missing import

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('user__username', 'message')

# Custom admin for the UserOTP model
@admin.register(UserOTP)
class UserOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'created_at', 'is_valid')
    search_fields = ('user__email', 'otp')
    ordering = ('-created_at',)

# Custom admin for the FacialVerificationLog model
@admin.register(FacialVerificationLog)
class FacialVerificationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'verification_status', 'get_user_email')
    search_fields = ('user__email', 'verification_status')
    ordering = ('-timestamp',)

    @admin.display(description='User Email')
    def get_user_email(self, obj):
        # Display the email of the user or "N/A" if the user does not exist
        return obj.user.email if obj.user else "N/A"

    def save_model(self, request, obj, form, change):
        # Assuming Wallet has a user field pointing to the User model
        user = getattr(obj, 'user', None)
        if user:
            profile = getattr(user, 'profile', None)
            if profile and hasattr(profile, 'deposit_to_wallet'):
                amount = form.cleaned_data.get('amount', 0)
                if amount > 0:
                    profile.deposit_to_wallet(amount)
        
        super().save_model(request, obj, form, change)

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter OTP',
            'class': 'form-control',
            'autocomplete': 'off'
        }),
        error_messages={
            'required': 'OTP is required.',
            'max_length': 'OTP must be exactly 6 digits.',
            'min_length': 'OTP must be exactly 6 digits.'
        },
        label="One-Time Password (OTP)"
    )

    def clean_otp(self):
        otp = self.cleaned_data.get('otp')

        # Validate that the OTP consists only of digits
        if not otp.isdigit():
            raise forms.ValidationError("OTP must contain only numeric characters.")

        # Optionally, add custom logic for additional checks
        # e.g., checking OTP against a database or OTP service
        return otp
