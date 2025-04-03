from django.urls import path
from . import views
from .views import CustomPasswordResetView, PasswordResetCompleteView, InitiatePasswordResetView

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('mark-as-read/<int:id>/', views.mark_as_read, name='mark_as_read'),
    path('complete-transaction/<int:transaction_id>/', views.complete_transaction, name='complete_transaction'),
    path('send-sms/', views.send_sms, name='send_sms'),
    path('gencode/', views.gencode, name='gencode'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('send-mail/', views.SendMailView.as_view(), name='send_mail'),
    path('decode-uid/', views.DecodeUIDView.as_view(), name='decode_uid'),
    
    # Password management routes
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),  # Password reset page
    path('password-reset-complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),  # Password reset complete page
    path('initiate-password-reset/', InitiatePasswordResetView.as_view(), name='initiate_password_reset'),  # Initiate password reset
]
