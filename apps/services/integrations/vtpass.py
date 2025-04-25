import requests
import hmac
import hashlib
import json
import logging
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from requests.exceptions import RequestException
from time import sleep

# Load environment variables from the .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retrieve VTPass API details from environment variables
BASE_URL: str = os.getenv("VTPASS_API_BASE_URL")  # Base URL from .env
API_KEY: str = os.getenv("VTPASS_API_KEY")  # API Key from .env

# Centralized configuration for retries and timeout
class Config:
    TIMEOUT = 10  # Timeout for API requests in seconds
    RETRIES = 3  # Number of retry attempts
    RETRY_DELAY = 2  # Delay between retries in seconds

class VTPassSDK:
    def __init__(self):
        if not BASE_URL or not API_KEY:
            raise ValueError("VTPass API Base URL and API Key must be set in the .env file.")
        self.base_url = BASE_URL
        self.api_key = API_KEY

    # Helper function for generating HMAC-SHA512 signature
    def generate_signature(self, payload: str) -> str:
        """
        Generates an HMAC-SHA512 signature using VTPass API key.
        """
        return hmac.new(self.api_key.encode(), payload.encode(), hashlib.sha512).hexdigest()

    # Helper function to build headers with authorization
    def build_headers(self, payload: Optional[str] = None) -> Dict[str, str]:
        """
        Builds headers with authorization and optional encryption signature.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if payload:
            headers["Encryption"] = self.generate_signature(payload)
        return headers

    # Helper function for making GET requests
    def get_request(self, endpoint: str) -> Dict[str, Any]:
        """
        Makes a GET request to the VTPass API.
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.build_headers(), timeout=Config.TIMEOUT)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"GET request to {url} failed: {e}")
            return {"error": str(e)}

    # Helper function for making POST requests with retry logic
    def post_request(self, endpoint: str, data: Dict[str, Any], retries: int = Config.RETRIES, delay: int = Config.RETRY_DELAY) -> Dict[str, Any]:
        """
        Makes a POST request to the VTPass API with retry logic.
        """
        url = f"{self.base_url}/{endpoint}"
        payload = json.dumps(data)
        headers = self.build_headers(payload)

        for attempt in range(retries):
            try:
                response = requests.post(url, headers=headers, data=payload, timeout=Config.TIMEOUT)
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                if attempt < retries - 1:
                    backoff_time = delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1}/{retries} failed. Retrying after {backoff_time} seconds: {e}")
                    sleep(backoff_time)
                else:
                    logger.error(f"POST request to {url} failed after {retries} attempts: {e}")
                    return {"error": str(e)}

    # Airtime Functions
    def fetch_airtime_providers(self) -> Dict[str, Any]:
        """Fetch available airtime providers."""
        return self.get_request("airtime")

    def purchase_airtime(self, provider: str, number: str, amount: float, reference: str) -> Dict[str, Any]:
        """Initiates an airtime purchase."""
        data = {
            "provider": provider,
            "number": number,
            "amount": amount,
            "reference": reference,
        }
        return self.post_request("airtime/recharge", data)

    # Data Functions
    def fetch_data_providers(self) -> Dict[str, Any]:
        """Fetch available data providers."""
        return self.get_request("data")

    def purchase_data(self, provider: str, number: str, amount: float, reference: str) -> Dict[str, Any]:
        """Purchases a data plan."""
        data = {
            "provider": provider,
            "number": number,
            "amount": amount,
            "reference": reference,
        }
        return self.post_request("data/recharge", data)

    # TV Subscription Functions
    def fetch_tv_providers(self) -> Dict[str, Any]:
        """Fetch available TV subscription providers."""
        return self.get_request("tv")

    def purchase_tv_subscription(self, provider: str, number: str, plan: str, reference: str) -> Dict[str, Any]:
        """Purchases a TV subscription."""
        data = {
            "provider": provider,
            "number": number,
            "plan": plan,
            "reference": reference,
        }
        return self.post_request("tv/recharge", data)

    # Electricity Functions
    def fetch_electricity_providers(self) -> Dict[str, Any]:
        """Fetch available electricity providers."""
        return self.get_request("electricity")

    def recharge_electricity(self, provider: str, number: str, meter_type: str, amount: float, reference: str) -> Dict[str, Any]:
        """Initiates an electricity recharge for prepaid or postpaid meter."""
        if meter_type not in ["prepaid", "postpaid"]:
            return {"error": "Invalid meter type. It should be 'prepaid' or 'postpaid'."}

        data = {
            "provider": provider,
            "number": number,
            "type": meter_type,
            "amount": amount,
            "reference": reference,
        }
        return self.post_request("electricity/recharge", data)

    def validate_electricity_meter(self, provider: str, number: str, meter_type: str) -> Dict[str, Any]:
        """Validates an electricity meter number for both prepaid and postpaid."""
        if meter_type not in ["prepaid", "postpaid"]:
            return {"error": "Invalid meter type. It should be 'prepaid' or 'postpaid'."}

        data = {"provider": provider, "number": number, "type": meter_type}
        return self.post_request("electricity/validate", data)

    # Education Functions
    def check_waec_result(self, pin: str) -> Dict[str, Any]:
        """Checks WAEC result using the provided PIN."""
        data = {
            "pin": pin
        }
        return self.post_request("education/waec-result", data)

    # Test Payment Functions (for testing the SDK)
    def test_airtime_payment(self, provider: str, number: str, amount: float, reference: str) -> Dict[str, Any]:
        """Simulates an airtime purchase for testing."""
        return self.purchase_airtime(provider, number, amount, reference)

    def test_electricity_payment(self, provider: str, meter_number: str, amount: float, reference: str) -> Dict[str, Any]:
        """Simulates an electricity payment for testing."""
        return self.recharge_electricity(provider, meter_number, "postpaid", amount, reference)

    def test_tv_payment(self, provider: str, decoder_number: str, amount: float, reference: str) -> Dict[str, Any]:
        """Simulates a TV subscription payment for testing."""
        return self.purchase_tv_subscription(provider, decoder_number, "basic", reference)
