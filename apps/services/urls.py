from django.urls import path
from . import views
from .views import (
    PurchaseAirtimeView, DataTopUpView, FlightBookingView, WAECResultCheckerView, 
    SchoolFeesPaymentView, FlightPaymentView, RescheduleFlightView, CancelFlightView, FlightBookedView, FlightCancelledView
)

app_name = 'services'

urlpatterns = [
    path('purchase_airtime/', PurchaseAirtimeView.as_view(), name='purchase_airtime'),
    path('data_topup/', DataTopUpView.as_view(), name='data_topup'),
    path('flight_booking/', FlightBookingView.as_view(), name='flight_booking'),
    path('flight_results/', views.FlightBookingView.as_view(), name='flight_results'),
    path('flight_payment/', FlightPaymentView.as_view(), name='flight_payment'),
    path('reschedule_flight/', RescheduleFlightView.as_view(), name='reschedule_flight'),
    path('cancel_flight/', CancelFlightView.as_view(), name='cancel_flight'),
    path('flight_booked/', FlightBookedView.as_view(), name='flight_booked'),
    path('flight_cancelled/', FlightCancelledView.as_view(), name='flight_cancelled'),
    path('get_loan/', views.get_loan, name='get_loan'),
    path('loan_success/', views.loan_success, name='loan_success'),
    path('school_fees_payment/', SchoolFeesPaymentView.as_view(), name='school_fees_payment'),
    path('school_fees_payment_success/', views.school_fees_payment_success, name='school_fees_payment_success'),
    path('electricity_payment/', views.electricity_payment, name='electricity_payment'),
    path('utility/pay/', views.utility_bills, name='utility_bills'),
    path('utility/history/', views.utility_bills_history, name='utility_bills_history'),
    path('electricity_payment_success/', views.electricity_payment_success, name='electricity_payment_success'),
    path('dstv_payment/', views.dstv_payment, name='dstv_payment'),
    path('dstv_payment_success/', views.dstv_payment_success, name='dstv_payment_success'),
    path('gotv_payment/', views.gotv_payment, name='gotv_payment'),
    path('gotv_payment_success/', views.gotv_payment_success, name='gotv_payment_success'),
    path('startimes_payment/', views.startimes_payment, name='startimes_payment'),
    path('startimes_payment_success/', views.startimes_payment_success, name='startimes_payment_success'),
    path('search/', views.search_view, name='search'),
    path('waec-result-checker/', WAECResultCheckerView.as_view(), name='waec_result_checker'),
]
