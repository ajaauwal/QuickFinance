from rest_framework import serializers
from .models import Transaction
from django.core.exceptions import ValidationError
from .models import Profile, Wallet, Payment
from .utils import validate_transaction_amount, update_transaction_status, update_user_balance


# Serializer for updating the user's profile
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'user', 'phone_number', 'address']  # Include the fields in your Profile model

    def update(self, instance, validated_data):
        # Update the profile instance with the new data
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.address = validated_data.get('address', instance.address)
        instance.save()
        return instance

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'user', 'service', 'amount', 
            'transaction_type', 'status', 'timestamp'
        ]
        read_only_fields = ['transaction_id', 'user', 'status', 'timestamp']  # Make some fields read-only

    def validate_amount(self, value):
        """
        Validate the transaction amount, ensuring it's positive and the user has sufficient funds.
        """
        user = self.context.get('user')  # Retrieve the user from the context (API view passes this)
        if value <= 0:
            raise ValidationError("Amount must be positive.")
        if not validate_transaction_amount(value, user):
            raise ValidationError("Insufficient funds.")
        return value

    def validate_service(self, value):
        """
        Validate the service to ensure it's active and allowed for the transaction.
        """
        if not value.is_active:  # Assuming your Service model has an `is_active` field
            raise ValidationError("Selected service is currently unavailable.")
        return value

    def create(self, validated_data):
        """
        Handle transaction creation, including deducting funds and setting transaction status.
        """
        user = self.context.get('user')
        amount = validated_data['amount']
        
        # Deduct funds from the user's balance before creating the transaction
        update_user_balance(user, amount, is_credit=False)
        
        # Create the transaction with default status 'Pending'
        transaction = Transaction.objects.create(user=user, status='Pending', **validated_data)
        
        # Optionally trigger post-creation updates or notifications
        update_transaction_status(transaction, 'Pending')
        return transaction

    def update(self, instance, validated_data):
        """
        Handle transaction updates, including updating status and user balance if required.
        """
        status = validated_data.get('status', instance.status)
        if status != instance.status:
            # Handle status-specific updates, e.g., refund on cancellation
            if status == 'Cancelled' and instance.status != 'Completed':
                update_user_balance(instance.user, instance.amount, is_credit=True)  # Refund user balance
            
            update_transaction_status(instance, status)
        
        return super().update(instance, validated_data)
