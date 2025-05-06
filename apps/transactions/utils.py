import uuid
import time
import logging
from decimal import Decimal

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from django.apps import apps

from .models import Transaction, Wallet
from .forms import BankTransferForm

logger = logging.getLogger(__name__)
User = get_user_model()

# ------------------- Wallet Balance Update -------------------

def update_user_wallet_balance(wallet: Wallet, amount: Decimal, action: str) -> None:
    try:
        if not wallet:
            logger.warning("Wallet not found.")
            return

        if action == 'credit':
            wallet.balance += amount
        elif action == 'debit':
            wallet.balance -= amount
        else:
            logger.warning(f"Unrecognized action {action} for user {wallet.user.username}")
            return

        wallet.save()
        logger.info(f"Updated wallet balance for {wallet.user.username} to ₦{wallet.balance}")
    except Exception as e:
        logger.error(f"Error updating wallet for {wallet.user.username}: {e}")
        raise

# ------------------- Transaction Utilities -------------------

def create_transaction(user, service, amount, transaction_type="Payment", status="Pending"):
    transaction = Transaction.objects.create(
        user=user,
        service=service,
        amount=amount,
        transaction_type=transaction_type,
        status=status,
        created_at=now(),
        updated_at=now(),
    )
    return transaction

def validate_transaction_amount(amount, user):
    if amount <= 0:
        raise ValidationError("Amount must be greater than zero.")
    if user.profile.wallet_balance < amount:
        raise ValidationError("Insufficient funds.")
    return True

def update_transaction_status(transaction, new_status):
    valid_statuses = ["Pending", "Completed", "Failed", "Refunded"]
    if new_status not in valid_statuses:
        raise ValidationError("Invalid transaction status.")

    transaction.status = new_status
    transaction.save()
    return transaction

def update_user_balance(user, amount, is_credit=True):
    profile = user.profile
    profile.wallet_balance += amount if is_credit else -amount
    profile.save()
    return profile.wallet_balance

# ------------------- Email Notifications -------------------

def send_transaction_email(transaction):
    subject = f"Transaction {transaction.transaction_id} - Status Update"
    message = (
        f"Hello {transaction.user.username},\n\n"
        f"Your transaction with ID {transaction.transaction_id} has been {transaction.status}.\n\n"
        "Thank you for using our service!"
    )
    send_email(transaction.user.email, subject, message)

def send_failure_email(transaction):
    subject = f"Transaction {transaction.transaction_id} - Failed"
    message = (
        f"Hello {transaction.user.username},\n\n"
        f"Your transaction with ID {transaction.transaction_id} has failed. "
        "Please try again or contact support for assistance.\n\n"
        "Best regards,\nYour Service Team"
    )
    send_email(transaction.user.email, subject, message)

def send_email(to_email, subject, message):
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=True)
        logger.info(f"Email sent to {to_email}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")

# ------------------- Wallet Management -------------------

def get_or_create_wallet(user):
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet

# ------------------- Paystack API Helpers -------------------

def paystack_api_request(url, payload, api_key, timeout=10, max_retries=3, retry_delay=2):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            logger.info(f"Paystack API request succeeded on attempt {attempt}")
            return response.json()
        except requests.Timeout:
            logger.warning(f"Timeout on attempt {attempt}. Retrying...")
        except requests.RequestException as e:
            logger.error(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                return {"status": "error", "message": f"Failed after {max_retries} attempts: {e}"}
        time.sleep(retry_delay)
    return {"status": "error", "message": "Max retries exceeded"}

def pay_with_paystack(user, amount):
    url = "https://api.paystack.co/transaction/initialize"
    payload = {"email": user.email, "amount": int(amount * 100)}  # in kobo
    response = paystack_api_request(url, payload, settings.PAYSTACK_SECRET_KEY)
    if response.get("status") == "success":
        return {"success": "Payment initialized", "data": response.get("data")}
    logger.error(f"Paystack failed: {response.get('message')}")
    return {"error": response.get("message")}

def create_transfer_recipient(name, account_number, bank_code, email):
    url = "https://api.paystack.co/transferrecipient"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}
    payload = {
        "type": "nuban",
        "name": name,
        "account_number": account_number,
        "bank_code": bank_code,
        "currency": "NGN",
        "email": email,
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("status"):
            return data["data"]
        logger.error(f"Failed to create recipient: {data.get('message')}")
    except requests.RequestException as e:
        logger.error(f"Error creating recipient: {e}")
    return None

def initiate_transfer(amount, recipient_code, reason=""):
    url = "https://api.paystack.co/transfer"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}
    payload = {
        "source": "balance",
        "amount": amount,
        "recipient": recipient_code,
        "reason": reason,
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("status"):
            return data["data"]
        logger.error(f"Failed to initiate transfer: {data.get('message')}")
    except requests.RequestException as e:
        logger.error(f"Transfer initiation error: {e}")
    return None

# ------------------- Payment & Transfer Logic -------------------

def create_payment(user, amount, payment_method, transaction_id):
    Payment = apps.get_model("transactions", "Payment")
    return Payment.objects.create(
        user=user,
        amount=amount,
        payment_method=payment_method,
        transaction_id=transaction_id,
        status="completed",
    )

def generate_transaction_id():
    return str(uuid.uuid4())

def process_funds_transfer(sender_account, receiver_account, amount):
    sender_user = get_object_or_404(User, account_number=sender_account)
    receiver_user = get_object_or_404(User, account_number=receiver_account)

    sender_wallet = get_or_create_wallet(sender_user)
    receiver_wallet = get_or_create_wallet(receiver_user)

    if sender_wallet.balance < amount:
        logger.error("Insufficient funds for transfer.")
        return {"error": "Insufficient funds."}

    sender_wallet.balance -= amount
    receiver_wallet.balance += amount
    sender_wallet.save()
    receiver_wallet.save()

    txn_id = generate_transaction_id()
    create_payment(sender_user, amount, "wallet_transfer", txn_id)
    create_payment(receiver_user, amount, "wallet_transfer", txn_id)

    logger.info(f"Funds transferred: {amount} from {sender_user.username} to {receiver_user.username}")
    return {"success": "Transfer successful."}

def pay_with_wallet(user, amount):
    wallet = get_or_create_wallet(user)
    if wallet.balance < amount:
        return {"error": "Insufficient funds"}
    wallet.balance -= amount
    wallet.save()
    return {"success": "Payment processed successfully"}

# ------------------- Views -------------------

def bank_transfer(request):
    if request.method == "POST":
        form = BankTransferForm(request.POST)
        if form.is_valid():
            sender_account = form.cleaned_data["sender_account"]
            receiver_account = form.cleaned_data["receiver_account"]
            amount = form.cleaned_data["amount"]

            result = process_funds_transfer(sender_account, receiver_account, amount)
            return redirect("funds_transfer_success" if "success" in result else "funds_transfer_failure")
    else:
        form = BankTransferForm()

    return render(request, "transactions/bank_transfer.html", {"form": form})

def transfer_success(request):
    return render(request, 'transactions/transfer_success.html')
