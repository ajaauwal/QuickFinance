import os
import logging
import uuid  
import csv
import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
import time  
import environ
from rest_framework.decorators import api_view
from django.contrib.auth.forms import PasswordChangeForm
from .forms import TransactionForm, WalletForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.utils import timezone
from .models import Wallet, Payment, Transaction
from .forms import ProfileForm, AddMoneyForm, TransferForm, WalletForm, TransferForm
from decimal import Decimal, InvalidOperation
from dotenv import load_dotenv
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.views import View
import requests
from django.conf import settings
from .models import Wallet, Transaction,  Bank, Payment, TransferRecipient, Transfer
from apps.services.paystack import PaystackAPI
from apps.services.paystack import PaystackAPI
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import PayWithDebitCardForm
from .models import DebitCard, Wallet, Bank
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.core.cache import cache
from rest_framework import status
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import UserBank
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import requests
import logging
from .models import Payment
from .serializers import PaymentSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Transaction
from .serializers import TransactionSerializer
from .utils import update_user_wallet_balance  # Ensure this is correctly implemented as shown below




# Load environment variables
load_dotenv()

# Initialize the logger
logger = logging.getLogger(__name__)

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()

# Paystack configurations
PAYSTACK_SECRET_KEY = env("PAYSTACK_SECRET_KEY", default="")
PAYSTACK_PUBLIC_KEY = env("PAYSTACK_PUBLIC_KEY", default="")
PAYSTACK_BASE_URL = "https://api.paystack.com"

# Initialize Paystack API
paystack = PaystackAPI()

# Get the custom user model
User = get_user_model()


# Paystack Payment Integration
def paystack_payment(request):
    if request.method == "POST":
        amount = request.POST.get('amount')
        email = request.POST.get('email')

        if not amount or not email:
            return JsonResponse({"error": "Missing amount or email"}, status=400)

        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "email": email,
            "amount": int(amount),  # Amount should already be in kobo (cent precision)
            "callback_url": "http://127.0.0.1:8000/paystack-callback",
        }

        try:
            response = requests.post(f"{PAYSTACK_BASE_URL}/transaction/initialize", json=payload, headers=headers)
            if response.status_code == 200:
                authorization_url = response.json()['data']['authorization_url']
                return redirect(authorization_url)
            return JsonResponse({"error": "Failed to initialize payment"}, status=response.status_code)
        except Exception as e:
            logger.error(f"Error during Paystack payment initialization: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    return render(request, 'paystack_payment.html')


@login_required
def transaction_view(request):
    """View to display the transaction form and handle transaction creation."""
    wallet = get_object_or_404(Wallet, user=request.user)

    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.wallet = wallet  # Associate the transaction with the wallet
            transaction.save()
            return redirect('transactions:transaction_success', transaction_id=transaction.id)
    else:
        form = TransactionForm()

    transactions = Transaction.objects.filter(wallet=wallet)

    context = {
        'form': form,
        'transactions': transactions,
    }

    return render(request, 'transactions/transaction_form.html', context)


def transaction_success(request, transaction_id):
    """View to show transaction success details."""
    # Get the transaction object based on the ID
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Check if the transaction is successful, or add any other logic as needed
    if transaction.status == 'Completed':
        return render(request, 'transactions/success.html', {'transaction': transaction})
    else:
        # Optionally, you can handle cases where the transaction wasn't successful
        return render(request, 'transactions/failure.html', {'transaction': transaction})


@login_required
def verify_transaction(request, reference):
    """View to verify the transaction using a reference."""
    # Get the transaction reference and attempt to verify the transaction status
    transaction = get_object_or_404(Transaction, reference=reference, user=request.user)

    # Get the Paystack secret key from the environment
    paystack_secret_key = env('PAYSTACK_SECRET_KEY')  # Accessing the key from .env

    headers = {
        'Authorization': f'Bearer {paystack_secret_key}',
    }

    # Paystack API endpoint to verify transaction
    url = f'https://api.paystack.co/transaction/verify/{reference}/'
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        if data['status'] == 'success':
            # Update the transaction status in your database
            transaction.status = 'Completed'
            transaction.save()

            messages.success(request, f"Transaction with reference {reference} was successfully verified.")
        else:
            # If the transaction failed, update status
            transaction.status = 'Failed'
            transaction.save()

            messages.error(request, f"Transaction with reference {reference} failed.")
    else:
        messages.error(request, "Failed to verify the transaction. Please try again later.")

    # Redirect to a transaction details page or a suitable page
    return redirect('transactions:transaction_detail', transaction_id=transaction.id)


@login_required
def update_transaction_status_view(request, transaction_id):
    """View to update the status of a specific transaction."""
    # Retrieve the transaction for the logged-in user
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    if request.method == 'POST':
        # Get the new status from the POST request (ensure it's a valid status)
        new_status = request.POST.get('status')
        
        if new_status in ['Pending', 'Completed', 'Failed', 'Cancelled']:
            # Update the status
            transaction.status = new_status
            transaction.save()
            messages.success(request, f"Transaction status updated to {new_status}")
        else:
            messages.error(request, "Invalid status provided.")
        
        return redirect('transactions:transaction_detail', transaction_id=transaction.id)

    # If GET request, render the form to update status (this part can be customized)
    return render(request, 'transactions/update_transaction_status.html', {'transaction': transaction})



class TransactionListView(APIView):
    """API view to list all transactions."""
    def get(self, request):
        transactions = Transaction.objects.all()  # Adjust as needed for filtering or pagination
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)


@login_required
def transaction_detail_view(request, transaction_id):
    """View to display the details of a specific transaction."""
    # Get the transaction object for the logged-in user
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)

    return render(request, 'transactions/transaction_detail.html', {'transaction': transaction})



@login_required
def create_transaction_view(request):
    """View for creating a new transaction."""
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user  # Attach the logged-in user
            transaction.save()
            return redirect('transactions:transaction_history')  # Redirect to transaction history or another page
    else:
        form = TransactionForm()

    return render(request, 'transactions/create_transaction.html', {'form': form})



from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Wallet, Transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
def transaction_history(request):
    """View to display the user's transaction history."""
    transactions_page = None  # Ensure transactions_page is always initialized
    
    try:
        # Check if wallet exists, if not, create it
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        
        if created:
            # If the wallet is created, you can optionally set an initial balance
            wallet.balance = 0  # You can set any default value if needed
            wallet.save()
            messages.info(request, "A new wallet has been created for you.")
        
        transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')

        # Pagination logic
        paginator = Paginator(transactions, 5)  # Show 5 transactions per page
        page = request.GET.get('page')
        try:
            transactions_page = paginator.get_page(page)
        except PageNotAnInteger:
            transactions_page = paginator.get_page(1)
        except EmptyPage:
            transactions_page = paginator.get_page(paginator.num_pages)

        recent_transactions = transactions_page[:5]  # Get the first 5 for recent transactions
        older_transactions = transactions_page[5:]   # Get the rest as older transactions

        if not transactions:
            messages.info(request, "No transactions found for your wallet.")

    except Wallet.DoesNotExist:
        wallet = None
        recent_transactions = []
        older_transactions = []
        messages.error(request, "Wallet not found for the current user.")
    except Exception as e:
        wallet = None
        recent_transactions = []
        older_transactions = []
        messages.error(request, f"Error fetching transactions: {str(e)}")

    # Handle JSON response for AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = [
            {
                'date': t.created_at.strftime('%Y-%m-%d %H:%M'),
                'description': t.description,
                'amount': float(t.amount),
                'status': t.status,
            } for t in recent_transactions
        ]
        return JsonResponse({'transactions': data})

    context = {
        'wallet': wallet,
        'wallet_currencies': [
            {
                "currency": "NGN",
                "symbol": "₦",
                "balance": wallet.balance if wallet else 0
            }
        ] if wallet else [],
        'recent_transactions': recent_transactions,
        'older_transactions': older_transactions,
        'transactions_page': transactions_page  # Pass the paginated result to the template
    }

    return render(request, 'transactions/transaction_history.html', context)

@login_required
def transaction_history_json(request):
    """View to return user's transaction history as JSON."""
    transactions = Transaction.objects.filter(wallet__user=request.user).order_by('-created_at')[:10]
    data = [
        {
            "date": t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "service": t.wallet.service.name if t.wallet and t.wallet.service else "N/A",
            "amount": float(t.amount),
            "status": t.status
        }
        for t in transactions
    ]
    return JsonResponse({'transactions': data})



@login_required
def pay_with_debit_card(request):
    if request.method == 'POST':
        form = PayWithDebitCardForm(request.POST)
        if form.is_valid():
            service = form.cleaned_data['service']
            amount = form.cleaned_data['amount']
            card_number = form.cleaned_data['card_number']
            expiry_date = form.cleaned_data['expiry_date']
            cvv = form.cleaned_data['cvv']

            # Assuming you have some logic to validate the debit card details
            try:
                card = DebitCard.objects.get(user=request.user, card_number=card_number, expiry_date=expiry_date, is_active=True)
                # If we get here, the card is valid
                # Make the payment
                wallet = Wallet.objects.get(user=request.user)

                if wallet.balance < amount:
                    return HttpResponse("Insufficient funds in your wallet", status=400)

                # Process payment (e.g., deduct amount from wallet, etc.)
                wallet.balance -= amount
                wallet.save()

                # Optionally, you can create a transaction record or log the payment details

                return HttpResponse("Payment successful")

            except DebitCard.DoesNotExist:
                return HttpResponse("Invalid or inactive card details", status=400)

    else:
        form = PayWithDebitCardForm()

    return render(request, 'transactions/pay_with_debit_card.html', {'form': form})


class ProfileView(LoginRequiredMixin, View):
    """View for viewing and updating the user's profile."""

    def get(self, request):
        # Fetch the current user's profile data
        user = request.user
        form = ProfileForm(instance=user.profile)

        # Fetch the wallet and transactions for the context
        wallet = get_object_or_404(Wallet, user=user) if user.is_authenticated else None
        transactions = Transaction.objects.filter(wallet=wallet) if wallet else []

        context = {
            'form': form,
            'wallet': wallet,
            'wallet_currencies': [
                {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
            ] if wallet else [],
            'transactions': transactions,
        }
        return render(request, 'transactions/profile.html', context)

    def post(self, request):
        # Update the user's profile data
        user = request.user
        form = ProfileForm(request.POST, instance=user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('accounts:profile')  # Redirect to the same profile page
        else:
            messages.error(request, 'Please correct the errors below.')

        # Re-fetch wallet and transactions for the context in case of errors
        wallet = get_object_or_404(Wallet, user=user) if user.is_authenticated else None
        transactions = Transaction.objects.filter(wallet=wallet) if wallet else []

        context = {
            'form': form,
            'wallet': wallet,
            'wallet_currencies': [
                {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
            ] if wallet else [],
            'transactions': transactions,
        }
        return render(request, 'transactions/profile.html', context)


class UpdateProfileView(APIView):
    """API view for updating the user's profile via API."""

    def post(self, request):
        # Extract user data from request
        user = request.user
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')

        # Check if data is provided
        if not first_name or not last_name or not email:
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Update the user's profile
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        return Response({"message": "Profile updated successfully"}, status=status.HTTP_200_OK)



from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Wallet

@login_required
def get_wallet_balance(request):
    """View for getting the user's wallet balance."""
    try:
        wallet = get_object_or_404(Wallet, user=request.user)
        return JsonResponse({'balance': wallet.balance})
    except Wallet.DoesNotExist:
        return JsonResponse({'error': 'Wallet not found for the user'}, status=404)


@login_required
def process_wallet_payment(request):
    """View for processing payments using the user's wallet balance."""
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        service_id = request.POST.get('service_id')
        wallet = get_object_or_404(Wallet, user=request.user)

        if wallet.balance < amount:
            return JsonResponse({"error": "Insufficient funds in wallet."}, status=400)

        wallet.balance -= amount
        wallet.save()

        # Record the transaction
        Transaction.objects.create(
            user=request.user,
            amount=amount,
            type='debit',
            description=f'Payment for service {service_id}',
            date=timezone.now(),
            status='Completed'
        )

        return JsonResponse({"message": "Payment successful!"}, status=200)

    return JsonResponse({"error": "Invalid request method."}, status=405)

@login_required
def process_debit_card_payment(request):
    """View for processing payments using a debit card."""
    if request.method == 'POST':
        amount = float(request.POST.get('amount'))
        card_number = request.POST.get('card_number')
        expiry_date = request.POST.get('expiry_date')
        cvc = request.POST.get('cvc')

        # You'd send this data to Paystack for processing
        payload = {
            'amount': int(amount * 100),  # Paystack expects amount in kobo
            'currency': 'NGN',
            'card_number': card_number,
            'expiry_date': expiry_date,
            'cvc': cvc,
        }

        # Ensure Paystack secret key is loaded from .env
        paystack_secret_key = os.getenv('PAYSTACK_SECRET_KEY')

        response = requests.post(
            'https://api.paystack.co/charge',
            headers={'Authorization': f'Bearer {paystack_secret_key}'}, 
            data=payload
        )

        if response.status_code == 200:
            # Handle successful payment response
            payment_data = response.json()
            # Update transaction, wallet, and other business logic

            return redirect('transactions:payment_success')

        else:
            # Handle failed payment
            return redirect('transactions:payment_failed')

    return render(request, 'transactions/pay_with_debit_card.html')


from django.conf import settings
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def add_money(request):
    """View for adding money to the user's wallet."""

    wallet, created = Wallet.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = AddMoneyForm(request.POST)
        if form.is_valid():
            amount = Decimal(form.cleaned_data['amount'])

            if amount <= 0:
                messages.error(request, "Enter a valid amount.")
            else:
                # Create a transaction record
                transaction = Transaction.objects.create(
                    user=request.user,
                    wallet=wallet,
                    amount=amount,
                    status='completed',
                    transaction_id=f'TXN_{request.user.id}_{wallet.id}_{int(wallet.balance * 100)}'
                )

                # Update wallet balance
                update_user_wallet_balance(wallet, amount, 'credit')

                messages.success(request, f"₦{amount} deposited successfully.")
                return redirect('transactions:add_money')  # Redirect to avoid re-submission
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddMoneyForm()

    transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')[:10]

    context = {
        'form': form,
        'wallet': wallet,
        'wallet_currencies': [
            {"currency": "NGN", "symbol": "₦", "balance": wallet.balance}
        ],
        'transactions': transactions,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,  # ✅ Add this line
    }

    return render(request, 'transactions/add_money.html', context)

import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # Optional if you prefer to allow POSTs from frontend directly
@login_required
def verify_payment(request):
    """Verify Paystack payment and credit wallet."""
    if request.method == 'POST':
        reference = request.POST.get('reference')

        if not reference:
            return JsonResponse({'error': 'No reference provided.'}, status=400)

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        url = f"https://api.paystack.co/transaction/verify/{reference}"

        response = requests.get(url, headers=headers)
        res_data = response.json()

        if res_data['status'] and res_data['data']['status'] == 'success':
            amount_paid = Decimal(res_data['data']['amount']) / 100  # Paystack amount is in kobo

            wallet, created = Wallet.objects.get_or_create(user=request.user)

            # Update wallet balance
            update_user_wallet_balance(wallet, amount_paid, 'credit')

            # Save a transaction record
            Transaction.objects.create(
                user=request.user,
                wallet=wallet,
                amount=amount_paid,
                status='completed',
                transaction_id=reference
            )

            return JsonResponse({'message': 'Payment verified and wallet credited.'})
        else:
            return JsonResponse({'error': 'Payment verification failed.'}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)



@login_required
def success_page(request):
    wallet = get_object_or_404(Wallet, user=request.user)
    transactions = Transaction.objects.filter(user=request.user)
    
    context = {
        'wallet': wallet,
        'wallet_currencies': [
            {"currency": "NGN", "symbol": "₦", "balance": wallet.balance}
        ],
        'transactions': transactions,
    }

    return render(request, 'transactions/success_page.html', context)



from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
import json

from .models import Wallet, Transaction


class WalletView(LoginRequiredMixin, View):
    """Class-based view for fetching wallet and transaction data and handling balance updates."""

    def get(self, request):
        """Fetch wallet and transaction data for the logged-in user."""
        wallet = Wallet.objects.filter(user=request.user).first()
        if not wallet:
            return JsonResponse({'error': 'Wallet not found'}, status=404)

        transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')[:5]

        wallet_data = {
            'balance': float(wallet.balance),
        }

        transaction_data = [
            {
                'date': t.created_at.strftime('%Y-%m-%d %H:%M'),
                'amount': float(t.amount),
                'type': t.description,  # Using 'description' to represent the transaction type
                'description': t.description,
                'status': t.status,
            }
            for t in transactions
        ]

        return JsonResponse({
            'wallet_data': wallet_data,
            'transactions': transaction_data
        })

    def post(self, request):
        """Handle transactions to debit or credit the user's wallet."""
        try:
            data = json.loads(request.body)
            amount = float(data.get('amount'))
            transaction_type = data.get('type')
            description = data.get('description', '')

            if not amount or transaction_type not in ['credit', 'debit']:
                return JsonResponse({'error': 'Invalid input data'}, status=400)

            wallet = get_object_or_404(Wallet, user=request.user)

            if transaction_type == 'credit':
                wallet.balance += amount
            else:  # debit
                if wallet.balance < amount:
                    return JsonResponse({'error': 'Insufficient balance'}, status=400)
                wallet.balance -= amount

            wallet.save()

            Transaction.objects.create(
                user=request.user,
                amount=amount,
                description=transaction_type,  # Storing transaction type in description
                created_at=timezone.now(),
                status='Completed'
            )

            return JsonResponse({'message': 'Transaction completed successfully'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)



@login_required
def wallet_balance(request):
    """
    View to display the user's wallet balance.
    """
    wallet = Wallet.objects.filter(user=request.user).first()
    balance = wallet.balance if wallet else 0
    transactions = Transaction.objects.filter(wallet=wallet)  # Fetch transactions based on wallet, not user directly

    context = {
        'wallet': wallet,
        'wallet_currencies': [
            {"currency": "NGN", "symbol": "₦", "balance": balance}
        ],
        'transactions': transactions,
    }

    return render(request, 'transactions/wallet_balance.html', context)


from decimal import Decimal
import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from .models import Wallet, Transaction
from .forms import TransferForm

@login_required
def transfer(request):
    wallet = Wallet.objects.filter(user=request.user).first()
    if not wallet:
        messages.error(request, "You don't have a wallet yet. Please create one first.")
        return redirect('create_wallet')

    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            recipient_name = form.cleaned_data['recipient_name']
            account_number = form.cleaned_data['account_number']
            bank_code = form.cleaned_data['bank_code']
            transfer_note = form.cleaned_data.get('transfer_note', 'Wallet Withdrawal')
            currency = form.cleaned_data['currency']

            if amount <= Decimal('0'):
                form.add_error('amount', 'Transfer amount must be positive.')
            elif wallet.balance < amount:
                form.add_error('amount', 'Insufficient wallet balance.')

            if form.errors:
                return render(request, 'transactions/transfer.html', {'form': form, 'wallet': wallet})

            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json',
            }

            # Step 1: Create a Transfer Recipient
            recipient_payload = {
                "type": "nuban",
                "name": recipient_name,
                "account_number": account_number,
                "bank_code": bank_code,
                "currency": currency,
            }
            try:
                recipient_response = requests.post(
                    'https://api.paystack.co/transferrecipient',
                    json=recipient_payload,
                    headers=headers,
                    timeout=10
                )
                recipient_response.raise_for_status()
                recipient_data = recipient_response.json()
            except requests.RequestException:
                form.add_error(None, "Network error while creating recipient. Please try again.")
                return render(request, 'transactions/transfer.html', {'form': form, 'wallet': wallet})

            if not recipient_data.get('status'):
                form.add_error(None, recipient_data.get('message', 'Failed to create transfer recipient.'))
                return render(request, 'transactions/transfer.html', {'form': form, 'wallet': wallet})

            recipient_code = recipient_data['data']['recipient_code']

            # Step 2: Initiate Transfer
            transfer_payload = {
                "source": "balance",
                "amount": int(amount * 100),  # Paystack requires amount in kobo
                "recipient": recipient_code,
                "reason": transfer_note,
            }
            try:
                transfer_response = requests.post(
                    'https://api.paystack.co/transfer',
                    json=transfer_payload,
                    headers=headers,
                    timeout=10
                )
                transfer_response.raise_for_status()
                transfer_data = transfer_response.json()
            except requests.RequestException:
                form.add_error(None, "Network error while initiating transfer. Please try again.")
                return render(request, 'transactions/transfer.html', {'form': form, 'wallet': wallet})

            if transfer_data.get('status'):
                # Deduct from Wallet
                wallet.balance -= amount
                wallet.save()

                # Record Transaction
                Transaction.objects.create(
                    wallet=wallet,
                    amount=amount,
                    transaction_type='TRANSFER',
                    recipient_name=recipient_name,
                    transaction_reference=transfer_data['data']['transfer_code'],
                    currency=currency,
                    transfer_note=transfer_note,
                )

                messages.success(request, 'Bank transfer initiated successfully!')
                return redirect('transfer_success')
            else:
                form.add_error(None, transfer_data.get('message', 'Transfer failed. Please try again.'))

    else:
        form = TransferForm()

    context = {
        'form': form,
        'wallet': wallet,
        'wallet_currencies': [
            {"currency": "NGN", "symbol": "₦", "balance": wallet.balance}
        ],
        'transactions': Transaction.objects.filter(wallet=wallet).order_by('-created_at')[:10],  # show latest 10
    }
    return render(request, 'transactions/transfer.html', context)


@login_required
def transfer_success(request):
    wallet = Wallet.objects.filter(user=request.user).first()
    balance = wallet.balance if wallet else 0
    transactions = Transaction.objects.filter(wallet=wallet)  # Use wallet for transaction filtering

    context = {
        'wallet': wallet,
        'wallet_currencies': [
            {"currency": "NGN", "symbol": "₦", "balance": balance}
        ],
        'transactions': transactions,
    }
    return render(request, 'transactions/transfer_success.html', context)


# views.py - Handling Paystack webhook
import json
import hmac
import hashlib
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Transaction

@csrf_exempt
def paystack_webhook(request):
    # Capture the incoming Paystack webhook data
    webhook_data = json.loads(request.body)

    # Validate Paystack signature to ensure the request is from Paystack
    paystack_secret = settings.PAYSTACK_SECRET_KEY
    signature = request.headers.get('x-paystack-signature')
    
    if not signature:
        return JsonResponse({'status': 'error', 'message': 'Signature missing'}, status=400)

    # Compute signature from the request body using the Paystack secret key
    computed_signature = hmac.new(
        paystack_secret.encode('utf-8'),
        msg=request.body,
        digestmod=hashlib.sha512
    ).hexdigest()

    # Compare the computed signature to the one in the headers
    if signature != computed_signature:
        return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)

    # Handle different Paystack events
    if webhook_data['event'] == 'transfer.success':
        transaction_id = webhook_data['data']['id']
        transfer_code = webhook_data['data']['reference']
        
        try:
            # Fetch the corresponding transaction
            transaction = Transaction.objects.get(transaction_reference=transfer_code)
            
            # Update the transaction status to SUCCESS
            transaction.status = 'SUCCESS'
            transaction.save()

            # You can notify the user here (e.g., via email, SMS, etc.)
            # For example, you could call a function to send a confirmation email

        except Transaction.DoesNotExist:
            # Handle the case where the transaction does not exist in the database
            return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)

        return JsonResponse({'status': 'success'}, status=200)

    elif webhook_data['event'] == 'transfer.failed':
        transaction_id = webhook_data['data']['id']
        transfer_code = webhook_data['data']['reference']

        try:
            # Fetch the corresponding transaction
            transaction = Transaction.objects.get(transaction_reference=transfer_code)
            
            # Update the transaction status to FAILED
            transaction.status = 'FAILED'
            transaction.save()

            # Notify the user about the failure if necessary

        except Transaction.DoesNotExist:
            # Handle the case where the transaction does not exist in the database
            return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)

        return JsonResponse({'status': 'failed'}, status=200)

    # If the event type is unknown, return an error response
    return JsonResponse({'status': 'error', 'message': 'Unknown event'}, status=400)


        

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wallet_summary(request):
    user = request.user
    profile = user.profile
    balance = profile.wallet_balance  # assuming this field exists
    return Response({
        "balance": f"₦{balance:.2f}",
        "next_bill": "April 28, 2025",  # Replace with real bill query
        "subscriptions_due": 2
    })


# Consolidated Wallet Transaction View for Web (Form-based)
@login_required
def wallet_transaction_view(request):
    wallet = get_object_or_404(Wallet, user=request.user)
    if request.method == 'POST':
        form = WalletForm(request.POST, initial={'wallet': wallet})
        if form.is_valid():
            transaction_type = form.cleaned_data['transaction_type']
            amount = form.cleaned_data['amount']

            if amount <= 0:
                messages.error(request, 'Amount must be greater than zero.')
                return redirect('transactions:wallet_transaction')

            if transaction_type == 'add':
                wallet.balance += amount
                wallet.save()
                messages.success(request, f'You have successfully added N{amount} to your wallet.')

            elif transaction_type == 'withdraw' and wallet.balance >= amount:
                wallet.balance -= amount
                wallet.save()
                messages.success(request, f'You have successfully withdrawn N{amount} from your wallet.')
            elif transaction_type == 'withdraw' and wallet.balance < amount:
                messages.error(request, 'Insufficient funds in your wallet.')

            return redirect('transactions:wallet_transaction')
    else:
        form = WalletForm(initial={'wallet': wallet})

    return render(request, 'transactions/wallet_transaction.html', {'form': form})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile
from .forms import ProfileForm

@login_required
def update_profile(request):
    """View to update user's profile information."""
    profile = get_object_or_404(Profile, user=request.user)  # Get the profile for the logged-in user
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()  # Save the updated profile
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('profile')  # Redirect to the profile page (or another relevant page)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'profile/update_profile.html', {'form': form})


@login_required
def manage_fund(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        amount_str = request.POST.get('amount')

        # Validate amount
        if not (amount_str and amount_str.isdigit()):
            return HttpResponse("Invalid amount. Please enter a numeric value.")

        amount = Decimal(amount_str)

        if action == 'deposit':
            form = AddMoneyForm(request.POST)
            if form.is_valid():
                amount = Decimal(form.cleaned_data['amount'])

                wallet.balance += amount
                wallet.save()

                # Optional custom transaction ID
                transaction_id = f'transaction_{wallet.user.id}_{wallet.balance}_{amount}'

                # Create detailed transaction record
                Transaction.objects.create(
                    user=request.user,
                    wallet=wallet,
                    amount=amount,
                    status='COMPLETED',
                    transaction_id=transaction_id
                )

                # Also record deposit in a separate (standard) format
                Transaction.objects.create(
                    wallet=wallet,
                    transaction_type='credit',
                    amount=amount,
                    description="Deposit to wallet",
                    timestamp=timezone.now(),
                    status='completed'
                )
                return redirect('fund_management_success')
            else:
                return HttpResponse("Form is invalid. Please correct the errors.")

        elif action == 'withdraw':
            if wallet.balance >= amount:
                wallet.balance -= amount
                wallet.save()

                Transaction.objects.create(
                    wallet=wallet,
                    transaction_type='debit',
                    amount=amount,
                    description="Withdrawal from wallet",
                    timestamp=timezone.now(),
                    status='completed'
                )
                return redirect('fund_management_success')
            else:
                return HttpResponse("Insufficient balance for withdrawal.")

        else:
            return HttpResponse("Invalid action selected.")

    # For GET request, show the fund management form
    form = AddMoneyForm()
    return render(request, 'transactions/manage_fund.html', {'form': form, 'wallet': wallet})


# Transfer Money View for Transferring Funds
@login_required
def transfer_money(request):
    if request.method == "POST":
        amount = request.POST.get("amount")
        bank_name = request.POST.get("bank_name")
        account_number = request.POST.get("account_number")
        phone_number = request.POST.get("phone_number")

        if not amount or not bank_name or not account_number or not phone_number:
            messages.error(request, "All fields are required.")
            return redirect('transactions:funds_transfer')

        try:
            amount = Decimal(amount)
        except (ValueError, InvalidOperation):
            messages.error(request, "Invalid amount format.")
            return redirect('transactions:funds_transfer')

        user_wallet = request.user.wallet
        if user_wallet.balance < amount:
            messages.error(request, "Insufficient Wallet Balance!")
            return redirect('transactions:wallet')

        user_wallet.balance -= amount
        user_wallet.save()

        transaction_reference = str(uuid.uuid4())

        transfer_data = {
            "email": request.user.email,
            "amount": int(amount * 100),
            "bank": bank_name,
            "account_number": account_number,
            "phone": phone_number,
            "reference": transaction_reference
        }

        try:
            transfer_response = paystack.Transfer.create(**transfer_data)
            if transfer_response["status"] == "success":
                Transaction.objects.create(
                    user=request.user,
                    amount=amount,
                    reference=transaction_reference,
                    status='pending'
                )
                messages.success(request, f"Transfer of N{amount} to {bank_name} completed successfully.")
            else:
                messages.error(request, "Transfer failed. Please check the bank details and try again.")
        except Exception as e:
            messages.error(request, f"An error occurred during the transfer: {e}")

        return redirect('transactions:wallet')
    
    return render(request, 'transactions/transfer_money.html')


# Create Transfer Recipient View for Paystack API Integration
def create_transfer_recipient(request):
    if request.method == "POST":
        name = request.POST.get("name")
        account_number = request.POST.get("account_number")
        bank_code = request.POST.get("bank_code")

        url = "https://api.paystack.co/transferrecipient"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "type": "nuban",
            "name": name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": "NGN",
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                recipient_data = response.json().get("data")
                recipient = TransferRecipient.objects.create(
                    user=request.user,
                    name=name,
                    account_number=account_number,
                    bank_code=bank_code,
                    recipient_code=recipient_data["recipient_code"],
                )
                return JsonResponse({"status": "success", "recipient_code": recipient.recipient_code})
            else:
                return JsonResponse({"status": "error", "message": response.json()})
        except requests.exceptions.RequestException as e:
            return JsonResponse({"status": "error", "message": f"An error occurred: {e}"})

    return JsonResponse({"status": "error", "message": "Invalid request method"})


# Change Password View
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to profile or another page after successful password change
        else:
            return render(request, 'change_password.html', {'form': form})
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'transactions/change_password.html', {'form': form})



@login_required
def transaction_form(request, bank_id):
    """Handle the transaction form."""
    # Fetch the selected bank using the bank_id passed in the URL
    bank = get_object_or_404(UserBank, id=bank_id, user=request.user)

    # Handle the transaction on POST request
    if request.method == 'POST':
        # Get the transaction amount entered by the user
        try:
            amount = Decimal(request.POST.get('amount'))  # Ensure the amount is a decimal number
        except (ValueError, TypeError):
            messages.error(request, "Invalid amount entered.")
            return redirect('transactions:transaction_form', bank_id=bank.id)

        # Check if the amount is valid
        if amount <= 0:
            messages.error(request, "Transaction amount must be greater than zero.")
            return redirect('transactions:transaction_form', bank_id=bank.id)

        # Check if the user has sufficient funds
        user_balance = bank.get_balance()

        if amount > user_balance:
            messages.error(request, "Insufficient funds for this transaction!")
            return redirect('transactions:transaction_form', bank_id=bank.id)

        # Create the transaction
        transaction = Transaction.objects.create(
            user=request.user,
            bank=bank,
            amount=amount,
            status='pending'  # Assuming 'pending' is the initial status
        )

        # Optionally, you can update the bank balance if needed
        bank.update_balance(-amount)  # Deduct the transaction amount from user's bank balance (you would need to implement this)

        # Optionally, send a notification or email about the transaction
        messages.success(request, f"Transaction of {amount} initiated successfully.")

        # Redirect to transaction success page
        return redirect('transactions:transaction_success', transaction_id=transaction.id)

    return render(request, 'transactions/transaction_form.html', {'bank': bank})


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import UserBank, Transaction
from decimal import Decimal

@login_required
def select_bank(request, bank_id):
    """Handle the selection of a bank."""
    # Fetch the bank based on the bank_id and user
    bank = get_object_or_404(UserBank, id=bank_id, user=request.user)

    # Optional: Logic to check if the user has sufficient funds for future transactions
    user_balance = bank.get_balance()  # Assuming you have this method implemented

    if user_balance <= 0:
        messages.warning(request, "Your bank account does not have sufficient funds for transactions.")
        return redirect('transactions:transaction_form', bank_id=bank.id)

    # Store selected bank in session (optional)
    request.session['selected_bank_id'] = bank.id

    # Redirect to the transaction form with the bank info
    messages.success(request, f"Bank {bank.bank_name} selected successfully.")
    return redirect('transactions:transaction_form', bank_id=bank.id)

@login_required
def bank_selection_view(request):
    """View to select a bank for transactions"""
    
    # Fetch the user's bank details (assuming you have a UserBank model)
    user_banks = UserBank.objects.filter(user=request.user)
    
    context = {
        'user_banks': user_banks,
    }
    
    return render(request, 'transactions/bank_selection.html', context)


@login_required
def process_bank_view(request, bank_id):
    """Process the bank selection and initiate a transaction."""
    bank = get_object_or_404(UserBank, id=bank_id, user=request.user)

    # Add logic to verify user's bank and balance
    user_balance = bank.get_balance()

    if user_balance <= 0:
        messages.warning(request, "Your bank account has insufficient funds for a transaction.")
        return redirect('transactions:transaction_form', bank_id=bank.id)

    # If balance is fine, proceed with the transaction form
    return redirect('transactions:transaction_form', bank_id=bank.id)

def get_bank_code(bank_name):
    bank_mapping = {
        "Access Bank": "044",
        "Guaranty Trust Bank": "058",
        "First Bank": "011",
        "United Bank for Africa": "033",
        "Zenith Bank": "057",
        "Stanbic IBTC Bank": "068",
        "Ecobank Nigeria": "050",
        "Fidelity Bank": "070",
        "Diamond Bank": "063",
        "Union Bank": "032",
        "Wema Bank": "035",
        "Skye Bank": "076",
        "Sterling Bank": "232",
        "Standard Chartered Bank": "068",
        "Citibank Nigeria": "023",
        "Keystone Bank": "082",
        "Unity Bank": "215",
        "Jaiz Bank": "301",
        "Suntrust Bank": "100",
        "Providus Bank": "101",
        "VFD Microfinance Bank": "080",
        "Heritage Bank": "030",
        "Polaris Bank": "076",
        "Titan Trust Bank": "313",
        "MFB Bank": "500",
        "Mainstreet Bank": "070",
        "FBNQuest Merchant Bank": "091",
        "Rand Merchant Bank": "077",
        "Opay": "999",
        "Moniepoint": "223",
        "Taj Bank": "318",
    }
    return bank_mapping.get(bank_name)




# Consolidated Wallet Transaction View for Web (Form-based)
@login_required
def wallet_transaction_view(request):
    wallet = get_object_or_404(Wallet, user=request.user)
    if request.method == 'POST':
        form = WalletForm(request.POST, initial={'wallet': wallet})
        if form.is_valid():
            transaction_type = form.cleaned_data['transaction_type']
            amount = form.cleaned_data['amount']

            if transaction_type == 'add':
                wallet.balance += amount
                wallet.save()
                messages.success(request, f'You have successfully added N{amount} to your wallet.')

            elif transaction_type == 'withdraw' and wallet.balance >= amount:
                wallet.balance -= amount
                wallet.save()
                messages.success(request, f'You have successfully withdrawn N{amount} from your wallet.')
            elif transaction_type == 'withdraw' and wallet.balance < amount:
                messages.error(request, 'Insufficient funds in your wallet.')

            return redirect('transactions:wallet_transaction')
    else:
        form = WalletForm(initial={'wallet': wallet})

    return render(request, 'transactions/wallet_transaction.html', {'form': form})





import requests
import os
from dotenv import load_dotenv

load_dotenv()
PAYSTACK_SECRET = os.getenv('PAYSTACK_SECRET_KEY')
HEADERS = {
    'Authorization': f'Bearer {PAYSTACK_SECRET}',
    'Content-Type': 'application/json'
}

def create_transfer_recipient(account_number, bank_code, account_name):
    url = 'https://api.paystack.co/transferrecipient'
    payload = {
        "type": "nuban",
        "name": account_name,
        "account_number": account_number,
        "bank_code": bank_code,
        "currency": "NGN"
    }
    response = requests.post(url, json=payload, headers=HEADERS)
    return response.json()

def initiate_transfer(amount, recipient_code, reason="Wallet Withdrawal"):
    url = 'https://api.paystack.co/transfer'
    payload = {
        "source": "balance",
        "amount": int(amount * 100),  # Paystack uses kobo
        "recipient": recipient_code,
        "reason": reason
    }
    response = requests.post(url, json=payload, headers=HEADERS)
    return response.json()


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import UserBank, Transaction
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .utils import create_transfer_recipient, initiate_transfer

@login_required
@csrf_exempt
def withdraw_to_bank(request):
    if request.method == 'POST':
        bank_id = request.POST.get('bank_id')
        amount = Decimal(request.POST.get('amount'))

        bank = UserBank.objects.get(id=bank_id, user=request.user)
        current_balance = bank.get_balance()

        if amount > current_balance:
            return JsonResponse({'status': False, 'message': 'Insufficient funds'})

        # Create Paystack recipient
        recipient_response = create_transfer_recipient(
            bank.account_number, bank.bank_code, bank.account_name
        )

        if not recipient_response['status']:
            return JsonResponse({'status': False, 'message': recipient_response['message']})

        recipient_code = recipient_response['data']['recipient_code']

        # Initiate transfer
        transfer_response = initiate_transfer(amount, recipient_code)

        if transfer_response['status']:
            # Deduct from wallet manually (implement your balance logic)
            # bank.balance -= amount
            # bank.save()

            # Log transaction
            Transaction.objects.create(
                user=request.user,
                amount=amount,
                bank_name=bank.bank_name,
                account_number=bank.account_number,
                status="Pending",
                reference=transfer_response['data']['reference']
            )
            return JsonResponse({'status': True, 'message': 'Transfer initiated successfully'})
        else:
            return JsonResponse({'status': False, 'message': transfer_response['message']})
    return JsonResponse({'status': False, 'message': 'Invalid request method'})


# Change Password View
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to profile or another page after successful password change
        else:
            return render(request, 'change_password.html', {'form': form})
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'transactions/change_password.html', {'form': form})


@login_required
def record_transaction(request):
    """Record a transaction made by the user."""
    if request.method == "POST":
        amount = request.POST.get('amount')
        currency = request.POST.get('currency', 'NGN')
        trans_type = request.POST.get('type')
        description = request.POST.get('description')

        try:
            amount = float(amount)
            transaction = Transaction(
                user=request.user,
                amount=amount,
                currency=currency,
                type=trans_type,
                description=description,
                date=timezone.now(),
                status='Completed'  # Assume completed for simplicity
            )
            transaction.save()
            return JsonResponse({"message": "Transaction recorded successfully!"}, status=201)
        except ValueError:
            return JsonResponse({"error": "Invalid amount format."}, status=400)
    return JsonResponse({"error": "Invalid request method."}, status=405)


import requests
import environ
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from .models import Transaction
import uuid
from apps.services.vtpass import VTPassAPI
from apps.services.models import Service


env = environ.Env()

PAYSTACK_SECRET_KEY = env('PAYSTACK_SECRET_KEY')
PAYSTACK_INITIALIZE_URL = "https://api.paystack.co/transaction/initialize"
PAYSTACK_VERIFY_URL = "https://api.paystack.co/transaction/verify/"

# Function to initiate payment
def initiate_payment(request):
    if request.method == "POST":
        service_type = request.POST.get('service_type')
        amount = float(request.POST.get('amount'))
        phone_or_meter = request.POST.get('phone_or_meter')

        reference = str(uuid.uuid4())

        transaction = Transaction.objects.create(
            user=request.user,
            service_type=service_type,
            amount=amount,
            phone_or_meter_number=phone_or_meter,
            status='pending',
            reference=reference
        )

        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "email": request.user.email,
            "amount": int(amount * 100),
            "reference": reference,
            "callback_url": "https://yourdomain.com/payment/callback/",
            "metadata": {
                "transaction_id": transaction.id,
                "service_type": service_type,
            }
        }

        response = requests.post(PAYSTACK_INITIALIZE_URL, json=payload, headers=headers)
        res_data = response.json()

        if res_data.get("status"):
            payment_link = res_data['data']['authorization_url']
            return redirect(payment_link)
        else:
            return JsonResponse({"error": "Failed to initiate payment"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)

# Callback function for verifying payment status
def payment_callback(request):
    reference = request.GET.get('reference')

    if not reference:
        return JsonResponse({"error": "Reference not provided"}, status=400)

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
    }

    response = requests.get(f"{PAYSTACK_VERIFY_URL}{reference}", headers=headers)
    res_data = response.json()

    if res_data.get("status"):
        payment_data = res_data['data']
        status = payment_data['status']

        transaction = get_object_or_404(Transaction, reference=reference)

        if status == 'success':
            transaction.status = 'completed'
            transaction.save()

            # Instantiate the VTPassAPI class and perform the service
            vtpass_api = VTPassAPI()  # Create an instance of VTPassAPI
            vtpass_api.perform_service(transaction)  # Call the method to process the transaction with VTPass

            return JsonResponse({"message": "Payment verified and service initiated successfully!"})

        else:
            transaction.status = 'failed'
            transaction.save()
            return JsonResponse({"message": "Payment failed."})
    else:
        return JsonResponse({"error": "Invalid payment verification"}, status=400)


# Deposit Money
def deposit_initialize(request):
    amount = request.POST.get('amount')
    email = request.user.email
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "email": email,
        "amount": int(amount) * 100  # convert Naira to Kobo
    }
    res = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, json=data)
    return JsonResponse(res.json())

# After Paystack success callback
def deposit_verify(request):
    reference = request.GET.get('reference')
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
    }
    res = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
    result = res.json()
    if result['status'] and result['data']['status'] == 'success':
        amount = result['data']['amount'] / 100  # Kobo to Naira
        user = request.user
        user.wallet_balance += amount
        user.save()
        return JsonResponse({"message": "Wallet credited successfully"})
    else:
        return JsonResponse({"error": "Verification failed"}, status=400)

# Pay for Service
def pay_for_service(request):
    service_id = request.POST.get('service_id')
    payment_method = request.POST.get('payment_method')  # wallet or paystack
    amount = Service.objects.get(id=service_id).price

    if payment_method == 'wallet':
        if request.user.wallet_balance >= amount:
            request.user.wallet_balance -= amount
            request.user.save()
            # Now trigger service purchase (e.g., airtime purchase, etc.)
            return JsonResponse({"message": "Payment successful via wallet"})
        else:
            return JsonResponse({"error": "Insufficient wallet balance"}, status=400)
    elif payment_method == 'paystack':
        # Initialize Paystack transaction
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "email": request.user.email,
            "amount": int(amount * 100),  # Kobo
        }
        res = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, json=data)
        return JsonResponse(res.json())
