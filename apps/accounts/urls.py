from . import views
from django.urls import include, path
from .views import (
    IndexView, CustomLoginView, CustomLogoutView, SignUpView,
    CustomPasswordResetView, CustomPasswordResetDoneView,
    CustomPasswordResetCompleteView, InitiatePasswordResetView,
    invite_friends, help_support, LoginAjaxView,
    CustomPasswordResetConfirmView
)

app_name = 'accounts'

urlpatterns = [
    # Home and index
    path('', IndexView.as_view(), name='index'),
    path('home/', views.home_view, name='home'),

    # Authentication
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
     path('oauth/', include('social_django.urls', namespace='social')),

    # Password reset
    path('password-reset/', InitiatePasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Ajax login
    path('ajax/login/', LoginAjaxView.as_view(), name='ajax_login'),

    # Social Auth (Signup + Login)
   

    # Extra features
    path('invite/', invite_friends, name='invite_friends'),
    path('help/', help_support, name='help_support'),
]
