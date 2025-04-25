from django.conf import settings
from django.db import models
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet
from django.contrib.auth.models import User



# Gender choices for profile
GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('non_binary', 'Non-binary'),
    ('prefer_not_to_say', 'Prefer not to say'),
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
        app_label = 'transactions'  # Ensure app label is correct

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Wallet Balance: {self.balance}"

    class Meta:
        app_label = 'transactions'  # Ensure app label is correct

class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)  # Direct reference to Wallet model
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100)

    def __str__(self):
        return f"Transaction {self.id} by {self.user.username}"

    class Meta:
        app_label = 'transactions'  # Ensure app label is correct




class ServiceType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Bank(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set when an instance is created

    def __str__(self):
        return self.name

class Bank(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)

    def __str__(self):
        return self.name

class UserBank(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.account_name} ({self.bank.name})"


class Transfer(models.Model):
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
        super(Transfer, self).save(*args, **kwargs)
        self.sender_wallet.balance -= (self.amount + self.fee)
        self.sender_wallet.save()
        self.recipient_wallet.balance += self.amount
        self.recipient_wallet.save()

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