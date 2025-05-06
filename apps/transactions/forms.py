from django import forms
from django.apps import apps
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Profile
from apps.services.models import Service
from .validators import validate_positive_amount


User = get_user_model()

# Validators
def validate_positive_amount(value):
    if value <= Decimal("0.00"):
        raise ValidationError(_("Amount must be greater than zero."))
    return value

# Define BANK_CHOICES at the module level (alphabetized for clarity)
BANK_CHOICES = [
    ("ABNGNGA", "Access Bank"),
    ("CARBONGH", "Carbon Bank"),
    ("ECOBANKNG", "Ecobank"),
    ("EYOWO", "Eyowo"),
    ("FCMBNGNG", "FCMB"),
    ("FBNGNNG", "Fidelity Bank"),
    ("FBNNGNG", "First Bank"),
    ("GLOBUSBANK", "Globus Bank"),
    ("GTBNGNGA", "GTB"),
    ("JAIZBANKNG", "Jaiz Bank"),
    ("KEYSTONE", "Keystone Bank"),
    ("KUDAMFNB", "Kuda Bank"),
    ("LOTUSBANK", "Lotus Bank"),
    ("MINTBANK", "Mint Bank"),
    ("MONIEPOINT", "MoniePoint"),
    ("OPAYNG", "Opay"),
    ("OPAYPAYCOM", "Paycom"),
    ("PALMPAY", "PalmPay"),
    ("PARALLEX", "Parallex Bank"),
    ("POLARISNG", "Polaris Bank"),
    ("PROVIDUSBANK", "Providus Bank"),
    ("RMBNG", "Rand Merchant Bank"),
    ("RUBIESBANK", "Rubies Bank"),
    ("SBINNG", "Stanbic IBTC"),
    ("SCBNA", "Standard Chartered Bank"),
    ("STERLINGNG", "Sterling Bank"),
    ("STBNAFRICA", "Suntrust Bank"),
    ("TAJNG", "Taj Bank"),
    ("UBANGNG", "UBA"),
    ("UNIONNGB", "Union Bank"),
    ("UNITYBANK", "Unity Bank"),
    ("VFDMICRO", "VFD Microfinance Bank"),
    ("WEMANG", "Wema Bank"),
    ("ZENITHNG", "Zenith Bank"),
]


from django import forms
from .validators import validate_positive_amount  # Assuming you have a custom validator

class BankTransferForm(forms.Form):
   
    account_number = forms.CharField(
        max_length=20,
        required=True,
        label="Recipient Account Number",
        widget=forms.TextInput(attrs={'placeholder': 'Enter Account Number'})
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        label="Amount",
        validators=[validate_positive_amount],
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Amount'})
    )
    transfer_note = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Add a note (optional)', 'rows': 3}),
        required=False,
        label="Transfer Note (optional)"
    )
    recipient_name = forms.CharField(
        max_length=255,
        required=True,
        label="Recipient Name",
        widget=forms.TextInput(attrs={'placeholder': 'Enter Recipient Name'})
    )
    transaction_reference = forms.CharField(
        max_length=100,
        required=True,
        label="Transaction Reference",
        widget=forms.TextInput(attrs={'placeholder': 'Auto-generated or custom reference'})
    )
    transfer_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Transfer Date"
    )
    currency = forms.ChoiceField(
        choices=[('NGN', 'NGN'), ('EUR', 'EUR'), ('USD', 'USD'), ('GBP', 'GBP')],
        initial='NGN',
        required=True,
        label="Currency"
    )
    recipient_phone = forms.CharField(
        max_length=15,
        required=False,
        label="Recipient Phone Number",
        widget=forms.TextInput(attrs={'placeholder': 'Optional'})
    )
    recipient_email = forms.EmailField(
        required=False,
        label="Recipient Email",
        widget=forms.EmailInput(attrs={'placeholder': 'Optional'})
    )
    confirm_transfer = forms.BooleanField(
        required=True,
        label="I confirm that the transfer details are correct"
    )
    bank_code = forms.ChoiceField(
        choices=[('', 'Select a Bank')] + BANK_CHOICES,  # Make sure BANK_CHOICES is defined
        required=True,
        label="Bank"
    )


from django import forms
from .models import WalletTransfer

class WalletTransferForm(forms.ModelForm):
    class Meta:
        model = WalletTransfer
        fields = ['wallet_id', 'amount', 'transfer_note']

    wallet_id = forms.CharField(
        max_length=30,
        required=True,
        label="Recipient Wallet ID",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Wallet ID'})
    )
    
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'})
    )
    
    transfer_note = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Optional transfer note', 'rows': 3}),
        required=False
    )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

    def clean_wallet_id(self):
        wallet_id = self.cleaned_data.get('wallet_id')
        if not wallet_id:
            raise forms.ValidationError("Wallet ID is required.")
        return wallet_id



class AddMoneyForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        from .models import Transaction  # Import models locally to avoid circular import
        transaction = super().save(commit=False)
        transaction.user = self.user
        if commit:
            transaction.save()
        return transaction


class TransactionForm(forms.ModelForm):
    # Transaction model fields
    bank = forms.ChoiceField(choices=BANK_CHOICES, label='Select Bank', widget=forms.Select(attrs={'class': 'form-control'}))
    amount = forms.DecimalField(max_digits=10, decimal_places=2, label='Amount', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    transaction_type = forms.ChoiceField(choices=[('credit', 'Credit'), ('debit', 'Debit')], label='Transaction Type', widget=forms.Select(attrs={'class': 'form-control'}))
    transaction_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}))
    description = forms.CharField(max_length=255, required=False, label='Description', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))

    class Meta:
        model = None  # This will be set dynamically in a method later
        fields = ['bank', 'amount', 'transaction_type', 'transaction_date', 'description']

    @classmethod
    def set_model(cls):
        # Dynamically assign the model once the app registry is ready
        cls.Meta.model = apps.get_model('transactions', 'Transaction')

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description:
            raise forms.ValidationError("Please provide a description.")
        return description



# Function to validate positive amount
def validate_positive_amount(amount):
    if amount <= 0:
        raise ValidationError("Amount must be greater than zero.")
    return amount

class PaymentForm(forms.Form):
    service = forms.ModelChoiceField(queryset=Service.objects.all(), required=True, label="Select Service")
    amount = forms.DecimalField(max_digits=10, decimal_places=2, required=True, label="Amount")
    payment_method = forms.ChoiceField(
        choices=[('credit_card', 'Credit Card'), ('debit_card', 'Debit Card'), ('wallet', 'Wallet')],
        required=True,
        label="Payment Method"
    )
    card_number = forms.CharField(max_length=16, required=False, label="Card Number", widget=forms.TextInput(attrs={'placeholder': 'XXXX-XXXX-XXXX-XXXX'}))
    expiry_date = forms.DateField(required=False, label="Expiry Date", widget=forms.DateInput(attrs={'type': 'month'}))
    cvv = forms.CharField(max_length=3, required=False, label="CVV", widget=forms.TextInput(attrs={'placeholder': 'XXX'}))
    wallet_balance = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Wallet Balance", disabled=True)
    description = forms.CharField(widget=forms.Textarea, required=False, label="Payment Description")
    user_email = forms.EmailField(required=True, label="User Email")
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        return validate_positive_amount(amount)
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        amount = cleaned_data.get('amount')
        
        # If payment method is wallet, validate sufficient balance
        if payment_method == 'wallet':
            wallet_balance = cleaned_data.get('wallet_balance', 0)
            if wallet_balance < amount:
                raise ValidationError("Insufficient balance in wallet.")
        
        return cleaned_data




class ProfileForm(forms.ModelForm):
    # Personal Information
    surname = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Surname'})
    )
    other_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Other Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    gender = forms.ChoiceField(
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    registration_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Registration Number'})
    )
    school = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'School'})
    )
    department = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'})
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    # Address Information
    country = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'})
    )
    state = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'})
    )
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'})
    )
    address_line_1 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1'})
    )
    address_line_2 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 2'})
    )

    class Meta:
        model = Profile
        fields = [
            'surname', 'other_name', 'email', 'phone', 'gender', 'registration_number',
            'school', 'department', 'date_of_birth', 'country', 'state', 'city',
            'address_line_1', 'address_line_2',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'user'):
            user = self.instance.user
            self.fields['email'].initial = user.email
            self.fields['phone'].initial = getattr(user, 'phone', '')

    def clean_email(self):
        """Custom validation for email field."""
        email = self.cleaned_data.get('email')
        if email and not email.endswith('@example.com'):
            raise ValidationError('Email must end with @example.com')
        return email

    def save(self, commit=True):
        """Override save to update the related user model."""
        profile = super().save(commit=False)
        if hasattr(profile, 'user'):
            user = profile.user
            user.email = self.cleaned_data['email']
            user.phone = self.cleaned_data.get('phone', '')
            if commit:
                user.save()
        if commit:
            profile.save()
        return profile


class WalletForm(forms.ModelForm):
    class Meta:
        model = None  # Set to None initially
        fields = ['balance', 'user']
        widgets = {
            'balance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter balance'}),
            'user': forms.HiddenInput(),
        }

    def _set_model(self):
        # Dynamically import the Wallet model after app registry is ready
        self._meta.model = apps.get_model('transactions', 'Wallet')

    def clean_balance(self):
        balance = self.cleaned_data.get('balance')
        if balance < 0:
            raise forms.ValidationError("Balance cannot be negative.")
        return balance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_model()

class PayWithWalletForm(forms.Form):
    service = forms.ModelChoiceField(queryset=Service.objects.all(), required=True, label="Select Service")
    amount = forms.DecimalField(max_digits=10, decimal_places=2, required=True, label="Amount")

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        return self.validate_positive_amount(amount)

    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get('service')
        amount = cleaned_data.get('amount')
        from .models import Wallet  # Import models locally to avoid circular import
        wallet = Wallet.objects.get(user=self.initial.get('user'))
        if wallet.balance < amount:
            raise ValidationError("Insufficient balance in wallet for this transaction.")
        return cleaned_data

    def validate_positive_amount(self, amount):
        if amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        return amount



class BankForm(forms.Form):
    bank_name = forms.ChoiceField(choices=BANK_CHOICES, required=True, label="Select Bank")
    account_number = forms.CharField(max_length=10, label="Account Number")
    amount = forms.DecimalField(max_digits=12, decimal_places=2, label="Amount")
    narration = forms.CharField(max_length=100, required=False, label="Narration")

    def clean_amount(self):
        return self.validate_positive_amount(self.cleaned_data.get('amount'))

    def validate_positive_amount(self, amount):
        if amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        return amount

class BankTransferForm(forms.Form):
    bank = forms.ChoiceField(choices=BANK_CHOICES, label="Select Bank")
    recipient_account = forms.CharField(max_length=30, label="Recipient Account")
    amount = forms.DecimalField(max_digits=10, decimal_places=2, label="Amount")

class TransfermoneyForm(forms.Form):
    bank_name = forms.ChoiceField(choices=BANK_CHOICES)
    account_number = forms.CharField(max_length=10)
    account_name = forms.CharField(max_length=100)
    amount = forms.DecimalField(max_digits=12, decimal_places=2)
    description = forms.CharField(widget=forms.Textarea, required=False)

class PayWithDebitCardForm(forms.Form):
    service = forms.ModelChoiceField(queryset=Service.objects.all(), required=True, label="Select Service")
    amount = forms.DecimalField(max_digits=10, decimal_places=2, required=True, label="Amount")
    card_number = forms.CharField(max_length=16, required=True, label="Debit Card Number", widget=forms.TextInput(attrs={'placeholder': 'XXXX-XXXX-XXXX-XXXX'}))
    expiry_date = forms.DateField(required=True, label="Expiry Date", widget=forms.DateInput(attrs={'type': 'month'}))
    cvv = forms.CharField(max_length=3, required=True, label="CVV", widget=forms.TextInput(attrs={'placeholder': 'XXX'}))

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        return self.validate_positive_amount(amount)

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        if amount > Decimal('10000.00'):
            raise ValidationError("Amount exceeds the allowed limit for card payments.")
        return cleaned_data
