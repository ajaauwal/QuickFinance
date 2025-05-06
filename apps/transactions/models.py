from django.conf import settings
from django.db import models
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet
from django.contrib.auth.models import User



GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
    ('N', 'Prefer not to say'),
]

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, null=True, blank=True, verbose_name="Phone Number")
    address = models.TextField(null=True, blank=True, verbose_name="Address")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Date of Birth")
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True, verbose_name="Profile Picture")
    gender = models.CharField(max_length=17, choices=GENDER_CHOICES, null=True, blank=True, verbose_name="Gender")
    wallet_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Wallet Balance")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def update_profile(self, phone_number=None, address=None, date_of_birth=None, profile_picture=None, gender=None):
        """Update user profile details."""
        if phone_number:
            self.phone_number = phone_number
        if address:
            self.address = address
        if date_of_birth:
            self.date_of_birth = date_of_birth
        if profile_picture:
            self.profile_picture = profile_picture
        if gender:
            self.gender = gender
        self.save()

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

from django.db import models
from django.conf import settings
from apps.services.models import Service
import random
from decimal import Decimal


def generate_wallet_id():
    """Generate a unique 10-digit wallet ID."""
    while True:
        wallet_id = random.randint(1000000000, 9999999999)  # 10-digit number
        if not Wallet.objects.filter(wallet_id=wallet_id).exists():
            return wallet_id


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    wallet_id = models.BigIntegerField(unique=True, default=generate_wallet_id)  # Unique wallet ID
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Wallet for {self.user.username} with ID: {self.wallet_id}"

    def deposit(self, amount):
        """Deposit funds into the wallet."""
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than zero.")
        
        self.balance += Decimal(amount)
        self.save()
        return self.balance

    def withdraw(self, amount):
        """Withdraw funds from the wallet."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than zero.")
        
        if self.balance < Decimal(amount):
            raise ValueError("Insufficient funds in wallet.")
        
        self.balance -= Decimal(amount)
        self.save()
        return self.balance

    def get_balance(self):
        """Return the current balance of the wallet."""
        return self.balance


import uuid  # Ensure uuid is imported
from django.db import models
from django.conf import settings

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    SERVICE_TYPES = [
        ('airtime', 'Airtime'),
        ('data', 'Data'),
        ('tv', 'TV Subscription'),
        ('electricity', 'Electricity Payment'),
        ('school_fees', 'School Fees Payment'),
        ('waec', 'WAEC Result Check'),
        ('wallet_to_wallet', 'Wallet to Wallet Transfer'),
        ('wallet_to_bank', 'Wallet to Bank Transfer'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    wallet = models.ForeignKey('Wallet', on_delete=models.CASCADE, null=True, blank=True)  # Wallet initiating the transaction

    # Recipient details (for wallet-to-bank)
    recipient_name = models.CharField(max_length=150, null=True, blank=True)
    account_number = models.CharField(max_length=20, null=True, blank=True)
    bank_code = models.CharField(max_length=20, null=True, blank=True)
    bank_name = models.CharField(max_length=100, null=True, blank=True)

    # Recipient details (for wallet-to-wallet)
    recipient_wallet_id = models.CharField(max_length=20, null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES)

    # Transaction metadata
    external_id = models.CharField(max_length=100, unique=True, editable=False)
    transaction_id = models.CharField(max_length=100, unique=True, editable=False, blank=True)
    reference = models.CharField(max_length=100, unique=True, editable=False, blank=True)
    transaction_reference = models.CharField(max_length=100, unique=True, editable=False, blank=True)
    transfer_note = models.CharField(max_length=255, null=True, blank=True)
    confirm_transfer = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)  # ✅ Fixed: this is the correct way

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Ensure the wallet exists before saving
        if self.wallet and not Wallet.objects.filter(id=self.wallet.id).exists():
            raise ValueError("The referenced wallet does not exist.")

        # Generate unique identifiers if not provided
        if not self.external_id:
            self.external_id = uuid.uuid4().hex
        if not self.transaction_id:
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
        if not self.reference:
            self.reference = uuid.uuid4().hex
        if not self.transaction_reference:
            self.transaction_reference = f"TR-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.service_type} - {self.status}"





class Bank(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set when an instance is created

    def __str__(self):
        return self.name

# models.py
class UserBank(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=255)
    bank_code = models.CharField(max_length=10)

    def get_balance(self):
        # Assume you store balance
        return Decimal('5000.00')
    


from django.db import models
from django.contrib.auth.models import User

class Transfer(models.Model):
    TRANSFER_TYPE_CHOICES = (
        ('wallet', 'Wallet Transfer'),
        ('bank', 'Bank Transfer'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    related_id = models.PositiveIntegerField(help_text="ID of WalletTransfer or BankTransfer")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_transfer_type_display()} | {self.user.username} | {self.amount}"



class BankTransfer(models.Model):
    sender_wallet = models.ForeignKey('Wallet', related_name='sent_transfers', on_delete=models.CASCADE)
    recipient_wallet = models.ForeignKey('Wallet', related_name='received_transfers', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_reference = models.CharField(max_length=100, unique=True)
    transfer_date = models.DateTimeField(auto_now_add=True)
    transfer_note = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed')],
        default='PENDING'
    )
    currency = models.CharField(max_length=3, default='USD')
    fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Transfer of {self.amount} {self.currency} from {self.sender_wallet.user.username} to {self.recipient_wallet.user.username}"

    def save(self, *args, **kwargs):
        if self.amount <= Decimal('0'):
            raise ValueError("Amount must be greater than zero.")
        if self.sender_wallet.balance < self.amount + self.fee:
            raise ValueError("Insufficient balance in the sender's wallet.")
        super(BankTransfer, self).save(*args, **kwargs)
        self.sender_wallet.balance -= (self.amount + self.fee)
        self.sender_wallet.save()
        self.recipient_wallet.balance += self.amount
        self.recipient_wallet.save()


from django.db import models
from django.contrib.auth.models import User

class WalletTransfer(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='sent_wallet_transfers'
    )
    recipient_wallet_id = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transfer_note = models.TextField(blank=True, null=True)
    transfer_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending')

    def __str__(self):
        return f"Transfer from {self.sender.username} to {self.recipient_wallet_id} - {self.status}"

    class Meta:
        verbose_name = 'Wallet Transfer'
        verbose_name_plural = 'Wallet Transfers'
        ordering = ['-transfer_date']



class TransferRecipient(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='recipients')
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account_name} ({self.account_number}) - {self.bank.name}"


class Payment(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} by {self.user}"

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
        if len(self.card_number) != 16:
            raise ValidationError("Card number must be 16 digits.")
        if len(self.cvv) != 3:
            raise ValidationError("CVV must be 3 digits.")

    def encrypt_sensitive_data(self):
        cipher_suite = Fernet('your_secret_key')
        self.card_number = cipher_suite.encrypt(self.card_number.encode()).decode()
        self.cvv = cipher_suite.encrypt(self.cvv.encode()).decode()

    def decrypt_sensitive_data(self):
        cipher_suite = Fernet('your_secret_key')
        self.card_number = cipher_suite.decrypt(self.card_number.encode()).decode()
        self.cvv = cipher_suite.decrypt(self.cvv.encode()).decode()


