# apps/notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.transactions.models import Transaction  # This is correct
from .models import Notification


@receiver(post_save, sender=Transaction)
def create_notification_for_transaction(sender, instance, created, **kwargs):
    """
    Signal receiver to create a Notification when a successful Transaction is saved.
    """
    if created and instance.status == 'success':
        Notification.objects.create(
            user=instance.user,
            message=f"Transaction of ₦{instance.amount} has been successfully completed."
        )
