from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    confirm_password = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        password_validation.validate_password(new_password)
        return new_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password != confirm_password:
            raise ValidationError("The new passwords do not match.")
        
        return cleaned_data


class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        max_length=6,  # Assuming OTP is a 6-digit code
        label="Enter OTP",
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter OTP', 'class': 'form-control'})
    )
