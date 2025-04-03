from django.contrib import admin
from .models import (
    Profile, ServiceType, Bank, UserBank, Wallet, Transfer,
    PaystackTransaction, Transaction, DebitCard, Payment, TransferRecipient
)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'gender', 'created_at')
    search_fields = ('user__username', 'phone_number')

@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(UserBank)
class UserBankAdmin(admin.ModelAdmin):
    list_display = ('user', 'bank', 'account_number')
    search_fields = ('user__username', 'account_number')

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'created_at')
    search_fields = ('user__username',)

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('sender_wallet', 'recipient_wallet', 'amount', 'status', 'transfer_date')
    search_fields = ('sender_wallet__user__username', 'recipient_wallet__user__username', 'transaction_reference')
    list_filter = ('status', 'transfer_date')

@admin.register(PaystackTransaction)
class PaystackTransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'status', 'amount', 'created_at')
    search_fields = ('reference',)
    list_filter = ('status', 'created_at')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'amount', 'payment_method', 'date_created')
    search_fields = ('user__username', 'service__name')
    list_filter = ('payment_method', 'date_created')

@admin.register(DebitCard)
class DebitCardAdmin(admin.ModelAdmin):
    list_display = ('user', 'card_number', 'expiry_date', 'is_active')
    search_fields = ('user__username', 'card_number')
    list_filter = ('is_active', 'expiry_date')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'status', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('status', 'created_at')

@admin.register(TransferRecipient)
class TransferRecipientAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipient_name', 'bank_name', 'account_number')
    search_fields = ('user__username', 'recipient_name', 'bank_name', 'account_number')
