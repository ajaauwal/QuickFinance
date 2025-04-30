import requests
import logging
import environ

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class PaystackAPI:
    BASE_URL = "https://api.paystack.co"

    def __init__(self):
        self.secret_key = env("PAYSTACK_SECRET_KEY", default=None)
        if not self.secret_key:
            logger.critical("Paystack secret key not found in environment variables.")
            raise ValueError("Paystack secret key not configured.")
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def initialize_transaction(self, reference, amount, email, callback_url=None, metadata=None):
        """
        Initializes a Paystack transaction.

        :param reference: Unique transaction reference
        :param amount: Amount in Naira
        :param email: Customer's email
        :param callback_url: Optional callback URL
        :param metadata: Optional dictionary for extra data
        :return: JSON response from Paystack
        """
        url = f"{self.BASE_URL}/transaction/initialize"
        data = {
            "reference": reference,
            "amount": int(amount * 100),  # Paystack uses Kobo
            "email": email,
        }
        if callback_url:
            data["callback_url"] = callback_url
        if metadata:
            data["metadata"] = metadata

        try:
            logger.info(f"Initializing Paystack transaction: {reference}")
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Paystack response: {result}")
            return result
        except requests.RequestException as e:
            logger.error(f"Failed to initialize transaction: {e}")
            return {"status": False, "message": str(e)}

    def verify_transaction(self, reference):
        """
        Verifies a Paystack transaction by reference.

        :param reference: Transaction reference
        :return: JSON response from Paystack
        """
        url = f"{self.BASE_URL}/transaction/verify/{reference}"
        try:
            logger.info(f"Verifying Paystack transaction: {reference}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Verification response: {result}")
            return result
        except requests.RequestException as e:
            logger.error(f"Failed to verify transaction: {e}")
            return {"status": False, "message": str(e)}


class PaystackSDK:
    """
    A simplified SDK to handle Paystack transactions.
    """

    def __init__(self):
        self.api = PaystackAPI()

    def process_payment(self, reference, amount, email, callback_url=None, metadata=None):
        """
        Initiates a transaction and returns the authorization URL.

        :param reference: Unique transaction reference
        :param amount: Amount in Naira
        :param email: Customer's email
        :param callback_url: Optional callback URL
        :param metadata: Optional extra data
        :return: Authorization URL or None
        """
        response = self.api.initialize_transaction(reference, amount, email, callback_url, metadata)
        if response.get("status") and "data" in response:
            auth_url = response["data"].get("authorization_url")
            logger.info(f"Redirecting to Paystack payment page: {auth_url}")
            return auth_url
        logger.warning(f"Payment initialization failed: {response.get('message')}")
        return None

    def confirm_payment(self, reference):
        """
        Confirms whether a payment with the given reference was successful.

        :param reference: Transaction reference
        :return: True if successful, False otherwise
        """
        response = self.api.verify_transaction(reference)
        data = response.get("data", {})
        if response.get("status") and data.get("status") == "success":
            logger.info(f"Payment confirmed for reference: {reference}")
            return True
        logger.warning(f"Payment verification failed or not successful: {response.get('message')}")
        return False


# Optional example usage block
if __name__ == "__main__":
    paystack = PaystackSDK()
    reference = "unique_transaction_ref_001"

    # Initialize a transaction
    auth_url = paystack.process_payment(
        reference=reference,
        amount=2500,
        email="customer@example.com",
        callback_url="https://quickfinance.com/payment/callback",
        metadata={"customer_id": 7890}
    )

    if auth_url:
        print(f"Visit this URL to complete payment: {auth_url}")
    else:
        print("Failed to generate payment authorization URL.")

    # Confirm payment (in real-world usage, this should happen after callback)
    success = paystack.confirm_payment(reference)
    print(f"Payment success status: {success}")
