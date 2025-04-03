from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User  # If you are using the default User model
import logging

logger = logging.getLogger(__name__)

# Utility functions like send_sms, send_email, send_in_app_notification, and generate_otp are assumed to be imported here.


class Notification(models.Model):
    """
    Model for in-app notifications for users.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title[:20]}"


class UserOTP(models.Model):
    """
    Model to store OTP codes for users.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)  # The OTP code, assuming a 6-digit code
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        """Check if the OTP has expired."""
        return timezone.now() > self.expires_at

    def save(self, *args, **kwargs):
        """Set the expiration time to 5 minutes from creation if not already set."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"OTP for {self.user.username} - {self.otp}"


class FacialVerificationLog(models.Model):
    """
    Model to log facial verification attempts for users.
    """
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='facial_verification_logs'
    )
    verification_status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.email} - {self.verification_status} at {self.timestamp}"

    class Meta:
        verbose_name = "Facial Verification Log"
        verbose_name_plural = "Facial Verification Logs"
        ordering = ['-timestamp']