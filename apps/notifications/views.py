import base64
import random
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views import View
from django.contrib.auth.decorators import login_required
from .models import Notification
from apps.transactions.models import Transaction
from apps.notifications.twilio import send_sms  # Ensure Twilio integration
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import  urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .forms import ChangePasswordForm
import string
from django.core.cache import cache


# Configure logger
logger = logging.getLogger(__name__)

# Initiate Password Reset (Send Reset Link)
class InitiatePasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset_form.html'  # Custom template for the password reset form
    email_template_name = 'accounts/password_reset_email.html'  # Template to send the email
    success_url = reverse_lazy('notifications:password_reset_complete')  # Redirect to this page once the email is sent

    subject_template_name = 'accounts/password_reset_subject.txt'  # Optional custom email subject


# Custom Password Reset View
class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('notifications:password_reset_complete')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Add custom logic after successful form submission
        return response


# Password Reset Complete View
class PasswordResetCompleteView(TemplateView):
    template_name = 'accounts/password_reset_complete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context if necessary
        return context


# Optional: Password Reset Token Verification Helper (for generating or verifying the token)
def verify_reset_token(token, uidb64):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if default_token_generator.check_token(user, token):
            return user
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
    return None


@login_required
def notification_list(request):
    """
    Displays a list of notifications for the logged-in user.
    """
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications/notifications.html', {'notifications': notifications})


@login_required
def mark_as_read(request, id):
    """
    Marks a notification as read for the logged-in user.
    """
    notification = get_object_or_404(Notification, id=id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications:notification_list')


@login_required
def complete_transaction(request, transaction_id):
    """
    Completes a transaction and sends an SMS notification via Twilio.
    """
    transaction = get_object_or_404(Transaction, id=transaction_id)

    if transaction.status == 'success':
        if hasattr(request.user, 'profile') and request.user.profile.phone_number:
            user_phone_number = request.user.profile.phone_number
            message = f"Your transaction of {transaction.amount} was successful. Thank you for using our service!"
            sms_status = send_sms(user_phone_number, message)

            if sms_status:
                Notification.objects.create(
                    user=request.user,
                    message=message,
                    is_read=False
                )
                messages.success(request, "Transaction completed successfully! An SMS has been sent to your phone.")
            else:
                messages.warning(request, "Transaction completed, but SMS could not be sent.")
        else:
            messages.error(request, "Transaction completed, but your profile does not have a valid phone number.")
    else:
        messages.error(request, "Transaction failed. Please try again.")

    return redirect('transactions:transaction_history')


# Helper methods for OTP generation and encoding
def generate_otp():
    """Generate a 6-digit OTP."""
    return random.randint(100000, 999999)


def encode(data):
    """Encode data using base64."""
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')


def decode(encoded_data):
    """Decode base64 encoded data."""
    try:
        return base64.b64decode(encoded_data).decode('utf-8')
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to decode data: {e}")
        return None


@login_required
def gencode(request):
    """
    Generate a unique encoded string and return it.
    """
    if request.method == 'GET':
        otp = generate_otp()
        encoded_otp = encode(str(otp))
        return JsonResponse({'success': True, 'encoded_code': encoded_otp, 'message': 'Code generated successfully.'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
def send_sms_view(request):
    """Send SMS using integrated SMS service (e.g., Twilio)."""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        message = request.POST.get('message')

        if not phone_number or not message:
            return JsonResponse({'success': False, 'error': 'Phone number and message are required.'})

        try:
            sms_status = send_sms(phone_number, message)
            if sms_status:
                logger.info(f"SMS sent to {phone_number} with message: {message}")
                return JsonResponse({'success': True, 'message': 'SMS sent successfully.'})
            else:
                return JsonResponse({'success': False, 'error': 'Failed to send SMS. Please try again.'})
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {e}")
            return JsonResponse({'success': False, 'error': 'An error occurred while sending SMS.'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
def send_otp(request):
    """Send OTP to the user's phone number."""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        if not phone_number:
            return JsonResponse({'success': False, 'error': 'Phone number is required.'})

        otp = generate_otp()
        try:
            send_sms(phone_number, f"Your OTP is {otp}")
            logger.info(f"OTP sent to {phone_number}: {otp}")
            return JsonResponse({'success': True, 'otp': otp})
        except Exception as e:
            logger.error(f"Failed to send OTP to {phone_number}: {e}")
            return JsonResponse({'success': False, 'error': 'Failed to send OTP. Please try again.'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
def verify_otp(request):
    """Verify the OTP sent to the user."""
    if request.method == 'POST':
        otp = request.POST.get('otp')
        if otp == "123456":  # Example OTP for testing purposes
            return JsonResponse({'success': True, 'message': 'OTP verified successfully.'})
        return JsonResponse({'success': False, 'error': 'Invalid OTP.'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


class SendMailView(View):
    def post(self, request, *args, **kwargs):
        """Send email notifications."""
        # Implement email logic here
        return JsonResponse({'success': True, 'message': 'Mail sent successfully.'})


class DecodeUIDView(View):
    def get(self, request, *args, **kwargs):
        """Decode UID logic."""
        # Implement UID decoding here
        return JsonResponse({'success': True, 'message': 'UID decoded successfully.'})


@login_required
def update_profile(request):
    """View for updating the user's profile."""
    if request.method == 'POST':
        # Add form handling and saving logic here
        messages.success(request, "Profile updated successfully.")
        return redirect('notifications:notification_list')
    return render(request, 'notifications/update_profile.html')


@login_required
def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            current_password = form.cleaned_data['current_password']
            new_password = form.cleaned_data['new_password']
            confirm_password = form.cleaned_data['confirm_password']

            if new_password != confirm_password:
                form.add_error('confirm_password', 'Passwords do not match')
            elif not request.user.check_password(current_password):
                form.add_error('current_password', 'Incorrect current password')
            else:
                request.user.set_password(new_password)
                request.user.save()
                return redirect('transactions:profile')
    else:
        form = ChangePasswordForm()

    return render(request, 'change_password.html', {'form': form})


class SendMailView(View):
    def post(self, request, *args, **kwargs):
        """
        Send an email using the specified subject and message.
        """
        # Get the subject, message, and recipient from the request
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        recipient = request.POST.get('recipient')  # Ensure this is a valid email

        # Check if necessary fields are provided
        if not subject or not message or not recipient:
            return JsonResponse({'success': False, 'error': 'Subject, message, and recipient are required.'})

        try:
            # Send email using Django's send_mail function
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,  # Sender email
                [recipient],  # Recipient list
                fail_silently=False,  # Whether to fail silently on errors
            )
            return JsonResponse({'success': True, 'message': 'Email sent successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Failed to send email. Error: {str(e)}'})


def generate_otp(request):
    email = request.POST.get('email')

    if not email:
        return JsonResponse({"error": "Email is required."}, status=400)

    # Generate a random 6-digit OTP
    otp = ''.join(random.choices(string.digits, k=6))

    # Store OTP in cache (valid for 5 minutes)
    cache.set(f"otp_{email}", otp, timeout=300)

    # Send OTP via email (optional)
    try:
        send_mail(
            'Your OTP Code',
            f'Your OTP code is {otp}',
            settings.DEFAULT_FROM_EMAIL,
            [email]
        )
        return JsonResponse({"message": "OTP sent successfully."}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def send_mail_view(request):
    subject = request.POST.get('subject')
    message = request.POST.get('message')
    recipient_email = request.POST.get('recipient_email')

    if not subject or not message or not recipient_email:
        return JsonResponse({"error": "Subject, message, and recipient email are required."}, status=400)

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # Ensure this is set in your settings
            [recipient_email],
        )
        return JsonResponse({"message": "Email sent successfully."}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
