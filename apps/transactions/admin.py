from django.contrib import admin
from .models import Transaction, Payment, Wallet, Profile, Bank, TransferRecipient, BankTransfer, WalletTransfer


# Admin for Transaction
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'status', 'amount', 'created_at')
    list_filter = ('status',)
    search_fields = ('transaction_id', 'status')
    ordering = ('-created_at',)

    def transaction_id(self, obj):
        return obj.id  # Adjust if transaction_id is a different field
    transaction_id.short_description = 'Transaction ID'


# Admin for Payment
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'payment_method', 'date')
    search_fields = ('id', 'payment_method')
    ordering = ('-date',)


# Admin for Wallet
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('get_user_email', 'balance', 'created_at')
    search_fields = ('user__email', 'user__username')
    ordering = ('-balance',)

    def get_user_email(self, obj):
        return obj.user.email  # Display the user's email
    get_user_email.short_description = 'User Email'


# Admin for Profile
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_first_name', 'get_last_name', 'wallet_balance', 'created_at')  # Added 'created_at'
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    ordering = ('user__email',)

    def wallet_balance(self, obj):
        return obj.wallet.balance if hasattr(obj, 'wallet') else "N/A"
    wallet_balance.short_description = 'Wallet Balance'

    def get_first_name(self, obj):
        return obj.user.first_name  # Display the user's first name
    get_first_name.short_description = 'First Name'

    def get_last_name(self, obj):
        return obj.user.last_name  # Display the user's last name
    get_last_name.short_description = 'Last Name'


# Admin for Bank
@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']  # Removed created_at if not present


# Admin for TransferRecipient
@admin.register(TransferRecipient)
class TransferRecipientAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'bank', 'account_number', 'account_name')
    list_filter = ('bank',)
    search_fields = ('user__username', 'account_number')
    ordering = ('-created_at',)


# Admin for BankTransfer
@admin.register(BankTransfer)
class BankTransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_sender', 'get_recipient', 'amount', 'get_bank_code', 'transfer_date', 'status')
    list_filter = ('status',)
    search_fields = ('sender__username', 'recipient__username', 'bank_code')
    ordering = ('-transfer_date',)

    def get_sender(self, obj):
        return obj.sender.username if obj.sender else "N/A"
    get_sender.short_description = 'Sender'

    def get_recipient(self, obj):
        return obj.recipient.username if obj.recipient else "N/A"
    get_recipient.short_description = 'Recipient'

    def get_bank_code(self, obj):
        return obj.bank_code if obj.bank_code else "N/A"
    get_bank_code.short_description = 'Bank Code'





@admin.register(WalletTransfer)
class WalletTransferAdmin(admin.ModelAdmin):
    # Display relevant fields in the admin list view
    list_display = ('id', 'sender_username', 'recipient_wallet_id', 'amount', 'transfer_note', 'transfer_date', 'status')
    list_filter = ('status',)  # Filter by transaction status
    search_fields = ('sender__username', 'recipient_wallet_id')  # Enable search by sender username and recipient_wallet_id
    ordering = ('-transfer_date',)  # Order the records by transfer_date descending

    def sender_username(self, obj):
        return obj.sender.username if obj.sender else "N/A"  # Safely return sender's username
    sender_username.short_description = 'Sender Username'  # Add a readable name for the sender column

