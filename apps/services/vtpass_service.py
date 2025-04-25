import uuid
from apps.transactions.models import Wallet, Transaction
from .vtpass import VTPassAPI
from django.contrib.auth.models import User
from .paystack import PaystackAPI  # you must implement this

class ServiceHandler:
    def __init__(self, user: User):
        self.user = user
        self.api = VTPassAPI()

    def _generate_reference(self):
        return str(uuid.uuid4()).replace('-', '')[:20]

    def _save_transaction(self, service_type, amount, provider, reference, status, response):
        return Transaction.objects.create(
            user=self.user,
            reference=reference,
            service_type=service_type,
            amount=amount,
            provider=provider,
            status=status,
            response_data=response
        )

    def _deduct_wallet(self, amount):
        wallet = Wallet.objects.get(user=self.user)
        if wallet.balance < amount:
            return False, "Insufficient wallet balance"
        wallet.balance -= amount
        wallet.save()
        return True, "Wallet debited"

    def handle_payment(self, amount, payment_method, **kwargs):
        reference = self._generate_reference()

        if payment_method == "wallet":
            success, msg = self._deduct_wallet(amount)
            if not success:
                return {"status": False, "message": msg}

            return {"status": True, "reference": reference}

        elif payment_method == "paystack":
            paystack = PaystackAPI()
            metadata = kwargs.get("metadata", {})
            redirect_url = kwargs.get("redirect_url")

            init = paystack.initialize_payment(
                email=self.user.email,
                amount=amount,
                reference=reference,
                metadata=metadata,
                callback_url=redirect_url
            )
            return init

    def fulfill_service(self, service_type, provider, amount, data, reference):
        """
        Call this after wallet deduction or Paystack success.
        data contains necessary parameters like phone, smartcard, etc.
        """
        if service_type == "airtime":
            response = self.api.purchase_airtime(provider, data["phone"], amount, reference)
        elif service_type == "data":
            response = self.api.purchase_data_plan(provider, data["phone"], data["plan"], reference)
        elif service_type == "tv":
            response = self.api.purchase_tv_subscription(provider, data["smartcard"], data["package"], reference)
        elif service_type == "electricity":
            response = self.api.purchase_electricity(provider, data["meter_number"], amount, reference, meter_type=data.get("type", "prepaid"), phone=data.get("phone", ""))
        else:
            response = {"status": False, "message": "Invalid service type"}

        status = "success" if response.get("code") == "000" else "failed"
        transaction = self._save_transaction(service_type, amount, provider, reference, status, response)
        return transaction
