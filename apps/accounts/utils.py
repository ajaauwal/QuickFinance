from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

def send_verification_email(user, request):
    subject = "Please verify your email address"
    message = render_to_string(
        'accounts/verification_email.html',
        {
            'user': user,
            'protocol': 'https' if request.is_secure() else 'http',
            'domain': request.get_host()
        }
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
