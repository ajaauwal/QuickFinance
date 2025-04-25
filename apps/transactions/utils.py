from datetime import timedelta
from decimal import Decimal
from typing import Any
import logging
import requests
import random
import time
import uuid

from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import get_user_model
from django.apps import apps

from .models import Transaction, Wallet
from .forms import TransferForm
from .helpers import update_transaction_status



# Use the custom user model
User = get_user_model()


from typing import Any
from .models import Wallet
import logging

logger = logging.getLogger(__name__)

def update_user_wallet_balance(wallet: Wallet, amount: Decimal, action: str) -> None:
    """
    Update the wallet balance for the user based on the transaction amount and action.
    """
    try:
        # Ensure we are updating the correct user's wallet
        if wallet:
            if action == 'credit':
                wallet.balance += amount
            elif action == 'debit':
                wallet.balance -= amount
            else:
                logger.warning(f"Unrecognized action {action} for user {wallet.user.username}.")
                return  # Do nothing if action is unrecognized

            # Save the updated wallet balance
            wallet.save()

            logger.info(f"Updated wallet balance for {wallet.user.username} to ₦{wallet.balance}")
        else:
            logger.warning(f"Wallet not found for user {wallet.user.username}")

    except Exception as e:
        # Log any error encountered
        logger.error(f"Error updating wallet balance for user {wallet.user.username}: {e}")
        raise  # Re-raise the error after logging it for further handling if needed


def create_transaction(user, service, amount, transaction_type="Payment", status="Pending"):
    """
    Utility function to create a new transaction for a user.
    """
    transaction = Transaction(
        user=user,
        service=service,
        amount=amount,
        transaction_type=transaction_type,
        status=status,
        created_at=now(),
        updated_at=now(),
    )
    transaction.save()
    return transaction


def validate_transaction_amount(amount, user):
    """
    Validate if the user has sufficient funds for a transaction.
    """
    if amount <= 0:
        raise ValidationError("Amount must be greater than zero.")

    if user.profile.wallet_balance < amount:
        raise ValidationError("Insufficient funds.")

    return True


def update_transaction_status(transaction, new_status):
    """
    Update the status of a transaction.
    """
    valid_statuses = ["Pending", "Completed", "Failed", "Refunded"]
    if new_status not in valid_statuses:
        raise ValidationError("Invalid transaction status.")

    transaction.status = new_status
    transaction.save()
    return transaction


def update_user_balance(user, amount, is_credit=True):
    """
    Update the user's wallet balance after a transaction.
    If `is_credit` is True, the amount is added to the balance; otherwise, it is deducted.
    """
    if is_credit:
        user.profile.wallet_balance += amount
    else:
        user.profile.wallet_balance -= amount

    user.profile.save()
    return user.profile.wallet_balance


def send_transaction_email(transaction: Any) -> None:
    """
    Send an email to the user about the transaction status (success or failure).
    """
    subject = f"Transaction {transaction.transaction_id} - Status Update"
    message = (
        f"Hello {transaction.user.username},\n\n"
        f"Your transaction with ID {transaction.transaction_id} has been {transaction.status}.\n\n"
        "Thank you for using our service!"
    )
    send_email(transaction.user.email, subject, message)


def send_failure_email(transaction: Any) -> None:
    """
    Send an email to the user about a failed transaction.
    """
    subject = f"Transaction {transaction.transaction_id} - Failed"
    message = (
        f"Hello {transaction.user.username},\n\n"
        f"Your transaction with ID {transaction.transaction_id} has failed. "
        "Please try again or contact support for assistance.\n\n"
        "Best regards,\nYour Service Team"
    )
    send_email(transaction.user.email, subject, message)


def send_email(to_email, subject, message):
    """
    Helper function to send an email.
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    try:
        send_mail(subject, message, from_email, [to_email], fail_silently=True)
        logger.info(f"Email sent to {to_email}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")


def get_or_create_wallet(user):
    """
    Retrieves or creates a wallet for the user.
    """
    Wallet = apps.get_model("wallets", "Wallet")
    wallet, created = Wallet.objects.get_or_create(user=user)
    return wallet


def paystack_api_request(url, payload, api_key, timeout=10, max_retries=3, retry_delay=2):
    """
    Makes a POST request to the Paystack API with retry logic and logging.
    """
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            logger.info(f"Paystack API request succeeded on attempt {attempt}: {response.json()}")
            return response.json()
        except requests.Timeout:
            logger.warning(f"API request timed out on attempt {attempt}. Retrying...")
        except requests.RequestException as e:
            logger.error(f"API request failed on attempt {attempt}: {e}")
            if attempt == max_retries:
                return {"status": "error", "message": f"API request failed after {max_retries} attempts: {e}"}

        time.sleep(retry_delay)

    return {"status": "error", "message": "Max retries exceeded without success"}


def process_funds_transfer(sender_account, receiver_account, amount):
    """
    Handles the transfer of funds between users.
    """
    sender_user = get_object_or_404(User, account_number=sender_account)
    receiver_user = get_object_or_404(User, account_number=receiver_account)

    sender_wallet = get_or_create_wallet(sender_user)
    receiver_wallet = get_or_create_wallet(receiver_user)

    if sender_wallet.balance < amount:
        logger.error("Insufficient funds for transfer.")
        return {"error": "Insufficient funds for the transfer."}

    sender_wallet.balance -= amount
    receiver_wallet.balance += amount
    sender_wallet.save()
    receiver_wallet.save()

    transaction_id = generate_transaction_id()
    create_payment(sender_user, amount, "wallet_transfer", transaction_id)
    create_payment(receiver_user, amount, "wallet_transfer", transaction_id)

    logger.info(f"Transfer successful: Sender {sender_user.username}, Receiver {receiver_user.username}, Amount {amount}")
    return {"success": "Transfer completed successfully."}


def create_payment(user, amount, payment_method, transaction_id):
    """
    Creates a payment record.
    """
    Payment = apps.get_model("transactions", "Payment")
    payment = Payment.objects.create(
        user=user,
        amount=amount,
        payment_method=payment_method,
        transaction_id=transaction_id,
        status="completed",
    )
    return payment


def generate_transaction_id():
    """
    Generates a unique transaction ID.
    """
    return str(uuid.uuid4())


def funds_transfer(request):
    """
    View to handle funds transfer form submission.
    """
    if request.method == "POST":
        form = TransferForm(request.POST)
        if form.is_valid():
            sender_account = form.cleaned_data["sender_account"]
            receiver_account = form.cleaned_data["receiver_account"]
            amount = form.cleaned_data["amount"]

            transfer_result = process_funds_transfer(sender_account, receiver_account, amount)
            if "success" in transfer_result:
                return redirect("funds_transfer_success")
            else:
                return redirect("funds_transfer_failure")
    else:
        form = TransferForm()

    return render(request, "transfer/funds_transfer.html", {"form": form})


def pay_with_wallet(user, amount):
    """
    Function to process a payment using the user's wallet.
    """
    wallet = get_or_create_wallet(user)
    if wallet.balance < amount:
        return {"error": "Insufficient funds"}

    wallet.balance -= amount
    wallet.save()
    return {"success": "Payment processed successfully"}



def transfer_success(request):
    return render(request, 'transactions/transfer_success.html')


def pay_with_paystack(user, amount):
    """
    Function to process a payment using Paystack.
    """
    PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
    url = "https://api.paystack.co/transaction/initialize"
    payload = {"email": user.email, "amount": int(amount * 100)}  # Convert to kobo

    response = paystack_api_request(url, payload, PAYSTACK_SECRET_KEY)
    if response.get("status") == "success":
        return {"success": "Payment processed successfully", "data": response.get("data")}
    else:
        logger.error(f"Paystack payment failed: {response.get('message')}")
        return {"error": response.get("message")}
