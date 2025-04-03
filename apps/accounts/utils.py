from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from apps.notifications.utils import urlsafe_base64_encode
from django.utils.encoding import force_bytes

def send_password_reset_email(user, request):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    subject = 'Password Reset Request'
    message = render_to_string('accounts/password_reset_email.html', {
        'user': user,
        'uid': uid,
        'token': token,
        'protocol': 'https' if request.is_secure() else 'http',
        'domain': request.get_host()
    })
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
