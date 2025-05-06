# apps/transactions/validators.py

from decimal import Decimal
from django.core.exceptions import ValidationError

def validate_positive_amount(amount, user=None):
    """
    Validates the transaction amount.

    Ensures:
    1. The amount is positive.
    2. The user has sufficient balance in their wallet (if a user is provided).

    Args:
        amount (Decimal): The transaction amount to validate.
        user (User, optional): The user initiating the transaction.

    Raises:
        ValidationError: If the amount is invalid or the user does not have sufficient funds.
    """
    if not isinstance(amount, Decimal):
        raise ValidationError("Transaction amount must be a valid decimal number.")
    
    if amount <= Decimal("0.00"):
        raise ValidationError("Transaction amount must be greater than zero.")
    
    if user:
        # Move the import here to avoid circular import
        from .models import Wallet
        
        wallet = Wallet.objects.filter(user=user).first()
        if wallet is None:
            raise ValidationError("User does not have an associated wallet.")
        if wallet.balance < amount:
            raise ValidationError("Insufficient funds in the wallet for this transaction.")

    return amount
