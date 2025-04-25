from django.db import models
from django.conf import settings


# =====================================
# SERVICE DEFINITION MODEL
# =====================================
class Service(models.Model):
    SERVICE_TYPES = [
        ('airtime', 'Airtime Recharge'),
        ('data', 'Data Top-Up'),
        ('electricity', 'Electricity Bill'),
        ('cable_tv', 'Cable TV Bill'),
        ('flight', 'Flight Booking'),
        ('fees', 'School Fees'),
        ('waecresultcheck', 'WAEC Result Check'),
    ]
    name = models.CharField(max_length=50)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)

    def __str__(self):
        return self.name


# =====================================
# BASE PAYMENT CHOICE
# =====================================
PAYMENT_METHOD_CHOICES = [
    ('credit_card', 'Credit Card'),
    ('bank_transfer', 'Bank Transfer'),
    ('wallet_balance', 'Wallet Balance'),
]


# =====================================
# AIRTIME RECHARGE
# =====================================
# Define Network Providers
NETWORK_PROVIDERS = (
    ('MTN', 'MTN'),
    ('Airtel', 'Airtel'),
    ('Glo', 'Glo'),
    ('9Mobile', '9Mobile'),
)

# =====================================
# Airtime Recharge
# =====================================
class AirtimeRecharge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='airtime_recharges')
    network_provider = models.CharField(max_length=20, choices=NETWORK_PROVIDERS)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.network_provider} - {self.amount}"


# =====================================
# DATA TOP-UP
# =====================================
class DataTopUp(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='data_topups'
    )
    network_provider = models.CharField(max_length=20, choices=NETWORK_PROVIDERS)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.network_provider} - {self.amount}"


# =====================================
# UTILITY BILLS (Generic)
# =====================================
class UtilityBills(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='utility_bills')
    service_type = models.CharField(max_length=20)
    account_number = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    cable_provider = models.CharField(max_length=20, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.service_type} - {self.amount}"


# =====================================
# ELECTRICITY PAYMENT
# =====================================
class ElectricityPayment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    meter_type = models.CharField(max_length=20)
    meter_number = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    contact_number = models.CharField(max_length=11)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Electricity Payment {self.id} by {self.user.username}"


# =====================================
# CABLE TV SUBSCRIPTIONS
# =====================================
from django.db import models
from django.contrib.auth.models import User

class DstvSubscription(models.Model):
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

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES)
    smart_card_number = models.CharField(max_length=30)
    package = models.CharField(max_length=20, choices=DSTV_PACKAGES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - DSTV - {self.package}"


class GoTVSubscription(models.Model):
    CUSTOMER_TYPES = DstvSubscription.CUSTOMER_TYPES

    GOTV_PACKAGES = [
        ('supa_plus', 'Supa+ - ₦5,500'),
        ('supa', 'Supa - ₦4,500'),
        ('max', 'Max - ₦3,200'),
        ('jolli', 'Jolli - ₦2,460'),
        ('jinja', 'Jinja - ₦1,640'),
        ('smallie', 'Smallie - ₦800'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES)
    smart_card_number = models.CharField(max_length=30)
    package = models.CharField(max_length=20, choices=GOTV_PACKAGES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - GoTV - {self.package}"


class StarTimesSubscription(models.Model):
    CUSTOMER_TYPES = DstvSubscription.CUSTOMER_TYPES

    STARTIMES_PACKAGES = [
        ('nova_dish', 'Nova (dish) - ₦1,700'),
        ('nova_antenna', 'Nova (antenna) - ₦1,300'),
        ('basic', 'Basic - ₦2,500'),
        ('smart', 'Smart - ₦3,200'),
        ('classic', 'Classic - ₦4,500'),
        ('super', 'Super - ₦6,200'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES)
    smart_card_number = models.CharField(max_length=30)
    package = models.CharField(max_length=30, choices=STARTIMES_PACKAGES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - StarTimes - {self.package}"


# =====================================
# SCHOOL FEES PAYMENT
# =====================================
class SchoolFeesPayment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    student_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"School Fees Payment {self.id} by {self.user.username} for {self.student_name}"


# =====================================
# WAEC RESULT CHECK
# =====================================
class WaecResultCheck(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exam_number = models.CharField(max_length=20)
    exam_year = models.CharField(max_length=4)
    token_used = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"WAEC Result Check for {self.exam_number} by {self.user.username}"


# =====================================
# FLIGHT / AIRLINE BOOKINGS
# =====================================
class FlightBooking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='flight_bookings')
    departure_city = models.CharField(max_length=100)
    arrival_city = models.CharField(max_length=100)
    departure_date = models.DateField()
    return_date = models.DateField(blank=True, null=True)
    number_of_passengers = models.IntegerField()
    children = models.IntegerField(default=0)
    infants = models.IntegerField(default=0)
    contact_number = models.CharField(max_length=15)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.departure_city} to {self.arrival_city}"


# =====================================
# PAYSTACK TRANSACTION (FOR CARD PAYMENTS)
# =====================================
class PaystackTransaction(models.Model):
    reference = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paystack Transaction {self.reference} - {self.status}"


# =====================================
# LOAN APPLICATION
# =====================================
class LoanApplication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    term = models.IntegerField(help_text="Loan term in months")
    purpose = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Loan Application {self.id} by {self.user.username}"
    

class ServicePayment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='service_payment')
    service_name = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_name} - {self.amount}"
