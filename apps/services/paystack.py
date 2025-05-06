import requests
import logging
import environ
import time

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

    def _make_request(self, url, method="post", data=None, retries=3, timeout=10, delay=2):
        """
        Helper function to make a request with retry logic.
        """
        for attempt in range(1, retries + 1):
            try:
                if method == "post":
                    response = requests.post(url, json=data, headers=self.headers, timeout=timeout)
                elif method == "get":
                    response = requests.get(url, headers=self.headers, timeout=timeout)

                response.raise_for_status()  # Will raise an error if status is not 2xx
                if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
                    return response.json()
                else:
                    logger.error(f"Unexpected response: {response.text}")
                    return {"status": False, "message": "Received non-JSON response"}
            except requests.Timeout:
                logger.warning(f"Timeout on attempt {attempt}. Retrying...")
            except requests.RequestException as e:
                logger.error(f"Attempt {attempt} failed: {e}")
                if attempt == retries:
                    return {"status": False, "message": f"Failed after {retries} attempts: {e}"}
            time.sleep(delay)
        return {"status": False, "message": "Max retries exceeded"}

    def initialize_transaction(self, reference, amount, email, callback_url=None, metadata=None, retries=3, timeout=10, delay=2):
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

        logger.info(f"Initializing Paystack transaction: {reference}")
        return self._make_request(url, method="post", data=data, retries=retries, timeout=timeout, delay=delay)

    def verify_transaction(self, reference, retries=3, timeout=10, delay=2):
        """
        Verifies a Paystack transaction by reference.

        :param reference: Transaction reference
        :return: JSON response from Paystack
        """
        url = f"{self.BASE_URL}/transaction/verify/{reference}"
        logger.info(f"Verifying Paystack transaction: {reference}")
        return self._make_request(url, method="get", retries=retries, timeout=timeout, delay=delay)


class PaystackSDK:
    """
    A simplified SDK to handle Paystack transactions.
    """

    def __init__(self):
        self.api = PaystackAPI()

    def process_payment(self, reference, amount, email, callback_url=None, metadata=None, retries=3, timeout=10, delay=2):
        """
        Initiates a transaction and returns the authorization URL.

        :param reference: Unique transaction reference
        :param amount: Amount in Naira
        :param email: Customer's email
        :param callback_url: Optional callback URL
        :param metadata: Optional extra data
        :return: Authorization URL or None
        """
        response = self.api.initialize_transaction(reference, amount, email, callback_url, metadata, retries, timeout, delay)
        if response.get("status") and "data" in response:
            auth_url = response["data"].get("authorization_url")
            logger.info(f"Redirecting to Paystack payment page: {auth_url}")
            return auth_url
        logger.warning(f"Payment initialization failed: {response.get('message')}")
        return None

    def confirm_payment(self, reference, retries=3, timeout=10, delay=2):
        """
        Confirms whether a payment with the given reference was successful.

        :param reference: Transaction reference
        :return: True if successful, False otherwise
        """
        response = self.api.verify_transaction(reference, retries, timeout, delay)
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
        metadata={"customer_id": 7890},
        retries=3,
        timeout=10,
        delay=2
    )

    if auth_url:
        print(f"Visit this URL to complete payment: {auth_url}")
    else:
        print("Failed to generate payment authorization URL.")

    # Confirm payment (in real-world usage, this should happen after callback)
    success = paystack.confirm_payment(reference)
    print(f"Payment success status: {success}")
