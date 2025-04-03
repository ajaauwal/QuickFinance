from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from apps.transactions.models import Transaction

@receiver(post_save, sender=Transaction)
def create_notification_for_transaction(sender, instance, created, **kwargs):
    if created and instance.status == 'success':
        Notification.objects.create(
            user=instance.user,
            message=f"Transaction of {instance.amount} has been successfully completed."
        )
