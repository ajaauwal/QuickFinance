from rest_framework import serializers
from .models import AirtimeRecharge, UtilityBill, Service

class AirtimeRechargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirtimeRecharge
        fields = '__all__'

class UtilityBillSerializer(serializers.ModelSerializer):
    class Meta:
        model = UtilityBill
        fields = '__all__'



class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

