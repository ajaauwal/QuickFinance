from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
        
    # Password Reset URLs
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset-done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Other Views
    path('help-support/', views.help_support, name='help_support'),
    path('invite-friends/', views.invite_friends, name='invite_friends'),

    # Index page (homepage) using the IndexView class
    path('', views.IndexView.as_view(), name='index'),  # Corrected to use IndexView class

    # API route for fetching wallet balance and token authentication
    path('api/token/', obtain_auth_token, name='api-token'),  # Token authentication
    path('accounts/', include('social_django.urls', namespace='social')),

    
]
