import requests
import environ
import logging

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
            logger.error("VTPass API credentials are missing. Check your .env file.")
        
        self.headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def _make_request(self, payload):
        """Handles sending POST requests to VTPass."""
        url = f"{self.BASE_URL}/pay"
        try:
            logger.info(f"Sending request to {url} with payload: {payload}")
            response = requests.post(url, json=payload, headers=self.headers, auth=(self.username, self.password))
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return data
        except requests.RequestException as e:
            logger.error(f"VTPass request failed: {e}")
            return {"status": False, "message": str(e)}

    def purchase_airtime(self, provider, phone_number, amount, reference):
        """Purchases airtime from VTPass."""
        payload = {
            "request_id": reference,
            "serviceID": provider,
            "amount": amount,
            "phone": phone_number
        }
        return self._make_request(payload)

    def purchase_data_plan(self, provider, phone_number, plan, reference):
        """Purchases data from VTPass."""
        payload = {
            "request_id": reference,
            "serviceID": provider,
            "amount": plan["amount"],
            "phone": phone_number,
            "variation_code": plan["variation_code"]
        }
        return self._make_request(payload)

    def purchase_tv_subscription(self, provider, customer_id, package, reference):
        """Purchases TV subscription from VTPass."""
        payload = {
            "request_id": reference,
            "serviceID": provider,
            "amount": package["amount"],
            "customer_id": customer_id,
            "variation_code": package["variation_code"]
        }
        return self._make_request(payload)

    def purchase_electricity(self, provider, meter_number, amount, reference):
        """Purchases electricity payment from VTPass."""
        payload = {
            "request_id": reference,
            "serviceID": provider,
            "amount": amount,
            "meter_number": meter_number
        }
        return self._make_request(payload)

    def purchase_education_payment(self, provider, student_id, amount, reference):
        """Makes an educational payment via VTPass."""
        payload = {
            "request_id": reference,
            "serviceID": provider,
            "amount": amount,
            "student_id": student_id
        }
        return self._make_request(payload)
