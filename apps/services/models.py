from django.db import models
from django.conf import settings




class ServicePayment(models.Model):
    service_name = models.CharField(max_length=100, help_text="Name of the service being paid for")
    customer_name = models.CharField(max_length=100, help_text="Name of the customer")
    phone_number = models.CharField(max_length=15, help_text="Customer's phone number")
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount paid for the service")
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_name} - {self.customer_name}"



# Service Model for defining different types of services
class Service(models.Model):
    SERVICE_TYPES = [
        ('airtime', 'Airtime Recharge'),
        ('data', 'Data Top-Up'),
        ('electricity', 'Electricity Bill'),
        ('cable_tv', 'Cable TV Bill'),
        ('flight', 'Flight Booking'),
    ]
    name = models.CharField(max_length=50)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)

    def __str__(self):
        return self.name

# Airtime Recharge Model
class AirtimeRecharge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='airtime_recharges')
    network_provider = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=[('wallet', 'Wallet'), ('debit_card', 'Debit Card')])
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.network_provider} - {self.amount}"

# Utility Bill Model
class UtilityBill(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='utility_bills')
    service_type = models.CharField(max_length=20)
    account_number = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    cable_provider = models.CharField(max_length=20, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=[('wallet', 'Wallet'), ('debit_card', 'Debit Card')])
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.service_type} - {self.amount}"

# Flight Booking Model
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
    payment_method = models.CharField(max_length=20, choices=[('wallet', 'Wallet'), ('debit_card', 'Debit Card')])
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.departure_city} to {self.arrival_city}"

# Data Top-Up Model
class DataTopUp(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='data_topups')
    network_provider = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=[('wallet', 'Wallet'), ('debit_card', 'Debit Card')])
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.network_provider} - {self.amount}"

# School Fees Payment Model
class SchoolFeesPayment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    student_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=[('wallet', 'Wallet'), ('debit_card', 'Debit Card')])
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"School Fees Payment {self.id} by {self.user.username} for {self.student_name}"


# Loan Application Model
class LoanApplication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    term = models.IntegerField()  # Loan term in months
    purpose = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Loan Application {self.id} by {self.user.username}"

# Data Purchase Model
class DataPurchase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.CharField(max_length=20)
    data_plan = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=11)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Data Purchase {self.id} by {self.user.username}"

# Airline Booking Model
class AirlineBooking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    departure_location = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    departure_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    number_of_passengers = models.IntegerField()
    contact_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Airline Booking {self.id} by {self.user.username}"

# Electricity Payment Model
class ElectricityPayment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    meter_type = models.CharField(max_length=20)
    meter_number = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    contact_number = models.CharField(max_length=11)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Electricity Payment {self.id} by {self.user.username}"

# Dstv Subscription Model
class DstvSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    customer_type = models.CharField(max_length=20)
    smart_card_number = models.CharField(max_length=30)
    package = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"DSTV Subscription {self.id} by {self.user.username}"

# GoTV Subscription Model
class GoTVSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    customer_type = models.CharField(max_length=20)
    smart_card_number = models.CharField(max_length=30)
    package = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"GoTV Subscription {self.id} by {self.user.username}"

# StarTimes Subscription Model
class StarTimesSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    customer_type = models.CharField(max_length=20)
    smart_card_number = models.CharField(max_length=30)
    package = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"StarTimes Subscription {self.id} by {self.user.username}"


from django.db import models
from django.conf import settings


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wallet({self.user.username})"  # Ensure it returns a recognizable but safe format

from django.db import models
from django.urls import reverse
from django.utils.text import slugify

class Service(models.Model):
    SERVICE_CATEGORIES = [
        ('manage_fund', 'Manage Fund'),
        ('airtime_data', 'Airtime & Data'),
        ('utility_bill', 'Utility Bill'),
        ('school_fees', 'School Fees'),
        ('flight_booking', 'Flight Booking'),
    ]

    name = models.CharField(max_length=50, unique=True, verbose_name="Service Name")
    category = models.CharField(max_length=20, choices=SERVICE_CATEGORIES, verbose_name="Category")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Slug")  # Still auto-generated but optional
    service_url = models.URLField(blank=True, null=True, verbose_name="Service URL")  

    def save(self, *args, **kwargs):
        """ Auto-generate a unique slug if not provided """
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Service.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """ Return service URL if provided, otherwise detail page using ID """
        if self.service_url:
            return self.service_url
        return reverse("services:service_detail", kwargs={"id": self.id})  # Uses ID instead of slug

    def __str__(self):
        return self.name



# Airtime & Data Recharge Model
class AirtimeRecharge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='airtime_recharges')
    network_provider = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=[('wallet', 'Wallet'), ('debit_card', 'Debit Card')])
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.network_provider} - {self.amount}"

# Utility Bill Model
class UtilityBill(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='utility_bills')
    service_type = models.CharField(max_length=20)
    account_number = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    cable_provider = models.CharField(max_length=20, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=[('wallet', 'Wallet'), ('debit_card', 'Debit Card')])
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.service_type} - {self.amount}"

# School Fees Payment Model
class SchoolFeesPayment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    student_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=[('wallet', 'Wallet'), ('debit_card', 'Debit Card')])
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"School Fees Payment {self.id} by {self.user.username} for {self.student_name}"

# Flight Booking Model
class FlightBooking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='flight_bookings')
    departure_city = models.CharField(max_length=100)
    arrival_city = models.CharField(max_length=100)
    departure_date = models.DateField()
    return_date = models.DateField(blank=True, null=True)
    number_of_passengers = models.IntegerField()
    contact_number = models.CharField(max_length=15)
    payment_method = models.CharField(max_length=20, choices=[('wallet', 'Wallet'), ('debit_card', 'Debit Card')])
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.departure_city} to {self.arrival_city}"

