from django.test import TestCase
from unittest.mock import patch
from django.urls import reverse
from .utils import (
    make_request,
    make_paystack_request,
    make_budpay_request,
    make_amadeus_request,
    initialize_transaction,
    verify_transaction,
    fetch_airtime_providers,
    purchase_airtime,
    utility_payment,
    fetch_flights,
    book_flight
)

class UtilsTestCase(TestCase):
    """Test cases for utility functions."""

    @patch("requests.request")
    def test_make_request_success(self, mock_request):
        mock_response = mock_request.return_value
        mock_response.json.return_value = {"success": True}
        mock_response.status_code = 200

        response = make_request("http://fakeapi.com", "endpoint")
        self.assertEqual(response, {"success": True})

    @patch("requests.request")
    def test_make_request_failure(self, mock_request):
        mock_request.side_effect = Exception("API request failed")

        with self.assertRaises(Exception):
            make_request("http://fakeapi.com", "endpoint")

    @patch("requests.request")
    def test_make_paystack_request(self, mock_request):
        mock_response = mock_request.return_value
        mock_response.json.return_value = {"status": "success"}
        mock_response.status_code = 200

        response = make_paystack_request("transaction/initialize")
        self.assertEqual(response["status"], "success")

    @patch("requests.request")
    def test_make_budpay_request(self, mock_request):
        mock_response = mock_request.return_value
        mock_response.json.return_value = {"status": "success"}
        mock_response.status_code = 200

        response = make_budpay_request("airtime/providers")
        self.assertEqual(response["status"], "success")

    @patch("requests.request")
    def test_make_amadeus_request(self, mock_request):
        mock_response = mock_request.return_value
        mock_response.json.return_value = {"data": ["flight1", "flight2"]}
        mock_response.status_code = 200

        response = make_amadeus_request("v2/shopping/flight-offers")
        self.assertIn("data", response)

    @patch("requests.request")
    def test_fetch_airtime_providers(self, mock_request):
        mock_response = mock_request.return_value
        mock_response.json.return_value = {"providers": ["Provider1", "Provider2"]}
        mock_response.status_code = 200

        response = fetch_airtime_providers()
        self.assertIn("providers", response)

    @patch("requests.request")
    def test_purchase_airtime(self, mock_request):
        mock_response = mock_request.return_value
        mock_response.json.return_value = {"status": "success"}
        mock_response.status_code = 200

        response = purchase_airtime("provider123", "1234567890", 500)
        self.assertEqual(response["status"], "success")

    @patch("requests.request")
    def test_pay_utility_bill(self, mock_request):
        mock_response = mock_request.return_value
        mock_response.json.return_value = {"status": "success"}
        mock_response.status_code = 200

        response = utility_payment("electricity", "123456", 1000, "provider123")
        self.assertEqual(response["status"], "success")

    @patch("requests.request")
    def test_fetch_flights(self, mock_request):
        mock_response = mock_request.return_value
        mock_response.json.return_value = {"data": ["Flight1", "Flight2"]}
        mock_response.status_code = 200

        response = fetch_flights("LAX", "JFK", "2024-12-20")
        self.assertIn("data", response)

    @patch("requests.request")
    def test_book_flight(self, mock_request):
        mock_response = mock_request.return_value
        mock_response.json.return_value = {"status": "confirmed"}
        mock_response.status_code = 200

        traveler_details = {"name": "John Doe"}
        response = book_flight("offer123", traveler_details)
        self.assertEqual(response["status"], "confirmed")


class APIViewsTestCase(TestCase):
    """Test cases for API views."""

    def test_airtime_recharge_view(self):
        url = reverse("airtime_recharge")
        data = {"phone_number": "1234567890", "amount": 500}

        with patch(".utils.make_budpay_request") as mock_request:
            mock_request.return_value = {"status": "success"}

            response = self.client.post(url, data, content_type="application/json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "success")

    def test_utility_bills_view(self):
        url = reverse("utility_bills", args=["electricity"])
        data = {"account_number": "123456", "amount": 1000, "provider_id": "prov123"}

        with patch(".utils.make_budpay_request") as mock_request:
            mock_request.return_value = {"status": "success"}

            response = self.client.post(url, data, content_type="application/json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "success")

    def test_initialize_transaction(self):
        with patch(".utils.make_paystack_request") as mock_request:
            mock_request.return_value = {"status": "success"}
            response = initialize_transaction(1000, "test@example.com", "http://callback.com")
            self.assertEqual(response["status"], "success")

    def test_verify_transaction(self):
        with patch(".utils.make_paystack_request") as mock_request:
            mock_request.return_value = {"status": "success"}
            response = verify_transaction("reference123")
            self.assertEqual(response["status"], "success")
