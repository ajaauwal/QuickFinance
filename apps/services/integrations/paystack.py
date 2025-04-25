import requests
import logging
import environ

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()  # Reads variables from the .env file

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class PaystackAPI:
    BASE_URL = "https://api.paystack.co"

    def __init__(self):
        # Load secret key from .env file
        self.secret_key = env("PAYSTACK_SECRET_KEY")
        if not self.secret_key:
            raise ValueError("Paystack secret key not found in environment variables.")
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def initialize_transaction(self, reference, amount, email, callback_url=None, metadata=None):
        """
        Initializes a transaction with Paystack.
        
        Args:
            reference (str): Unique transaction reference.
            amount (float): Transaction amount in Naira.
            email (str): Customer's email address.
            callback_url (str): Optional URL to redirect to after payment.
            metadata (dict): Optional metadata to include in the transaction.
        
        Returns:
            dict: API response as JSON.
        """
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
            logger.debug(f"Initializing transaction with reference: {reference} for amount: {amount}")
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            logger.debug(f"Transaction initialized successfully: {response.json()}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to initialize transaction: {e}")
            return {"status": False, "message": str(e)}

    def verify_transaction(self, reference):
        """
        Verifies a transaction with Paystack.
        
        Args:
            reference (str): Transaction reference.
        
        Returns:
            dict: API response as JSON.
        """
        url = f"{self.BASE_URL}/transaction/verify/{reference}"
        try:
            logger.debug(f"Verifying transaction with reference: {reference}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            logger.debug(f"Transaction verification result: {response.json()}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to verify transaction: {e}")
            return {"status": False, "message": str(e)}

# Example Usage
if __name__ == "__main__":
    paystack = PaystackAPI()

    # Initialize a transaction
    init_response = paystack.initialize_transaction(
        reference="unique_transaction_reference",
        amount=2000,  # Amount in Naira
        email="ctairtel@gmail.com",
        callback_url="https://mitng.com/paystack/callback",
        metadata={"customer_id": 12345}
    )
    logger.debug(f"Transaction initialize response: {init_response}")
    print(init_response)

    # Verify a transaction
    verify_response = paystack.verify_transaction(reference="unique_transaction_reference")
    logger.debug(f"Transaction verification response: {verify_response}")
    print(verify_response)
