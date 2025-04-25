from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
import logging
import traceback

from .models import Profile, Wallet, Transaction
from .utils import send_transaction_email, send_failure_email

logger = logging.getLogger(__name__)
User = get_user_model()

# ✅ Create Profile and Wallet when a new user is created
@receiver(post_save, sender=User)
def create_user_profile_and_wallet(sender, instance, created, **kwargs):
    if created:
        try:
            with transaction.atomic():
                Profile.objects.get_or_create(user=instance)
                Wallet.objects.get_or_create(user=instance)

            logger.info(f"✅ Profile and Wallet created for user: {instance.username}")

            # Send welcome email
            try:
                send_mail(
                    subject='Welcome to Quickfinance!',
                    message='Thanks for signing up to Quickfinance. We are excited to have you on board.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.email],
                    fail_silently=False,
                )
                logger.info(f"📧 Welcome email sent to: {instance.email}")
            except Exception as email_err:
                logger.warning(f"❗ Failed to send welcome email to {instance.email}: {email_err}")

        except Exception as e:
            logger.error(f"❌ Error creating profile or wallet for user {instance.username}: {e}")
            logger.debug(traceback.format_exc())

# 🔁 Update profile and wallet on user update
@receiver(post_save, sender=User)
def update_user_profile_and_wallet(sender, instance, created, **kwargs):
    if not created:
        try:
            if hasattr(instance, 'profile'):
                instance.profile.save()
                logger.info(f"🔄 Profile updated for user: {instance.username}")
            if hasattr(instance, 'wallet'):
                instance.wallet.save()
                logger.info(f"🔄 Wallet updated for user: {instance.username}")
        except Exception as e:
            logger.error(f"❌ Error updating profile or wallet for user {instance.username}: {e}")
            logger.debug(traceback.format_exc())

# 💸 Handle transaction logic and update wallet
@receiver(post_save, sender=Transaction)
def handle_transaction(sender, instance, created, **kwargs):
    try:
        if created:
            logger.info(f"📥 New transaction created: {instance.id} by {instance.user.username}")

            if instance.status == 'Pending':
                instance.status = 'Completed'
                instance.save()
                logger.info(f"✅ Transaction {instance.id} marked as Completed")
                send_transaction_email(instance)

            update_user_wallet_balance(instance.wallet, instance.amount, 'credit')

        else:
            logger.info(f"🔄 Transaction {instance.id} was updated.")
            if instance.status == 'Completed':
                send_transaction_email(instance)
            elif instance.status == 'Failed':
                send_failure_email(instance)

    except Exception as e:
        logger.error(f"❌ Error handling transaction {instance.id}: {e}")
        logger.debug(traceback.format_exc())

# 🧮 Wallet balance updater
def update_user_wallet_balance(wallet, amount, transaction_type):
    if wallet is None:
        raise ValueError("❗ Wallet does not exist for the user.")

    amount = Decimal(amount)

    if transaction_type == 'credit':
        wallet.balance += amount
    elif transaction_type == 'debit':
        if wallet.balance >= amount:
            wallet.balance -= amount
        else:
            raise ValueError("❌ Insufficient funds for debit transaction.")
    else:
        raise ValueError("❌ Invalid transaction type specified.")

    wallet.save()
