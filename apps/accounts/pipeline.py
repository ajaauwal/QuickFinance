# accounts/pipeline.py

from social_core.exceptions import AuthForbidden
from django.contrib.auth import get_user_model
from social_core.pipeline.partial import partial

User = get_user_model()

@partial
def prevent_login_existing_user(backend, uid, user=None, social=None, *args, **kwargs):
    """
    Prevents existing users from logging in via Google. 
    This ensures Google is used for signup only.
    """
    # If a social account is already linked to a user, block login
    if social:
        raise AuthForbidden(backend, "You already have an account. Please log in instead.")

    # Additionally, prevent if there's an existing user with the same email
    details = kwargs.get('details', {})
    email = details.get('email')
    if email:
        try:
            existing_user = User.objects.get(email=email)
            # Block signup if user with same email exists
            raise AuthForbidden(backend, "An account with this email already exists. Please log in.")
        except User.DoesNotExist:
            # No user found, allow the signup to proceed
            pass

    return
