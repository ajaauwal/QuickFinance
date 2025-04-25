import requests
import uuid
import environ
import logging
from typing import Dict, Optional

# Load environment variables
env = environ.Env()
environ.Env.read_env()

# Set up logging
logger = logging.getLogger(__name__)


class VTPassAPI:
    BASE_URL = "https://sandbox.vtpass.com/api"

    def __init__(self):
        self.api_key = env("VTPASS_API_KEY", default=None)
        self.username = env("VTPASS_USERNAME", default=None)
        self.password = env("VTPASS_PASSWORD", default=None)

        if not all([self.api_key, self.username, self.password]):
            logger.error("VTPass API credentials are missing. Please check your .env file.")

        self.headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def _make_request(self, endpoint: str, payload: Dict) -> Dict:
        """Handles sending POST requests to VTPass."""
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            logger.info(f"[VTPASS REQUEST] URL: {url}, Payload: {payload}")
            response = requests.post(url, json=payload, headers=self.headers, auth=(self.username, self.password))
            response.raise_for_status()
            data = response.json()
            logger.info(f"[VTPASS RESPONSE] {data}")
            return data
        except requests.RequestException as e:
            logger.error(f"[VTPASS ERROR] {e}")
            return {"status": False, "message": str(e)}

    def _generate_reference(self) -> str:
        """Generates a unique reference ID."""
        return str(uuid.uuid4())

    def purchase_airtime(self, provider: str, phone_number: str, amount: int, reference: Optional[str] = None) -> Dict:
        """Purchases airtime via VTPass."""
        payload = {
            "request_id": reference or self._generate_reference(),
            "serviceID": provider,
            "amount": amount,
            "phone": phone_number
        }
        return self._make_request("pay", payload)

    def purchase_data_plan(self, provider: str, phone_number: str, plan: Dict, reference: Optional[str] = None) -> Dict:
        """Purchases data bundle via VTPass."""
        payload = {
            "request_id": reference or self._generate_reference(),
            "serviceID": provider,
            "amount": plan["amount"],
            "phone": phone_number,
            "variation_code": plan["variation_code"]
        }
        return self._make_request("pay", payload)

    def purchase_tv_subscription(self, provider: str, customer_id: str, package: Dict, reference: Optional[str] = None) -> Dict:
        """Pays for TV subscription via VTPass."""
        payload = {
            "request_id": reference or self._generate_reference(),
            "serviceID": provider,
            "amount": package["amount"],
            "customer_id": customer_id,
            "variation_code": package["variation_code"]
        }
        return self._make_request("pay", payload)

    def purchase_electricity(self, provider: str, meter_number: str, amount: int, reference: Optional[str] = None) -> Dict:
        """Pays for electricity via VTPass."""
        payload = {
            "request_id": reference or self._generate_reference(),
            "serviceID": provider,
            "amount": amount,
            "meter_number": meter_number
        }
        return self._make_request("pay", payload)

    def purchase_education_payment(self, provider: str, student_id: str, amount: int, reference: Optional[str] = None) -> Dict:
        """Makes an educational payment via VTPass."""
        payload = {
            "request_id": reference or self._generate_reference(),
            "serviceID": provider,
            "amount": amount,
            "student_id": student_id
        }
        return self._make_request("pay", payload)
