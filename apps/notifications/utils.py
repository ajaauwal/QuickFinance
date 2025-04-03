import logging
import random
import base64
import pyotp
import requests
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings
from django.apps import apps
from typing import Optional, Any
from django.contrib.auth.models import User

# Set up logging
logger = logging.getLogger(__name__)

# --------------------------- ENCODING / DECODING UTILS ---------------------------

def encode_uid(uid: Any) -> str:
    """
    Encode a user ID or any data to a URL-safe base64 string.
    """
    return urlsafe_base64_encode(force_bytes(uid))


def decode_uid(encoded_uid: str) -> str:
    """
    Decode a URL-safe base64 encoded string back to its original data.
    """
    try:
        return force_str(urlsafe_base64_decode(encoded_uid))
    except (ValueError, TypeError) as e:
        logger.error(f"Error decoding UID: {e}")
        raise ValueError("Invalid or malformed encoded UID.")


def encode_data(data: str) -> str:
    """
    Encode data using Base64.
    """
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')


def decode_data(encoded_data: str) -> Optional[str]:
    """
    Decode Base64 encoded data.
    """
    try:
        return base64.b64decode(encoded_data).decode('utf-8')
    except Exception as e:
        logger.error(f"Error decoding data: {e}")
        return None


# --------------------------- OTP UTILS ---------------------------

def generate_otp() -> str:
    """
    Generate a 6-digit OTP.
    """
    return f"{random.randint(100000, 999999)}"


def generate_totp(secret: str) -> str:
    """
    Generate a time-based one-time password (TOTP) using a secret key.
    """
    totp = pyotp.TOTP(secret)
    return totp.now()


def verify_totp(secret: str, otp: str) -> bool:
    """
    Verify a given TOTP against the secret key.
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(otp)


# --------------------------- SMS UTILS ---------------------------

def send_sms(phone_number: str, message: str) -> bool:
    """
    Sends an SMS to the given phone number using a third-party SMS gateway.
    """
    SMS_API_URL = "https://example-sms-api.com/send"  # Replace with actual SMS API URL
    API_KEY = "your_api_key"  # Replace with your SMS API key

    payload = {
        "to": phone_number,
        "message": message,
        "api_key": API_KEY,
    }

    try:
        response = requests.post(SMS_API_URL, json=payload)
        response.raise_for_status()
        logger.info(f"SMS sent to {phone_number}: {message}")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to send SMS to {phone_number}: {e}")
        return False


# --------------------------- EMAIL UTILS ---------------------------

def send_email(subject: str, message: str, recipient_list: list) -> bool:
    """
    Sends an email to the specified recipients.
    """
    from_email = settings.DEFAULT_FROM_EMAIL  # Ensure DEFAULT_FROM_EMAIL is set in settings.py

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        logger.info(f"Email sent to {recipient_list}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_list}: {e}")
        return False


# --------------------------- IN-APP NOTIFICATION UTILS ---------------------------

def send_in_app_notification(user: User, title: str, message: str) -> bool:
    """
    Sends an in-app notification to the specified user.
    """
    try:
        # Import the Notification model dynamically to avoid circular imports
        Notification = apps.get_model('notifications', 'Notification')

        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            created_at=now()
        )
        logger.info(f"In-app notification sent to {user.username}: {title}")
        return True
    except Exception as e:
        logger.error(f"Failed to send in-app notification to {user.username}: {e}")
        return False
