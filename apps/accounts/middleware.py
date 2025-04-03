# middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class AuthenticationMiddleware:
    """
    Middleware that checks if a user is authenticated before accessing the homepage.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            # Redirect the user to the login page if not authenticated
            if request.path not in [reverse('login'), reverse('signup')]:
                return redirect('login')  # Replace 'login' with the actual name of your login view
        response = self.get_response(request)
        return response
