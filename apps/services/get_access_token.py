import requests
from .config import PAYSTACK_SECRET_KEY

def get_paystack_access_token():
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
    }
    response = requests.get("https://api.paystack.co/", headers=headers)
    return response.json()