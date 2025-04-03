from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# Gender choices for the gender field
GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

class User(AbstractUser):
    """
    Custom user model with additional fields for profile information.
    """
    surname = models.CharField(max_length=30)  # Ensure it doesn't conflict with last_name
    other_name = models.CharField(max_length=30, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    registration_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    school = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True)
    
    # Ensure email is unique for authentication
    email = models.EmailField(unique=True)

    # Override the default USERNAME_FIELD to use email instead of username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'surname', 'registration_number']

    def __str__(self):
        return f"{self.first_name} {self.surname} ({self.email})"

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
