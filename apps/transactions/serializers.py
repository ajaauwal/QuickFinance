from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Profile, Wallet, Payment, Transaction
from .utils import (
    validate_transaction_amount,
    update_transaction_status,
    update_user_balance
)

# Serializer for updating the user's profile
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'user', 'phone_number', 'address']

    def update(self, instance, validated_data):
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
        read_only_fields = ['transaction_id', 'user', 'status', 'timestamp']

    def validate_amount(self, value):
        user = self.context.get('user')
        if value <= 0:
            raise ValidationError("Amount must be positive.")
        if not validate_transaction_amount(value, user):
            raise ValidationError("Insufficient funds.")
        return value

    def validate_service(self, value):
        if not value.is_active:
            raise ValidationError("Selected service is currently unavailable.")
        return value

    def create(self, validated_data):
        user = self.context.get('user')
        amount = validated_data['amount']

        # Deduct balance before creating transaction
        update_user_balance(user, amount, is_credit=False)

        transaction = Transaction.objects.create(
            user=user,
            status='Pending',
            **validated_data
        )

        update_transaction_status(transaction, 'Pending')
        return transaction

    def update(self, instance, validated_data):
        status = validated_data.get('status', instance.status)
        if status != instance.status:
            if status == 'Cancelled' and instance.status != 'Completed':
                update_user_balance(instance.user, instance.amount, is_credit=True)
            update_transaction_status(instance, status)

        return super().update(instance, validated_data)
