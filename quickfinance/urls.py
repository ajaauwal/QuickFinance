from django.contrib import admin
from django.urls import path, include
from apps.accounts.views import CustomLoginView  # Import the CustomLoginView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Define the schema view for Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Quickfinance API",
        default_version='v1',
        description="API documentation for the Quickfinance project",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@quickfinance.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Root URL directs to the login page in the accounts app
    path('', CustomLoginView.as_view(), name='login'),

    # Admin route
    path('admin/', admin.site.urls),

    # Debug toolbar route (ensure 'debug_toolbar' is installed and in INSTALLED_APPS)
    path('__debug__/', include('debug_toolbar.urls')),

    # Include app-specific URLs
    path('accounts/', include('apps.accounts.urls')),  # Accounts app URLs
    path('services/', include('apps.services.urls')),  # Services app URLs
    path('transactions/', include('apps.transactions.urls')),  # Transactions app URLs
    path('notifications/', include('apps.notifications.urls')),  # Notifications app URLs

    # Social authentication URLs
    path('social-auth/', include('social_django.urls', namespace='social')),

    # Swagger UI routes
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('swagger.json/', schema_view.without_ui(cache_timeout=0), name='swagger-json'),
]
