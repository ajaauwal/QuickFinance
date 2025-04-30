import environ
import requests

env = environ.Env()

class VTPassAPI:
    def __init__(self):
        self.url = "https://sandbox.vtpass.com/api/pay"  # sandbox URL
        self.username = env('VTPASS_USERNAME')
        self.password = env('VTPASS_PASSWORD')

    def perform_service(self, transaction):
        headers = {
            "api-key": self.username,
            "secret-key": self.password,
            "Content-Type": "application/json",
        }

        service_map = {
            'airtime': 'airtime',
            'data': 'data',
            'tv': 'tv',
            'electricity': 'electricity',
            'school_fees': 'education',
            'waec': 'waec',
        }

        payload = {
            "request_id": transaction.reference,
            "serviceID": service_map.get(transaction.service_type),
            "billersCode": transaction.phone_or_meter_number,
            "amount": str(transaction.amount),
            "phone": transaction.phone_or_meter_number,
        }

        response = requests.post(self.url, json=payload, headers=headers)
        res_data = response.json()

        if res_data.get("code") == "000":
            transaction.status = 'completed'
        else:
            transaction.status = 'failed'

        transaction.save()
        return res_data
