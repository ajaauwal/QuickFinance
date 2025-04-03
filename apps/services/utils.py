import requests
from typing import Optional, Dict, Any
from django.conf import settings
import environ
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
env = environ.Env()
environ.Env.read_env()

# Constants for API URLs and API keys, sourced from .env file
VTPASS_BASE_URL = env('VTPASS_API_BASE_URL', default='https://vtpass.com/api')
VTPASS_PUBLIC_KEY = env('VTPASS_PUBLIC_KEY', default='')
VTPASS_SECRET_KEY = env('VTPASS_SECRET_KEY', default='')

AMADEUS_API_KEY = env('AMADEUS_API_KEY', default='')
AMADEUS_API_SECRET = env('AMADEUS_API_SECRET', default='')
AMADEUS_BASE_URL = env('AMADEUS_BASE_URL', default='https://test.api.amadeus.com/v1')

PAYSTACK_PUBLIC_KEY = env('PAYSTACK_PUBLIC_KEY', default='')
PAYSTACK_SECRET_KEY = env('PAYSTACK_SECRET_KEY', default='')
PAYSTACK_BASE_URL = env('PAYSTACK_BASE_URL', default='https://api.paystack.co/')
PAYSTACK_PAYMENT_URL = env('PAYSTACK_PAYMENT_URL', default='https://api.paystack.co/transaction/initialize')
PAYSTACK_TRANSFER_URL = env('PAYSTACK_TRANSFER_URL', default='https://api.paystack.co/transfer')
PAYSTACK_CALLBACK_URL = env('PAYSTACK_CALLBACK_URL', default='')

# Check for missing API keys
if not VTPASS_SECRET_KEY:
    logger.warning("VTPASS_SECRET_KEY is not set. Ensure it is defined in the .env file.")

if not PAYSTACK_SECRET_KEY:
    logger.warning("PAYSTACK_SECRET_KEY is not set. Ensure it is defined in the .env file.")

if not AMADEUS_API_KEY:
    logger.warning("AMADEUS_API_KEY is not set. Ensure it is defined in the .env file.")

def make_request(api_url: str, endpoint: str, method: str = "GET", payload: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Generic function to make HTTP requests to any API.
    """
    url = f"{api_url}/{endpoint}"
    default_headers = {"Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)

    try:
        response = requests.request(method, url, json=payload, headers=default_headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API request to {url} failed: {str(e)}")
        return {"error": f"API request failed: {str(e)}"}

def make_paystack_request(endpoint: str, method: str = "GET", payload: Optional[Dict] = None) -> Dict[str, Any]:
    """Make a request to the Paystack API."""
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    return make_request(PAYSTACK_BASE_URL, endpoint, method, payload, headers)

def make_vtpass_request(endpoint: str, method: str = "GET", payload: Optional[Dict] = None) -> Dict[str, Any]:
    """Make a request to the VTpass API."""
    headers = {"Authorization": f"Bearer {VTPASS_SECRET_KEY}"}
    return make_request(VTPASS_BASE_URL, endpoint, method, payload, headers)

def make_amadeus_request(endpoint: str, method: str = "GET", payload: Optional[Dict] = None) -> Dict[str, Any]:
    """Make a request to the Amadeus API."""
    headers = {"Authorization": f"Bearer {AMADEUS_API_KEY}"}
    return make_request(AMADEUS_BASE_URL, endpoint, method, payload, headers)

def fetch_airtime_providers() -> Dict[str, Any]:
    """Fetch available airtime providers."""
    return make_vtpass_request("airtime/providers")

def purchase_airtime(provider_id: str, phone_number: str, amount: float) -> Dict[str, Any]:
    """Purchase airtime."""
    payload = {"provider_id": provider_id, "phone_number": phone_number, "amount": amount}
    return make_vtpass_request("airtime/purchase", method="POST", payload=payload)

def utility_payment(service_type: str, account_number: str, amount: float, provider_id: str) -> Dict[str, Any]:
    """Pay utility bills such as electricity or cable TV."""
    payload = {"service_type": service_type, "account_number": account_number, "amount": amount, "provider_id": provider_id}
    return make_vtpass_request("utility/payment", method="POST", payload=payload)

def initialize_transaction(amount: float, email: str, callback_url: str) -> Dict[str, Any]:
    """Initialize a Paystack transaction."""
    payload = {"amount": int(amount * 100), "email": email, "callback_url": callback_url}
    return make_paystack_request("transaction/initialize", method="POST", payload=payload)

def verify_transaction(reference: str) -> Dict[str, Any]:
    """Verify a Paystack transaction."""
    return make_paystack_request(f"transaction/verify/{reference}")

def fetch_flights(origin: str, destination: str, departure_date: str, return_date: Optional[str] = None) -> Dict[str, Any]:
    """Fetch available flights."""
    payload = {"originLocationCode": origin, "destinationLocationCode": destination, "departureDate": departure_date, "returnDate": return_date, "adults": 1, "nonStop": True}
    return make_amadeus_request("v2/shopping/flight-offers", method="POST", payload=payload)

def book_flight(flight_offer_id: str, traveler_details: Dict[str, Any]) -> Dict[str, Any]:
    """Book a flight using Amadeus API."""
    payload = {"flightOffers": [flight_offer_id], "travelers": traveler_details}
    return make_amadeus_request("v1/booking/flight-orders", method="POST", payload=payload)
