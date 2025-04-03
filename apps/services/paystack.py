import requests
import logging
import environ

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()  # Reads variables from the .env file

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class PaystackAPI:
    BASE_URL = "https://api.paystack.co"

    def __init__(self):
        # Load secret key from .env file
        self.secret_key = env("PAYSTACK_SECRET_KEY", default=None)
        if not self.secret_key:
            raise ValueError("Paystack secret key not found in environment variables.")
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def initialize_transaction(self, reference, amount, email, callback_url=None, metadata=None):
        """Initializes a transaction with Paystack."""
        url = f"{self.BASE_URL}/transaction/initialize"
        data = {
            "reference": reference,
            "amount": int(amount * 100),  # Convert to kobo
            "email": email,
        }
        if callback_url:
            data["callback_url"] = callback_url
        if metadata:
            data["metadata"] = metadata

        try:
            logger.debug(f"Initializing transaction: {reference} for {amount} NGN")
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Transaction initialization failed: {e}")
            return {"status": False, "message": str(e)}

    def verify_transaction(self, reference):
        """Verifies a transaction with Paystack."""
        url = f"{self.BASE_URL}/transaction/verify/{reference}"
        try:
            logger.debug(f"Verifying transaction: {reference}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Transaction verification failed: {e}")
            return {"status": False, "message": str(e)}


class PaystackSDK:
    """A simplified interface for Paystack operations."""

    def __init__(self):
        self.api = PaystackAPI()

    def process_payment(self, reference, amount, email, callback_url=None, metadata=None):
        """Handles initializing and verifying a payment."""
        response = self.api.initialize_transaction(reference, amount, email, callback_url, metadata)
        if response.get("status"):
            return response["data"].get("authorization_url")  # Redirect user to Paystack payment page
        logger.error(f"Payment processing failed: {response.get('message')}")
        return None

    def confirm_payment(self, reference):
        """Confirms if a payment was successful."""
        response = self.api.verify_transaction(reference)
        if response.get("status") and response.get("data", {}).get("status") == "success":
            return True
        logger.warning(f"Payment verification failed: {response.get('message')}")
        return False


# Example Usage
if __name__ == "__main__":
    paystack = PaystackSDK()

    # Initialize a transaction
    auth_url = paystack.process_payment(
        reference="unique_transaction_ref",
        amount=2000,  # Amount in Naira
        email="customer@example.com",
        callback_url="https://example.com/callback",
        metadata={"customer_id": 12345}
    )
    if auth_url:
        print(f"Payment URL: {auth_url}")
    else:
        print("Failed to generate payment URL.")

    # Verify a transaction
    is_successful = paystack.confirm_payment(reference="unique_transaction_ref")
    print(f"Payment successful: {is_successful}")
