from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import environ
from django.contrib.auth import get_user_model

User = get_user_model()



# Initialize environment variables from .env
env = environ.Env()
environ.Env.read_env()

# Ensure the signal is connected to the User model
@receiver(post_save, sender=User)
def send_verification_email(sender, instance, created, **kwargs):
    # Only send verification email if it's a newly created user and not a superuser
    if created and not instance.is_superuser:
        subject = 'Verify your email'
        message = render_to_string('emails/verification_email.html', {'user': instance})
        from_email = env('EMAIL_HOST_USER')  # Fetch the sender email from the .env file
        recipient_list = [instance.email]
        
        # Send email
        send_mail(subject, message, from_email, recipient_list)
