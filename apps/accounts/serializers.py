from django.contrib.auth.models import User  # Import User model
from rest_framework import serializers
from apps.transactions.models import Profile, Wallet

# Serializer for creating a new user and registering them
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        # Create a new user with the given validated data
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        # Update the user instance with the new data
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)

        # Only update password if provided
        password = validated_data.get('password')
        if password:
            instance.set_password(password)

        instance.save()
        return instance

