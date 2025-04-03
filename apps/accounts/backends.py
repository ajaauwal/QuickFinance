from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class EmailBackend(ModelBackend):
    """
    Custom authentication backend to authenticate users using their email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user by email address and password.
        """
        email = kwargs.get('email', username)  # Allow `username` for compatibility with default auth forms
        if email is None or password is None:
            return None
        
        try:
            # Check if a user exists with the given email
            user = UserModel.objects.get(Q(email=email))
        except UserModel.DoesNotExist:
            return None
        
        # Validate password and return the user if valid
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None

    def user_can_authenticate(self, user):
        """
        Reject inactive users by default. Extendable for more conditions.
        """
        return super().user_can_authenticate(user)
