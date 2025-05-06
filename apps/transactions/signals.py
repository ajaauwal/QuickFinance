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
from .utils import send_transaction_email, send_failure_email, update_user_wallet_balance

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
        # 🟢 This checks if the transaction was just created
        if created:
            logger.info(f"📥 New transaction created: {instance.id} by {instance.user.username}")

            # We DO NOT immediately credit if it's pending—just wait for it to become completed
            if instance.status == 'Pending':
                logger.info(f"🕒 Transaction {instance.id} is pending. Waiting for completion.")
                # Possibly send a 'payment pending' email if needed

            elif instance.status == 'Completed':
                logger.info(f"✅ Transaction {instance.id} created as Completed. Crediting wallet.")
                update_user_wallet_balance(instance.wallet, instance.amount, 'credit')
                send_transaction_email(instance)

        else:
            logger.info(f"🔄 Transaction {instance.id} was updated.")
            # Only credit if status changed to Completed after update
            if instance.status == 'Completed':
                # Check if wallet has already been credited (to prevent double credit)
                if not instance.wallet.transactions.filter(id=instance.id, status='Completed').exists():
                    logger.info(f"✅ Transaction {instance.id} is now Completed (via update). Crediting wallet.")
                    update_user_wallet_balance(instance.wallet, instance.amount, 'credit')
                send_transaction_email(instance)

            elif instance.status == 'Failed':
                send_failure_email(instance)

    except Exception as e:
        logger.error(f"❌ Error handling transaction {instance.id}: {e}")
        logger.debug(traceback.format_exc())


from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WalletTransfer, BankTransfer, Transfer

@receiver(post_save, sender=WalletTransfer)
def create_transfer_for_wallet(sender, instance, created, **kwargs):
    if created:
        Transfer.objects.create(
            user=instance.sender,
            transfer_type='wallet',
            amount=instance.amount,
            related_id=instance.id,
            status=instance.status
        )

@receiver(post_save, sender=BankTransfer)
def create_transfer_for_bank(sender, instance, created, **kwargs):
    if created:
        Transfer.objects.create(
            user=instance.user,
            transfer_type='bank',
            amount=instance.amount,
            related_id=instance.id,
            status=instance.status
        )
