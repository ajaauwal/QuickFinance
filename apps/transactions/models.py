from django.conf import settings
from django.db import models
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet
from django.contrib.auth.models import User
from apps.services.models import Service

# Gender choices for profile
GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
    ('prefer_not_to_say', 'Prefer not to say'),
]

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    gender = models.CharField(max_length=17, choices=GENDER_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"



class Bank(models.Model):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.name

class UserBank(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=20, unique=True)
    account_name = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.account_name} ({self.bank.name})"

from decimal import Decimal
from django.db import models
from django.conf import settings

class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='wallet_service'  # Updated related_name to avoid conflicts
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - Wallet Balance: {self.balance}"

    def add_funds(self, amount):
        self.balance += Decimal(amount)
        self.save()

    def withdraw_funds(self, amount):
        amount = Decimal(amount)
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False
    
    
class Transfer(models.Model):
    sender_wallet = models.ForeignKey(Wallet, related_name='sent_transfers', on_delete=models.CASCADE)
    recipient_wallet = models.ForeignKey(Wallet, related_name='received_transfers', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_reference = models.CharField(max_length=100, unique=True)
    transfer_date = models.DateTimeField(auto_now_add=True)
    transfer_note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('PENDING', 'Pending'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed')], default='PENDING')
    currency = models.CharField(max_length=3, default='USD')
    fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    
    def __str__(self):
        return f"Transfer of {self.amount} {self.currency} from {self.sender_wallet.user.username} to {self.recipient_wallet.user.username}"

class PaystackTransaction(models.Model):
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Paystack Transaction {self.reference} - {self.status}"

class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=[('wallet', 'Wallet'), ('debit_card', 'Debit Card')])
    date_created = models.DateTimeField(auto_now_add=True)  # Keep this for the timestamp
    wallet = models.ForeignKey(Wallet, null=True, blank=True, on_delete=models.SET_NULL, related_name='transactions')
    paystack_transaction = models.ForeignKey(PaystackTransaction, null=True, blank=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return f"{self.user.username} - {self.service.name} - {self.amount}"

class DebitCard(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    card_number = models.CharField(max_length=16, unique=True)
    expiry_date = models.DateField()
    cvv = models.CharField(max_length=3)
    cardholder_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Debit Card ending in {self.card_number[-4:]}"

    def clean(self):
        if self.expiry_date < timezone.now().date():
            raise ValidationError("The card has expired.")

class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed')])
    created_at = models.DateTimeField(auto_now_add=True)

class TransferRecipient(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    recipient_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.recipient_name} - {self.bank_name}"


from django.db import models

class ServiceType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name="services")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
