from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _



# Gender choices for the user model
GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]


from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom user model aligned with SignUpForm.
    Email is used as the primary identifier instead of username.
    """
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)

    # Email will be used for login
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    class Meta:
        app_label = 'accounts'
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class InviteFriend(models.Model):
    """
    Model to handle user invitations.
    """
    friend_name = models.CharField(max_length=255)
    friend_email = models.EmailField()
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    date_invited = models.DateTimeField(auto_now_add=True)
    invitation_status = models.CharField(max_length=50, default='Pending')

    def __str__(self):
        return f"Invitation to {self.friend_name} ({self.friend_email}) by {self.invited_by.email}"

    class Meta:
        ordering = ['-date_invited']


class HelpRequest(models.Model):
    """
    Model to store help requests submitted by users.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='help_requests'
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50,
        choices=[('Pending', 'Pending'), ('Resolved', 'Resolved')],
        default='Pending'
    )

    def __str__(self):
        return f"Help Request from {self.user.email}"

    class Meta:
        ordering = ['-created_at']
