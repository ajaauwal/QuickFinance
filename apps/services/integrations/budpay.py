import requests
import hmac
import hashlib
import json
import logging
from typing import Optional, Dict, Any
from django.conf import settings
from requests.exceptions import RequestException
from time import sleep

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URL and API key for BudPay
BASE_URL: str = settings.BUDPAY_API_BASE_URL  # Ensure this is set in your .env file
API_KEY: bytes = settings.BUDPAY_API_KEY.encode()  # Ensure this is set in your .env file

# Centralized configuration
class Config:
    TIMEOUT = 10
    RETRIES = 3
    RETRY_DELAY = 2


# Helper function for HMAC encryption
def generate_signature(payload: str) -> str:
    """
    Generates an HMAC-SHA-512 signature using the BudPay Secret Key.
    """
    return hmac.new(API_KEY, payload.encode(), hashlib.sha512).hexdigest()


# Common function to build headers
def build_headers(payload: Optional[str] = None) -> Dict[str, str]:
    """
    Builds headers with Authorization and optional signature.
    """
    headers = {
        "Authorization": f"Bearer {settings.BUDPAY_API_KEY}",
        "Content-Type": "application/json",
    }
    if payload:
        headers["Encryption"] = generate_signature(payload)
    return headers


# Common function for GET requests
def get_request(endpoint: str) -> Dict[str, Any]:
    """
    Makes a GET request to the BudPay API.
    """
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url, headers=build_headers(), timeout=Config.TIMEOUT)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logger.error(f"GET request to {url} failed: {e}")
        return {"error": str(e)}


# Common function for POST requests with retry logic
def post_request(endpoint: str, data: Dict[str, Any], retries: int = Config.RETRIES, delay: int = Config.RETRY_DELAY) -> Dict[str, Any]:
    """
    Makes a POST request to the BudPay API with a retry mechanism.
    """
    url = f"{BASE_URL}/{endpoint}"
    payload = json.dumps(data)
    headers = build_headers(payload)

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
def fetch_airtime_providers() -> Dict[str, Any]:
    """Fetches available airtime providers from BudPay."""
    return get_request("airtime")


def purchase_airtime(provider: str, number: str, amount: float, reference: str) -> Dict[str, Any]:
    """Initiates an airtime purchase."""
    data = {
        "provider": provider,
        "number": number,
        "amount": amount,
        "reference": reference,
    }
    return post_request("airtime/recharge", data)


# Internet Functions
def fetch_internet_providers() -> Dict[str, Any]:
    """Fetches available internet providers from BudPay."""
    return get_request("internet")


def validate_internet_number(provider: str, number: str) -> Dict[str, Any]:
    """Validates an internet account number."""
    data = {"provider": provider, "number": number}
    return post_request("internet/validate", data)


def purchase_internet(provider: str, number: str, plan: str, reference: str) -> Dict[str, Any]:
    """Purchases an internet subscription."""
    data = {
        "provider": provider,
        "number": number,
        "plan": plan,
        "reference": reference,
    }
    return post_request("internet/recharge", data)


# TV Subscription Functions
def fetch_tv_providers() -> Dict[str, Any]:
    """Fetches available TV subscription providers from BudPay."""
    return get_request("tv")


def validate_tv_account(provider: str, number: str) -> Dict[str, Any]:
    """Validates a TV account number."""
    data = {"provider": provider, "number": number}
    return post_request("tv/validate", data)


def purchase_tv_subscription(provider: str, number: str, plan: str, reference: str) -> Dict[str, Any]:
    """Purchases a TV subscription."""
    data = {
        "provider": provider,
        "number": number,
        "plan": plan,
        "reference": reference,
    }
    return post_request("tv/recharge", data)


# Electricity Functions
def fetch_electricity_providers() -> Dict[str, Any]:
    """Fetches available electricity providers from BudPay."""
    return get_request("electricity")


def validate_electricity_meter(provider: str, number: str, meter_type: str) -> Dict[str, Any]:
    """Validates an electricity meter number."""
    data = {"provider": provider, "number": number, "type": meter_type}
    return post_request("electricity/validate", data)


def recharge_electricity(provider: str, number: str, meter_type: str, amount: float, reference: str) -> Dict[str, Any]:
    """Initiates an electricity recharge."""
    data = {
        "provider": provider,
        "number": number,
        "type": meter_type,
        "amount": amount,
        "reference": reference,
    }
    return post_request("electricity/recharge", data)


# Test Payment Functions
def test_airtime_payment(provider: str, number: str, amount: float, reference: str) -> Dict[str, Any]:
    """Simulates an airtime purchase using test credentials."""
    return purchase_airtime(provider, number, amount, reference)


def test_electricity_payment(provider: str, meter_number: str, amount: float, reference: str) -> Dict[str, Any]:
    """Simulates an electricity payment using test credentials."""
    return recharge_electricity(provider, meter_number, "postpaid", amount, reference)


def test_tv_payment(provider: str, decoder_number: str, amount: float, reference: str) -> Dict[str, Any]:
    """Simulates a TV subscription payment using test credentials."""
    return purchase_tv_subscription(provider, decoder_number, "basic", reference)
