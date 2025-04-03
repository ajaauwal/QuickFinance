from django.urls import path
from . import views
from .views import (
    PurchaseAirtimeView, DataTopUpView, FlightBookingView, WAECResultCheckerView, PayForServiceView,
    SchoolFeesPaymentView, FlightPaymentView, RescheduleFlightView, CancelFlightView, 
    FlightBookedView, FlightCancelledView, FlightResultsView, service_details, search_view
)

app_name = 'services'

urlpatterns = [
    # VTpass-related payment URLs
    path('airtime/purchase/', PurchaseAirtimeView.as_view(), name='purchase_airtime'),
    path('data/topup/', DataTopUpView.as_view(), name='data_topup'),
    path('electricity/payment/', views.electricity_payment, name='electricity_payment'),
    path('dstv/payment/', views.dstv_payment, name='dstv_payment'),
    path('gotv/payment/', views.gotv_payment, name='gotv_payment'),
    path('startimes/payment/', views.startimes_payment, name='startimes_payment'),
    path('school-fees/payment/', SchoolFeesPaymentView.as_view(), name='school_fees_payment'),

    # Success pages for VTpass services
    path('electricity-payment/success/', views.electricity_payment_success, name='electricity_payment_success'),
    path('dstv-payment/success/', views.dstv_payment_success, name='dstv_payment_success'),
    path('gotv-payment/success/', views.gotv_payment_success, name='gotv_payment_success'),
    path('startimes-payment/success/', views.startimes_payment_success, name='startimes_payment_success'),
    path('school-fees-payment/success/', views.school_fees_payment_success, name='school_fees_payment_success'),

    # Flight booking and management URLs
    path('flight/booking/', FlightBookingView.as_view(), name='flight_booking'),
    path('flight/results/', FlightResultsView.as_view(), name='flight_results'),  
    path('flight/payment/', FlightPaymentView.as_view(), name='flight_payment'),
    path('flight/reschedule/', RescheduleFlightView.as_view(), name='reschedule_flight'),
    path('flight/cancel/', CancelFlightView.as_view(), name='cancel_flight'),
    path('flight/booked/', FlightBookedView.as_view(), name='flight_booked'),
    path('flight/cancelled/', FlightCancelledView.as_view(), name='flight_cancelled'),

    # General service payments and search
    path('pay-for-service/', PayForServiceView.as_view(), name='pay_for_service'),
    path('payment/success/', views.payment_success, name='payment_success'),

    # WAEC Result Checker
    path('waec-result-checker/', WAECResultCheckerView.as_view(), name='waec_result_checker'),

    # Utility Bills
    path("utility-bills/", views.utility_bills, name="utility_bills"),

    # Search and Service Details
    path('search/', search_view, name='search'),
    path('<int:id>/', service_details, name='service_details'),
]
