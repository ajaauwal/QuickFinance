from django.contrib import admin
from .models import Transaction, Payment, Wallet, Profile, Bank, TransferRecipient, Transfer


from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    # List display fields, ensure they match fields or methods in your Transaction model
    list_display = ('transaction_id', 'status', 'amount', 'created_at')  
    
    # Filter options for the admin panel
    list_filter = ('status',)  
    
    # Fields that can be searched within the admin interface
    search_fields = ('transaction_id', 'status')  
    
    # Default ordering in the admin panel
    ordering = ('-created_at',)  

    # If transaction_id is a method, define it as a method within the admin class
    def transaction_id(self, obj):
        return obj.id  # Adjust if transaction_id is a different field
    transaction_id.short_description = 'Transaction ID'  # Optional: Add description for the list display



# Admin for Payment
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'payment_method', 'date')  # Adjusted to actual field names
    search_fields = ('id', 'payment_method')
    ordering = ('-date',)  # Ordering by actual 'date' field


# Admin for Wallet
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('get_user_email', 'balance', 'created_at')  # Show user email, balance, and created_at
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
    list_display = ('id', 'user', 'bank', 'account_number', 'account_name')  # Adjusted based on model fields
    list_filter = ('bank',)  # Adjusted to use the 'bank' field
    search_fields = ('user__username', 'account_number')
    ordering = ('-created_at',)


# Admin for Transfer
@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender_wallet', 'recipient_wallet', 'amount', 'transaction_reference', 'transfer_date', 'status')  # Adjusted to valid fields
    list_filter = ('status',)  # Added filter by status
    search_fields = ('transaction_reference', 'sender_wallet__user__username', 'recipient_wallet__user__username')  # Updated to valid fields
    ordering = ('-transfer_date',)  # Ordering by transfer_date instead of timestamp

    def get_user_email(self, obj):
        return obj.sender_wallet.user.email  # Display the sender's email
    get_user_email.short_description = 'Sender Email'

    def get_recipient_name(self, obj):
        return obj.recipient_wallet.user.first_name  # Display the recipient's first name
    get_recipient_name.short_description = 'Recipient Name'
