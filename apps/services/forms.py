from django import forms
from django.core.validators import RegexValidator
from .models import (
    AirtimeRecharge, DataTopUp, LoanApplication, SchoolFeesPayment, FlightBooking,
    ElectricityPayment, DstvSubscription, GoTVSubscription, StarTimesSubscription,
    ServicePayment
)

# Validator for Nigerian phone numbers
phone_validator = RegexValidator(
    regex=r'^[0]\d{10}$',
    message="Enter a valid 11-digit phone number starting with 0."
)

# Services for selection dropdown
SERVICES = [
    ('AirtimeRecharge', 'Airtime Recharge'),
    ('DataPurchase', 'Data Purchase'),
    ('SchoolFeesPayment', 'School Fees Payment'),
    ('AirlineBooking', 'Airline Booking'),
    ('ElectricityPayment', 'Electricity Payment'),
    ('DstvSubscription', 'DSTV Subscription'),
    ('GoTVSubscription', 'GoTV Subscription'),
    ('StarTimesSubscription', 'StarTimes Subscription'),
]

class ServicePaymentForm(forms.ModelForm):
    class Meta:
        model = ServicePayment
        fields = ['service_name', 'customer_name', 'phone_number', 'amount']
        widgets = {
            'service_name': forms.TextInput(attrs={'placeholder': 'Enter Service Name'}),
            'customer_name': forms.TextInput(attrs={'placeholder': 'Enter Your Name'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Enter Phone Number'}),
            'amount': forms.NumberInput(attrs={'placeholder': 'Enter Amount'}),
        }
        labels = {
            'service_name': 'Service Name',
            'customer_name': 'Customer Name',
            'phone_number': 'Phone Number',
            'amount': 'Amount',
        }

# Airtime Recharge Form
class AirtimeRechargeForm(forms.ModelForm):
    NETWORK_PROVIDERS = [
        ('mtn', 'MTN', 'images/mtn.png'),
        ('glo', 'Glo', 'images/glo.png'),
        ('airtel', 'Airtel', 'images/airtel.png'),
        ('9mobile', '9Mobile', 'images/9mobile.png'),
    ]
    AMOUNTS = [
        (100, '₦100'),
        (200, '₦200'),
        (500, '₦500'),
        (1000, '₦1000'),
        (2000, '₦2000'),
    ]

    network_provider = forms.ChoiceField(choices=[(x[0], x[1]) for x in NETWORK_PROVIDERS], label="Network Provider")
    phone_number = forms.CharField(
        max_length=11,
        label="Phone Number",
        validators=[phone_validator],
        widget=forms.TextInput(attrs={'placeholder': 'Enter Phone Number'})
    )
    amount = forms.ChoiceField(choices=AMOUNTS, label="Recharge Amount")

    class Meta:
        model = AirtimeRecharge
        fields = ['network_provider', 'phone_number', 'amount']

# Data TopUp Form
class DataTopUpForm(forms.ModelForm):
    DATA_PROVIDERS = AirtimeRechargeForm.NETWORK_PROVIDERS
    DATA_PLANS = [
        ('daily', 'Daily Subscription'),
        ('weekly', 'Weekly Subscription'),
        ('monthly', 'Monthly Subscription'),
        ('2_months', '2-Months Subscription'),
        ('3_months', '3-Months Subscription'),
        ('6_months', '6-Months Subscription'),
        ('1_year', '1-Year Subscription'),
    ]

    provider = forms.ChoiceField(choices=[(x[0], x[1]) for x in DATA_PROVIDERS], label="Data Provider")
    data_plan = forms.ChoiceField(choices=DATA_PLANS, label="Subscription Duration")
    phone_number = forms.CharField(max_length=11, validators=[phone_validator], label="Phone Number")
    amount = forms.DecimalField(max_digits=10, decimal_places=2, label="Amount")

    class Meta:
        model = DataTopUp
        fields = ['provider', 'data_plan', 'phone_number', 'amount']

# School Fees Payment Form
class SchoolFeesPaymentForm(forms.ModelForm):
    FACULTIES = [
        ('engineering', 'Faculty of Engineering - ₦100,000'),
        ('law', 'Faculty of Law - ₦120,000'),
        ('arts', 'Faculty of Arts - ₦80,000'),
        ('science', 'Faculty of Science - ₦90,000'),
    ]

    faculty = forms.ChoiceField(choices=FACULTIES)
    student_id = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Enter Student ID'}))
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = SchoolFeesPayment
        fields = ['faculty', 'student_id', 'amount']

# Flight Booking and Payment Forms
class FlightBookingForm(forms.Form):
    departure_city = forms.CharField(max_length=100)
    arrival_city = forms.CharField(max_length=100)
    departure_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}))
    return_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}), required=False)
    number_of_passengers = forms.IntegerField(min_value=1)
    children = forms.IntegerField(min_value=0, required=False)
    infants = forms.IntegerField(min_value=0, required=False)
    contact_number = forms.CharField(max_length=15)

    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number')
        if len(contact_number) < 10:
            raise forms.ValidationError("Please enter a valid contact number.")
        return contact_number

class FlightPaymentForm(forms.Form):
    flight_id = forms.CharField(widget=forms.HiddenInput())
    amount = forms.DecimalField(widget=forms.HiddenInput())
    payment_method = forms.ChoiceField(choices=[('wallet', 'Wallet'), ('debit_card', 'Debit Card')])

class ConfirmBookingForm(forms.Form):
    flight_id = forms.CharField(widget=forms.HiddenInput())

class FlightResultsForm(forms.Form):
    flight_id = forms.CharField(widget=forms.HiddenInput())
    amount = forms.DecimalField(widget=forms.HiddenInput())
    payment_method = forms.ChoiceField(choices=[('wallet', 'Wallet'), ('debit_card', 'Debit Card')])
    status = forms.CharField(widget=forms.HiddenInput())
    booking_date = forms.DateField(widget=forms.HiddenInput())
    cancel_reason = forms.CharField(widget=forms.Textarea(), required=False)
    new_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}), required=False)
    booking_reference = forms.CharField(max_length=100, required=False, widget=forms.HiddenInput())

class FlightBookedForm(forms.Form):
    flight_id = forms.CharField(widget=forms.HiddenInput())
    booking_reference = forms.CharField(max_length=100)

class RescheduleFlightForm(forms.Form):
    flight_id = forms.CharField(widget=forms.HiddenInput())
    new_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}))

class CancelFlightForm(forms.Form):
    flight_id = forms.CharField(widget=forms.HiddenInput())
    cancel_reason = forms.CharField(widget=forms.Textarea())

# Electricity Payment
class ElectricityPaymentForm(forms.ModelForm):
    METER_TYPES = [
        ('prepaid', 'Prepaid Meter'),
        ('postpaid', 'Postpaid Meter'),
    ]

    meter_type = forms.ChoiceField(choices=METER_TYPES)
    meter_number = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Enter Meter Number'}))
    amount = forms.DecimalField(max_digits=10, decimal_places=2)
    contact_number = forms.CharField(max_length=11, validators=[phone_validator])

    class Meta:
        model = ElectricityPayment
        fields = ['meter_type', 'meter_number', 'amount', 'contact_number']

# DSTV Subscription
class DstvSubscriptionForm(forms.ModelForm):
    CUSTOMER_TYPES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
    ]

    DSTV_PACKAGES = [
        ('premium', 'Premium - ₦10,000'),
        ('compact_plus', 'Compact Plus - ₦7,500'),
        ('compact', 'Compact - ₦5,000'),
        ('comfam', 'Confam - ₦3,800'),
        ('yanga', 'Yanga - ₦2,500'),
        ('padi', 'Padi - ₦1,800'),
    ]

    customer_type = forms.ChoiceField(choices=CUSTOMER_TYPES)
    smart_card_number = forms.CharField(max_length=30)
    package = forms.ChoiceField(choices=DSTV_PACKAGES)
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=1.00)

    class Meta:
        model = DstvSubscription
        fields = ['customer_type', 'smart_card_number', 'package', 'amount']

# GoTV Subscription
class GoTVSubscriptionForm(forms.ModelForm):
    CUSTOMER_TYPES = DstvSubscriptionForm.CUSTOMER_TYPES

    GOTV_PACKAGES = [
        ('supa_plus', 'Supa+ - ₦5,500'),
        ('supa', 'Supa - ₦4,500'),
        ('max', 'Max - ₦3,200'),
        ('jolli', 'Jolli - ₦2,460'),
        ('jinja', 'Jinja - ₦1,640'),
        ('smallie', 'Smallie - ₦800'),
    ]

    customer_type = forms.ChoiceField(choices=CUSTOMER_TYPES)
    smart_card_number = forms.CharField(max_length=30)
    package = forms.ChoiceField(choices=GOTV_PACKAGES)
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=1.00)

    class Meta:
        model = GoTVSubscription
        fields = ['customer_type', 'smart_card_number', 'package', 'amount']

# StarTimes Subscription
class StarTimesSubscriptionForm(forms.ModelForm):
    CUSTOMER_TYPES = DstvSubscriptionForm.CUSTOMER_TYPES

    STARTIMES_PACKAGES = [
        ('nova_dish', 'Nova (Dish) - ₦1,700'),
        ('nova_antenna', 'Nova (Antenna) - ₦1,300'),
        ('basic', 'Basic - ₦2,500'),
        ('smart', 'Smart - ₦3,500'),
        ('classic', 'Classic - ₦4,500'),
    ]

    customer_type = forms.ChoiceField(choices=CUSTOMER_TYPES)
    smart_card_number = forms.CharField(max_length=30)
    package = forms.ChoiceField(choices=STARTIMES_PACKAGES)
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=1.00)

    class Meta:
        model = StarTimesSubscription
        fields = ['customer_type', 'smart_card_number', 'package', 'amount']


# Loan Application Form
class LoanApplicationForm(forms.ModelForm):
    TERM_CHOICES = [(i, f"{i} months") for i in range(1, 61)]  # Loan term choices from 1 to 60 months

    amount = forms.DecimalField(max_digits=10, decimal_places=2, label="Loan Amount")
    term = forms.ChoiceField(choices=TERM_CHOICES, label="Loan Term")
    purpose = forms.CharField(max_length=255, label="Purpose of Loan", widget=forms.Textarea(attrs={'placeholder': 'Enter the purpose of the loan'}))

    class Meta:
        model = LoanApplication
        fields = ['amount', 'term', 'purpose']



class UtilityBillsForm(forms.Form):
    provider = forms.ChoiceField(choices=[
        ('electricity', 'Electricity'),
        ('dstv', 'DSTV'),
        ('gotv', 'GOTV'),
        ('startimes', 'Startimes')
    ])
    account_number = forms.CharField(max_length=20)
    amount = forms.DecimalField(max_digits=10, decimal_places=2)
    email = forms.EmailField()


from django import forms

class WAECResultCheckerForm(forms.Form):
    candidate_number = forms.CharField(max_length=10, required=True, label="Candidate Number")
    year_of_exam = forms.IntegerField(required=True, label="Year of Exam")
    payment_method = forms.ChoiceField(choices=[('wallet', 'Wallet'), ('debit_card', 'Debit Card')], label="Payment Method")
    email = forms.EmailField(required=True, label="Email Address")
    card_details = forms.CharField(widget=forms.PasswordInput(), required=False, label="Debit Card Details (if Debit Card selected)")
