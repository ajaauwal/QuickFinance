import requests
from typing import Optional, Dict
from django.conf import settings

# Constants for API URLs and API keys, sourced from environment variables
BUDPAY_API_BASE_URL = settings.BUDPAY_API_BASE_URL
PAYSTACK_BASE_URL = settings.PAYSTACK_BASE_URL
AMADEUS_BASE_URL = settings.AMADEUS_BASE_URL
PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
AMADEUS_API_KEY = settings.AMADEUS_API_KEY
BUDPAY_API_KEY = settings.BUDPAY_API_KEY  # Budpay secret key

def make_request(api_url: str, endpoint: str, method: str = "GET", payload: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
    """
    Generic function to make HTTP requests to any API.

    Args:
        api_url (str): Base URL of the API.
        endpoint (str): API endpoint to access.
        method (str): HTTP method ("GET" or "POST").
        payload (dict, optional): Payload for POST requests.
        headers (dict, optional): Additional headers for the request.

    Returns:
        dict: JSON response from the API.

    Raises:
        Exception: If the API request fails.
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
        raise Exception(f"API request to {url} failed: {str(e)}")

# Paystack Utility Functions
def make_paystack_request(endpoint: str, method: str = "GET", payload: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
    """
    Make a request to the Paystack API.
    """
    headers = headers or {}  # Ensure headers is not None
    headers.update({"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"})
    return make_request(PAYSTACK_BASE_URL, endpoint, method, payload, headers)

# Budpay Utility Functions
def make_budpay_request(endpoint: str, method: str = "GET", payload: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
    """
    Make a request to the Budpay API.
    """
    headers = headers or {}  # Ensure headers is not None
    headers.update({"Authorization": f"Bearer {BUDPAY_API_KEY}"})
    return make_request(BUDPAY_API_BASE_URL, endpoint, method, payload, headers)

# Amadeus Utility Functions
def make_amadeus_request(endpoint: str, method: str = "GET", payload: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
    """
    Make a request to the Amadeus API.
    """
    headers = headers or {}  # Ensure headers is not None
    headers.update({"Authorization": f"Bearer {AMADEUS_API_KEY}"})
    return make_request(AMADEUS_BASE_URL, endpoint, method, payload, headers)

# Specific API functions for Budpay, Paystack, and Amadeus
# Add your specific functions below as needed
def fetch_airtime_providers() -> Dict:
    """Fetch available airtime providers."""
    return make_budpay_request("airtime/providers")

def purchase_airtime(provider_id: str, phone_number: str, amount: float) -> Dict:
    """Purchase airtime."""
    payload = {
        "provider_id": provider_id,
        "phone_number": phone_number,
        "amount": amount
    }
    return make_budpay_request("airtime/purchase", method="POST", payload=payload)

def utility_payment(service_type: str, account_number: str, amount: float, provider_id: str) -> Dict:
    """Pay utility bills such as electricity or cable TV."""
    payload = {
        "service_type": service_type,
        "account_number": account_number,
        "amount": amount,
        "provider_id": provider_id
    }
    return make_budpay_request("utility/payment", method="POST", payload=payload)

def initialize_transaction(amount: float, email: str, callback_url: str) -> Dict:
    """Initialize a Paystack transaction."""
    payload = {
        "amount": int(amount * 100),  # Convert to kobo
        "email": email,
        "callback_url": callback_url
    }
    return make_paystack_request("transaction/initialize", method="POST", payload=payload)

def verify_transaction(reference: str) -> Dict:
    """Verify a Paystack transaction."""
    return make_paystack_request(f"transaction/verify/{reference}")

def fetch_flights(origin: str, destination: str, departure_date: str, return_date: Optional[str] = None) -> Dict:
    """Fetch available flights."""
    payload = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "returnDate": return_date,
        "adults": 1,
        "nonStop": True
    }
    return make_amadeus_request("v2/shopping/flight-offers", method="POST", payload=payload)

def book_flight(flight_offer_id: str, traveler_details: Dict) -> Dict:
    """Book a flight using Amadeus API."""
    payload = {
        "flightOffers": [flight_offer_id],
        "travelers": traveler_details
    }
    return make_amadeus_request("v1/booking/flight-orders", method="POST", payload=payload)
