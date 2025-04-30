from django.urls import path
from . import views
from .views import (
    WalletView,
    ProfileView,
    TransactionListView,
    bank_selection_view,
    process_bank_view,
    initiate_payment,
    payment_callback,
    update_profile,
    update_user_wallet_balance,
    get_wallet_balance,
    change_password,
    transfer,
    transfer_success,
    success_page,
    wallet_balance,
    record_transaction,
    add_money,
    manage_fund,
    process_wallet_payment,
    process_debit_card_payment,
    verify_payment,
    transaction_history,
    create_transaction_view,
    transaction_detail_view,
    update_transaction_status_view,
    verify_transaction,
    select_bank,
    transaction_form,
    transaction_success,
    transaction_view,
    wallet_summary,
    transaction_history_json,  # <-- Ensure this exists
)

app_name = 'transactions'

urlpatterns = [
    # Transaction CRUD
    path('history/', transaction_history, name='transaction_history'),
    path('history/json/', transaction_history_json, name='transaction_history_json'),
    path('create/', create_transaction_view, name='create_transaction'),
    path('<int:transaction_id>/', transaction_detail_view, name='transaction_detail'),
    path('<int:transaction_id>/update-status/', update_transaction_status_view, name='update_transaction_status'),

    # Payment Initiation and Verification
    path('verify/<str:reference>/', verify_transaction, name='verify_transaction'),
    path('initiate-payment/', initiate_payment, name='initiate_payment'),  # Updated to function-based view
    path('verify-payment/', verify_payment, name='verify_payment'),

     path('api/deposit/initialize/', views.deposit_initialize, name='deposit_initialize'),
    path('api/deposit/verify/', views.deposit_verify, name='deposit_verify'),
    path('api/pay/service/', views.pay_for_service, name='pay_for_service'),

    # Wallet & Fund Management
    path('add-money/', add_money, name='add_money'),
    path('manage-fund/', manage_fund, name='manage_fund'),
    path('process-wallet-payment/', process_wallet_payment, name='process_wallet_payment'),
    path('process-debit-card-payment/', process_debit_card_payment, name='process_debit_card_payment'),
    path('wallet/balance/', wallet_balance, name='wallet_balance'),
    path('wallet/', WalletView.as_view(), name='wallet'),

    # Transaction Logging
    path('record-transaction/', record_transaction, name='record_transaction'),
    path('transaction/', transaction_view, name='transaction'),

    # Transfers
    path('transfer/', transfer, name='transfer'),
    path('transfer/success/', transfer_success, name='transfer_success'),
    # urls.py
    path('withdraw/', views.withdraw_to_bank, name='withdraw_to_bank'),


    # Bank Operations
    path('select-bank/', bank_selection_view, name='bank_selection'),
    path('select-bank/<int:bank_id>/', select_bank, name='select_bank'),
    path('process-bank/<str:bank>/', process_bank_view, name='process_bank'),
    path('transaction-form/<int:bank_id>/', transaction_form, name='transaction_form'),
    path('transaction-success/<int:transaction_id>/', transaction_success, name='transaction_success'),

    # Payment Gateways
    path('payment/callback/', payment_callback, name='payment_callback'),

    # User Profile & Settings
    path('profile/', ProfileView.as_view(), name='profile'),
    path('update-profile/', update_profile, name='update_profile'),
    path('change-password/', change_password, name='change_password'),
    path('api/get_wallet_balance/', get_wallet_balance, name='get_wallet_balance'),
    path('update-user-wallet-balance/<str:amount>/', update_user_wallet_balance, name='update_user_wallet_balance'),

    # Miscellaneous
    path('success/page/', success_page, name='success_page'),
    path('transactions/list/', TransactionListView.as_view(), name='transaction_list'),
    path('api/wallet-summary/', wallet_summary, name='wallet-summary'),
]
