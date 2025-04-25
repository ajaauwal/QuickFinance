from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetCompleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse_lazy
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import logging
from .forms import SignUpForm, InviteFriendForm, HelpRequestForm
from apps.transactions.models import Wallet, Transaction
from allauth.socialaccount.providers import registry
from allauth.socialaccount.models import SocialLogin
from social_django.utils import load_strategy
from allauth.socialaccount.helpers import complete_social_login

# Set up logging
logger = logging.getLogger(__name__)

User = get_user_model()

# --------------------- Views ---------------------
class IndexView(LoginRequiredMixin, View):
    def get(self, request):
        wallet = Wallet.objects.filter(user=request.user).first()
        transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')[:5]


        context = {
            "wallet": wallet,
            "wallet_currencies": [
                {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
            ] if wallet else [],
            "transactions": transactions,
        }
        return render(request, 'accounts/index.html', context)


# --------------------- Password Reset Views ---------------------
class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'


class InitiatePasswordResetView(View):
    def get(self, request):
        form = PasswordResetForm()
        return render(request, 'accounts/password_reset_form.html', {'form': form})

    def post(self, request):
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email=email).first()
            if user:
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
                messages.success(request, 'Password reset email has been sent.')
                return redirect(reverse_lazy('password_reset_done'))
            messages.error(request, 'No user found with this email address.')
        return render(request, 'accounts/password_reset_form.html', {'form': form})


# --------------------- Authentication Views ---------------------
class CustomLoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:index')
        form = AuthenticationForm()
        return render(request, 'accounts/login.html', {'form': form})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect(request.GET.get('next', reverse_lazy('accounts:index')))
        messages.error(request, 'Invalid login credentials.')
        return render(request, 'accounts/login.html', {'form': form})


class LoginAjaxView(View):
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return JsonResponse({'success': True, 'message': 'Login successful'})
        return JsonResponse({'success': False, 'message': 'Invalid credentials'}, status=400)


class CustomLogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect(request.GET.get('next', reverse_lazy('accounts:index')))


# --------------------- Miscellaneous Views ---------------------
@login_required
def invite_friends(request):
    if request.method == 'POST':
        form = InviteFriendForm(request.POST)
        if form.is_valid():
            invite = form.save(commit=False)
            invite.invited_by = request.user.email
            invite.save()
            return HttpResponse("Invitation sent successfully!")
    else:
        form = InviteFriendForm()
    return render(request, 'accounts/invite_friends.html', {'form': form})


def help_support(request):
    if request.method == 'POST':
        form = HelpRequestForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse("Your help request has been submitted successfully.")
    else:
        form = HelpRequestForm()
    return render(request, 'accounts/help_support.html', {'form': form})


# --------------------- Social Authentication Views ---------------------
class SocialDjangoView(View):
    def post(self, request, *args, **kwargs):
        provider = request.POST.get('provider')
        token = request.POST.get('token')

        if provider and token:
            strategy = load_strategy(request)
            provider_class = registry.by_id(provider)

            if provider_class:
                try:
                    social_login = SocialLogin()
                    social_login.token = token
                    complete_social_login(request, social_login)
                    messages.success(request, "Social login successful!")
                    return JsonResponse({'message': 'Social login successful'}, status=200)
                except Exception as e:
                    logger.error(f"Social login error: {e}")
                    return JsonResponse({'error': 'Social login failed'}, status=400)

            return JsonResponse({'error': 'Provider not supported'}, status=400)

        return JsonResponse({'error': 'Invalid social login data'}, status=400)


# --------------------- SignUp View ---------------------
class SignUpView(View):
    def get(self, request):
        return render(request, 'accounts/signup.html', {'form': SignUpForm()})

    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Signup successful! Please log in to continue.")
            return redirect('accounts:login')  # Redirects to login page after signup
        return render(request, 'accounts/signup.html', {'form': form})
