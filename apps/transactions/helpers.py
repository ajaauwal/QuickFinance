# apps/transactions/helpers.py

def validate_transaction_amount(amount):
    """
    Validates whether the transaction amount is greater than zero.

    Args:
        amount (float): The transaction amount to validate.

    Returns:
        bool: True if the amount is valid, otherwise False.
    """
    return amount > 0

def update_transaction_status(transaction, status):
    """
    Updates the status of a transaction and saves the changes.

    Args:
        transaction (Transaction): The transaction object to update.
        status (str): The new status to assign to the transaction.

    Returns:
        None
    """
    transaction.status = status
    transaction.save()
