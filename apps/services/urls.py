from django.urls import path
from . import views
from .views import (
    DataTopUpView, WAECResultCheckerView, SchoolFeesPaymentView, flight_search, search_hotels
)

app_name = 'services'

urlpatterns = [
    # Airtime and Data Topup
    path('services/purchase_airtime/', views.purchase_airtime, name='purchase_airtime'),
    path('data_topup/', DataTopUpView.as_view(), name='data_topup'),
   
    # School Fees Payment
    path('school_fees_payment/', SchoolFeesPaymentView.as_view(), name='school_fees_payment'),
    path('school_fees_payment_success/', views.school_fees_payment_success, name='school_fees_payment_success'),

    # Utility Payments
    path('electricity_payment/', views.electricity_payment, name='electricity_payment'),
    path('utility/pay/', views.utility_bills, name='utility_bills'),
    path('utility/history/', views.utility_bills_history, name='utility_bills_history'),
    path('electricity_payment_success/', views.electricity_payment_success, name='electricity_payment_success'),

    # TV Payment Services
    path('dstv_payment/', views.dstv_payment, name='dstv_payment'),
    path('dstv_payment_success/', views.dstv_payment_success, name='dstv_payment_success'),
    path('gotv_payment/', views.gotv_payment, name='gotv_payment'),
    path('gotv_payment_success/', views.gotv_payment_success, name='gotv_payment_success'),
    path('startimes_payment/', views.startimes_payment, name='startimes_payment'),
    path('startimes_payment_success/', views.startimes_payment_success, name='startimes_payment_success'),

    # Search
    path('search/', views.search_view, name='search'),

    # WAEC Result Checker
    path('waec-result-checker/', WAECResultCheckerView.as_view(), name='waec_result_checker'),

    # Flight Booking and APIs
    path('flight_booking/', views.flight_booking, name='flight_booking'),
    path('api/flights/', flight_search, name='search_flights'),  # For flight search
    path('api/hotels/', search_hotels, name='search_hotels'),  # For hotel search
]
