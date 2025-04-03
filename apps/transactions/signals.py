from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Profile, Wallet, Transaction
from .utils import send_transaction_email, send_failure_email
from decimal import Decimal
import logging
from django.contrib.auth import get_user_model
from django.db import transaction
import traceback  # Import the traceback module

# Set up logging
logger = logging.getLogger(__name__)

# Signal to handle a Transaction after it is saved
@receiver(post_save, sender=Transaction)
def handle_transaction(sender, instance, created, **kwargs):
    """
    Signal triggered after a Transaction is saved.
    - Logs the creation of a transaction.
    - Updates transaction status if necessary.
    - Sends notifications to the user.
    """
    try:
        if created:
            logger.info(f"New transaction created: {instance.id} by {instance.user.username}")
            
            if instance.status == 'Pending':
                instance.status = 'Completed'
                instance.save()
                logger.info(f"Transaction {instance.id} status updated to 'Completed'")
                send_transaction_email(instance)
            
            update_user_wallet_balance(instance.wallet, instance.amount, 'credit')
        
        else:
            logger.info(f"Transaction {instance.id} was updated.")
            
            if instance.status == 'Completed':
                send_transaction_email(instance)
            elif instance.status == 'Failed':
                send_failure_email(instance)
    except Exception as e:
        logger.error(f"Error handling transaction {instance.id}: {e}")

def send_transaction_email(transaction):
    """
    Send an email to the user about the transaction status (success or failure).
    """
    subject = f"Transaction {transaction.id} - Status Update"
    message = f"Hello {transaction.user.username},\n\nYour transaction with ID {transaction.id} has been {transaction.status}.\n\nThank you for using our service!"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [transaction.user.email]

    try:
        send_mail(subject, message, from_email, recipient_list)
        logger.info(f"Email sent to {transaction.user.email} regarding transaction {transaction.id}")
    except Exception as e:
        logger.error(f"Failed to send email for transaction {transaction.id}: {e}")

def send_failure_email(transaction):
    """
    Send an email to the user about a failed transaction.
    """
    subject = f"Transaction {transaction.id} - Failed"
    message = f"Hello {transaction.user.username},\n\nYour transaction with ID {transaction.id} has failed. Please try again or contact support for assistance.\n\nBest regards,\nYour Service Team"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [transaction.user.email]

    try:
        send_mail(subject, message, from_email, recipient_list)
        logger.info(f"Failure email sent to {transaction.user.email} for transaction {transaction.id}")
    except Exception as e:
        logger.error(f"Failed to send failure email for transaction {transaction.id}: {e}")

# Signal to create the user's profile and wallet
@receiver(post_save, sender=get_user_model())
def create_user_profile_and_wallet(sender, instance, created, **kwargs):
    """
    Create the profile and wallet when a user is created.
    """
    if created:
        try:
            with transaction.atomic():  # Wrap in atomic block for consistency
                profile, profile_created = Profile.objects.get_or_create(user=instance)
                wallet, wallet_created = Wallet.objects.get_or_create(user=instance)

                if profile_created:
                    logger.info(f"Profile created for user: {instance.username}")
                if wallet_created:
                    logger.info(f"Wallet created for user: {instance.username}")
            
            send_mail(
                subject='Welcome to Quickfinance!',
                message='Thanks for signing up to Quickfinance. We are excited to have you on board.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                fail_silently=False,
            )
            logger.info(f"Welcome email sent to: {instance.email}")
        
        except Exception as e:
            logger.error(f"Error creating profile or wallet for user {instance.username}: {e}")
            # Add more detailed logging
            logger.error(f"Exception details: {e.__class__.__name__}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

# Signal to update the user's profile and wallet
@receiver(post_save, sender=get_user_model())
def update_user_profile_and_wallet(sender, instance, created, **kwargs):
    """
    Update the profile and wallet when a user is updated.
    """
    if not created:  # Only update for existing users
        try:
            if hasattr(instance, 'profile'):
                instance.profile.save()
                logger.info(f"Profile updated for user: {instance.username}")
            
            if hasattr(instance, 'wallet'):
                instance.wallet.save()
                logger.info(f"Wallet updated for user: {instance.username}")
        
        except Exception as e:
            logger.error(f"Error updating profile or wallet for user {instance.username}: {e}")

@receiver(post_save, sender=Wallet)
def handle_wallet_transaction(sender, instance, created, **kwargs):
    """
    Signal triggered after a Wallet transaction is saved.
    """
    if created:
        try:
            logger.info(f"New wallet transaction created for user: {instance.user.username}")
            update_user_wallet_balance(instance, instance.balance, 'credit')
        except Exception as e:
            logger.error(f"Error updating wallet balance for wallet {instance.id}: {e}")

def update_user_wallet_balance(wallet, amount, transaction_type):
    """
    Updates the wallet balance based on the transaction type (credit or debit).
    """
    if wallet is None:
        raise ValueError("Wallet does not exist for the user.")
    
    if transaction_type == 'credit':
        wallet.balance += Decimal(amount)
    elif transaction_type == 'debit':
        if wallet.balance >= Decimal(amount):
            wallet.balance -= Decimal(amount)
        else:
            raise ValueError("Insufficient funds for debit transaction.")
    else:
        raise ValueError("Invalid transaction type specified.")
    
    wallet.save()




# Set up logging
logger = logging.getLogger(__name__)

# Signal to handle a Transaction after it is saved
@receiver(post_save, sender=Transaction)
def handle_transaction(sender, instance, created, **kwargs):
    """
    Signal triggered after a Transaction is saved.
    - Logs the creation of a transaction.
    - Updates transaction status if necessary.
    - Sends notifications to the user.
    """
    try:
        if created:
            logger.info(f"New transaction created: {instance.id} by {instance.user.username}")
            
            if instance.status == 'Pending':
                instance.status = 'Completed'
                instance.save()
                logger.info(f"Transaction {instance.id} status updated to 'Completed'")
                send_transaction_email(instance)
            
            update_user_wallet_balance(instance.wallet, instance.amount, 'credit')
        
        else:
            logger.info(f"Transaction {instance.id} was updated.")
            
            if instance.status == 'Completed':
                send_transaction_email(instance)
            elif instance.status == 'Failed':
                send_failure_email(instance)
    except Exception as e:
        logger.error(f"Error handling transaction {instance.id}: {e}")



def send_email(subject, message, recipient_list):
    from_email = settings.DEFAULT_FROM_EMAIL
    try:
        send_mail(subject, message, from_email, recipient_list)
        logger.info(f"Email sent to {recipient_list}")
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_list}: {e}")

def send_transaction_email(transaction):
    subject = f"Transaction {transaction.id} - Status Update"
    message = f"Hello {transaction.user.username},\n\nYour transaction with ID {transaction.id} has been {transaction.status}.\n\nThank you for using our service!"
    send_email(subject, message, [transaction.user.email])

def send_failure_email(transaction):
    subject = f"Transaction {transaction.id} - Failed"
    message = f"Hello {transaction.user.username},\n\nYour transaction with ID {transaction.id} has failed. Please try again or contact support for assistance.\n\nBest regards,\nYour Service Team"
    send_email(subject, message, [transaction.user.email])


# Signal to create the user's profile and wallet
@receiver(post_save, sender=get_user_model())
def create_user_profile_and_wallet(sender, instance, created, **kwargs):
    """
    Create the profile and wallet when a user is created.
    """
    if created:
        try:
            with transaction.atomic():  # Wrap in atomic block for consistency
                profile, profile_created = Profile.objects.get_or_create(user=instance)
                wallet, wallet_created = Wallet.objects.get_or_create(user=instance)

                if profile_created:
                    logger.info(f"Profile created for user: {instance.username}")
                if wallet_created:
                    logger.info(f"Wallet created for user: {instance.username}")
            
            send_mail(
                subject='Welcome to Quickfinance!',
                message='Thanks for signing up to Quickfinance. We are excited to have you on board.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                fail_silently=False,
            )
            logger.info(f"Welcome email sent to: {instance.email}")
        
        except Exception as e:
            logger.error(f"Error creating profile or wallet for user {instance.username}: {e}")
            # Add more detailed logging
            logger.error(f"Exception details: {e.__class__.__name__}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

# Signal to update the user's profile and wallet
@receiver(post_save, sender=get_user_model())
def update_user_profile_and_wallet(sender, instance, created, **kwargs):
    """
    Update the profile and wallet when a user is updated.
    """
    if not created:  # Only update for existing users
        try:
            if hasattr(instance, 'profile'):
                instance.profile.save()
                logger.info(f"Profile updated for user: {instance.username}")
            
            if hasattr(instance, 'wallet'):
                instance.wallet.save()
                logger.info(f"Wallet updated for user: {instance.username}")
        
        except Exception as e:
            logger.error(f"Error updating profile or wallet for user {instance.username}: {e}")

@receiver(post_save, sender=Wallet)
def handle_wallet_transaction(sender, instance, created, **kwargs):
    """
    Signal triggered after a Wallet transaction is saved.
    """
    if created:
        try:
            logger.info(f"New wallet transaction created for user: {instance.user.username}")
            update_user_wallet_balance(instance, instance.balance, 'credit')
        except Exception as e:
            logger.error(f"Error updating wallet balance for wallet {instance.id}: {e}")

def update_user_wallet_balance(wallet, amount, transaction_type):
    """
    Updates the wallet balance based on the transaction type (credit or debit).
    """
    if wallet is None:
        raise ValueError("Wallet does not exist for the user.")
    
    if transaction_type == 'credit':
        wallet.balance += Decimal(amount)
    elif transaction_type == 'debit':
        if wallet.balance >= Decimal(amount):
            wallet.balance -= Decimal(amount)
        else:
            raise ValueError("Insufficient funds for debit transaction.")
    else:
        raise ValueError("Invalid transaction type specified.")
    
    wallet.save()
