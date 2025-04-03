from django.urls import path
from . import views
from .views import (
    record_transaction,
    bank_selection_view,
    process_bank_view,
    WalletView,
    ProfileView,
    PaymentInitiateView,
    TransactionListView,
    paystack_payment,
    paystack_callback,
    update_profile,
    update_user_wallet_balance,
    get_wallet_balance,
    change_password,
    transfer,
    transfer_success,
    success_page,
    wallet_balance,
    pay_with_debit_card,  # Added this to the imports
)

app_name = 'transactions'

urlpatterns = [
    # Transaction-related views
    path('history/', views.transaction_history, name='transaction_history'),
    path('create/', views.create_transaction_view, name='create_transaction'),
    path('<int:transaction_id>/', views.transaction_detail_view, name='transaction_detail'),
    path('<int:transaction_id>/update-status/', views.update_transaction_status_view, name='update_transaction_status'),
    path('verify/<str:reference>/', views.verify_transaction, name='verify_transaction'),
    path('initiate-payment/', PaymentInitiateView.as_view(), name='initiate_payment'),

    # Payment and fund management views
    path('transfer/', transfer, name='transfer'),
    path('success/page/', success_page, name='success_page'),
    path('transfer/success/', transfer_success, name='transfer_success'),
    path('process-wallet-payment/', views.process_wallet_payment, name='process_wallet_payment'),
    path('payment-with-debit-card/', pay_with_debit_card, name='pay_with_debit_card'),  # Updated this
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('manage-fund/', views.manage_fund, name='manage_fund'),
    path('add-money/', views.add_money, name='add_money'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('record-transaction/', record_transaction, name='record_transaction'),

    # Corrected wallet balance route
    path('wallet/balance/', wallet_balance, name='wallet_balance'),

    # Bank-related views
    path('select-bank/', bank_selection_view, name='bank_selection'),
    path('select-bank/<int:bank_id>/', views.select_bank, name='select_bank'),
    path('process-bank/<str:bank>/', process_bank_view, name='process_bank'),
    path('transaction-form/<int:bank_id>/', views.transaction_form, name='transaction_form'),
    path('transaction-success/<int:transaction_id>/', views.transaction_success, name='transaction_success'),

    # Payment and transaction paths
    path('transactions/list/', TransactionListView.as_view(), name='transaction_list'),
    path('payments/paystack/', paystack_payment, name='paystack_payment'),
    path('payments/callback/', paystack_callback, name='paystack_callback'),

    # Miscellaneous views
    path('transaction/', views.transaction_view, name='transaction'),
    path('wallet/', WalletView.as_view(), name='wallet'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('update-profile/', update_profile, name='update_profile'),
    path('change-password/', change_password, name='change_password'),
    path('api/get_wallet_balance/', get_wallet_balance, name='get_wallet_balance'),
    path('update-user-wallet-balance/<str:amount>/', update_user_wallet_balance, name='update_user_wallet_balance'),
]
