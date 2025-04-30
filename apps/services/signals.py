from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import ServicePayment, PaystackTransaction, SchoolFeesPayment

# Signal for creating a service payment (you may want to trigger an email or log)
@receiver(post_save, sender=ServicePayment)
def service_payment_created(sender, instance, created, **kwargs):
    if created:
        # Example action: Send email notification to the user when payment is successful
        if instance.status == 'completed':
            send_mail(
                subject=f"Payment Successful for {instance.service_name}",
                message=f"Dear {instance.customer_name},\n\nYour payment of {instance.amount} for {instance.service_name} was successful.\n\nThank you for using our service.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.user.email],
            )

# Signal for creating a Paystack transaction (you can store transaction status or update models based on transaction status)
@receiver(post_save, sender=PaystackTransaction)
def paystack_transaction_created(sender, instance, created, **kwargs):
    if created:
        # Example action: Update the related payment status if the transaction is successful
        if instance.status == 'success':
            # You can update a related model here
            # For example, setting the status of ServicePayment to 'completed' based on Paystack transaction
            service_payment = ServicePayment.objects.get(payment_reference=instance.reference)
            service_payment.status = 'completed'
            service_payment.save()

# Signal for School Fees Payment (Example of automatic handling after a payment)
@receiver(post_save, sender=SchoolFeesPayment)
def school_fees_payment_created(sender, instance, created, **kwargs):
    if created:
        # Example action: Notify the user after successful school fee payment
        send_mail(
            subject=f"School Fee Payment Confirmation for {instance.student_name}",
            message=f"Dear {instance.user.username},\n\nYour school fee payment of {instance.amount} has been successfully processed for {instance.student_name}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.user.email],
        )
