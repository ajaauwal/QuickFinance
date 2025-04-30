from django import forms
from django.core.validators import RegexValidator
from .models import PurchaseAirtime, DataTopUp, UtilityBills, ElectricityPayment, DstvSubscription, GoTVSubscription, StarTimesSubscription, SchoolFeesPayment, WaecResultCheck, Flight, Booking, FlightSearch, PaystackTransaction, ServicePayment

# Validator for Nigerian phone numbers
phone_validator = RegexValidator(
    regex=r'^[0]\d{10}$',
    message="Enter a valid 11-digit phone number starting with 0."
)

# Services for selection dropdown
SERVICES = [
    ('PurchaseAirtime', 'Airtime Recharge'),
    ('DataPurchase', 'Data Purchase'),
    ('SchoolFeesPayment', 'School Fees Payment'),
    ('AirlineBooking', 'Airline Booking'),
    ('ElectricityPayment', 'Electricity Payment'),
    ('DstvSubscription', 'DSTV Subscription'),
    ('GoTVSubscription', 'GoTV Subscription'),
    ('StarTimesSubscription', 'StarTimes Subscription'),
    ('waecresultcheck', 'WAEC Result Check'),
]

# =====================================
# Service Payment Form
# =====================================
class ServicePaymentForm(forms.ModelForm):
    class Meta:
        model = ServicePayment
        fields = ['service_name', 'customer_name', 'phone_number', 'amount']
        widgets = {
            'service_name': forms.TextInput(attrs={'placeholder': 'Enter Service Name'}),
            'customer_name': forms.TextInput(attrs={'placeholder': 'Enter Your Name'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Enter Phone Number', 'validators': [phone_validator]}),
            'amount': forms.NumberInput(attrs={'placeholder': 'Enter Amount'}),
        }
        labels = {
            'service_name': 'Service Name',
            'customer_name': 'Customer Name',
            'phone_number': 'Phone Number',
            'amount': 'Amount',
        }

# =====================================
# Airtime Recharge Form
# =====================================
class PurchaseAirtimeForm(forms.ModelForm):
    class Meta:
        model = PurchaseAirtime
        fields = ['network_provider', 'phone_number', 'amount', 'payment_method']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

# =====================================
# Data Top-Up Form
# =====================================
class DataTopUpForm(forms.ModelForm):
    class Meta:
        model = DataTopUp
        fields = ['network_provider', 'phone_number', 'amount', 'payment_method']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

# =====================================
# Utility Bills Form
# =====================================
class UtilityBillsForm(forms.ModelForm):
    class Meta:
        model = UtilityBills
        fields = ['service_type', 'account_number', 'amount', 'cable_provider', 'payment_method']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

# =====================================
# Electricity Payment Form
# =====================================
class ElectricityPaymentForm(forms.ModelForm):
    class Meta:
        model = ElectricityPayment
        fields = ['meter_type', 'meter_number', 'amount', 'contact_number']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

# =====================================
# DSTV Subscription Form
# =====================================
class DstvSubscriptionForm(forms.ModelForm):
    class Meta:
        model = DstvSubscription
        fields = ['customer_type', 'smart_card_number', 'package', 'amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

# =====================================
# GoTV Subscription Form
# =====================================
class GoTVSubscriptionForm(forms.ModelForm):
    class Meta:
        model = GoTVSubscription
        fields = ['customer_type', 'smart_card_number', 'package', 'amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

# =====================================
# StarTimes Subscription Form
# =====================================
class StarTimesSubscriptionForm(forms.ModelForm):
    class Meta:
        model = StarTimesSubscription
        fields = ['customer_type', 'smart_card_number', 'package', 'amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

# =====================================
# School Fees Payment Form
# =====================================
class SchoolFeesPaymentForm(forms.ModelForm):
    class Meta:
        model = SchoolFeesPayment
        fields = ['student_name', 'amount', 'payment_method']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

# =====================================
# WAEC Result Check Form
# =====================================
class WaecResultCheckForm(forms.ModelForm):
    class Meta:
        model = WaecResultCheck
        fields = ['exam_number', 'exam_year', 'amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

# =====================================
# Flight Booking Form
# =====================================
class FlightForm(forms.ModelForm):
    class Meta:
        model = Flight
        fields = ['flight_number', 'departure', 'destination', 'arrival_time', 'price', 'available_seats']
        widgets = {
            'departure': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'arrival_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

# =====================================
# Flight Booking Form for Users
# =====================================
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['flight', 'email', 'passengers']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Your Email', 'class': 'form-control'}),
            'passengers': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'flight': forms.Select(attrs={'class': 'form-control'}),
        }

# =====================================
# Flight Search Form
# =====================================
class FlightSearchForm(forms.ModelForm):
    class Meta:
        model = FlightSearch
        fields = ['origin', 'destination', 'date']

# =====================================
# Paystack Transaction Form
# =====================================
class PaystackTransactionForm(forms.ModelForm):
    class Meta:
        model = PaystackTransaction
        fields = ['reference', 'status', 'amount']

# =====================================
# Service Payment Form
# =====================================
class ServicePaymentForm(forms.ModelForm):
    class Meta:
        model = ServicePayment
        fields = ['service_name', 'customer_name', 'phone_number', 'amount', 'payment_reference', 'status']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }
