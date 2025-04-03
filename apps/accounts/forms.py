from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model

User = get_user_model()

# Sign Up Form
class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="First Name")
    surname = forms.CharField(max_length=30, required=True, label="Surname")
    gender = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')], required=True, label="Gender")
    registration_number = forms.CharField(max_length=30, required=True, label="Registration Number")
    school = forms.CharField(max_length=100, required=True, label="School")
    department = forms.CharField(max_length=100, required=True, label="Department")
    email = forms.EmailField(required=True, label="Email")
    phone = forms.CharField(max_length=15, required=True, label="Mobile Number")

    class Meta:
        model = User
        fields = ['first_name', 'surname', 'username', 'gender', 'registration_number', 'school', 'department', 'email', 'phone', 'password1', 'password2']

# Login Form
class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254, widget=forms.TextInput(attrs={'autofocus': True, 'placeholder': 'Enter Username'}), label="Username")
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Enter Password'}), label="Password")

# Password Reset Form
class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={'autocomplete': 'email'}))

# Set Password Form
class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label="New password", widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    new_password2 = forms.CharField(label="New password confirmation", widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

# Help Request Form
class HelpRequestForm(forms.Form):
    subject = forms.CharField(max_length=100, required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)

# Invite Friend Form
class InviteFriendForm(forms.Form):
    friend_email = forms.EmailField(required=True)