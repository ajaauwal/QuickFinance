from django.urls import path
from .views import (
    IndexView, CustomLoginView, CustomLogoutView, SignUpView,
    CustomPasswordResetView, CustomPasswordResetDoneView,
    CustomPasswordResetCompleteView, InitiatePasswordResetView,
    invite_friends, help_support, LoginAjaxView, SocialDjangoView
)

app_name = 'accounts'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
    
    # Password reset paths
    path('password-reset/', InitiatePasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Ajax login
    path('ajax/login/', LoginAjaxView.as_view(), name='ajax_login'),

    # Social login
    path('social/login/', SocialDjangoView.as_view(), name='social_login'),

    # Other features
    path('invite/', invite_friends, name='invite_friends'),
    path('help/', help_support, name='help_support'),
]
