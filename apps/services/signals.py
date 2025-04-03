from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from apps.transactions.models import Wallet, Profile
from .models import SchoolFeesPayment

@receiver(post_save, sender=User)
def create_user_associations(sender, instance, created, **kwargs):
    """
    Signal to create related Wallet and Profile instances
    whenever a new User is created.
    """
    if created:
        try:
            Wallet.objects.create(user=instance)
            Profile.objects.create(user=instance)
        except Exception as e:
            print(f"Error creating Wallet or Profile: {e}")

@receiver(post_save, sender=User)
def save_user_associations(sender, instance, **kwargs):
    """
    Signal to save related Wallet and Profile instances
    whenever the User instance is saved.
    """
    try:
        if hasattr(instance, 'wallet'):
            instance.wallet.save()
        if hasattr(instance, 'profile'):
            instance.profile.save()
    except Exception as e:
        print(f"Error saving Wallet or Profile: {e}")

@receiver(post_save, sender=SchoolFeesPayment)
def handle_school_fees_payment(sender, instance, created, **kwargs):
    if created:
        # Add any post-save actions here
        pass
