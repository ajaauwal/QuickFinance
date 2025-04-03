import os
from django.core.mail import send_mail
from django.conf import settings

# Ensure the settings module is set correctly for Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quickfinance.settings')

try:
    # Sending a test email
    send_mail(
        'Test Email',
        'This is a test email sent from Django.',
        settings.EMAIL_HOST_USER,  # Use the EMAIL_HOST_USER from settings
        ['zullymusty@gmail.com'],  # Replace with the recipient's email address
        fail_silently=False,
    )
    print("Email sent successfully!")
except Exception as e:
    print("Failed to send email:", e)
