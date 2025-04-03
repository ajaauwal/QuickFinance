import requests
from django.conf import settings
from ..models.checkin_response import CheckinResponse
from requests.exceptions import RequestException

def get_amadeus_access_token():
    """Retrieve the access token for Amadeus API using client credentials."""
    url = f"{settings.AMADEUS_BASE_URL}/security/oauth2/token"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials',
        'client_id': settings.AMADEUS_API_KEY,
        'client_secret': settings.AMADEUS_API_SECRET
    }

    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

        # If successful, return the access token
        return response.json().get('access_token')

    except RequestException as e:
        raise Exception(f"Error getting access token: {str(e)}")

def get_checkin_link_from_amadeus(pnr):
    """Retrieve the check-in link for a specific PNR."""
    access_token = get_amadeus_access_token()  # Get the access token
    url = f"{settings.AMADEUS_BASE_URL}/v1/airlines/booking/checkin-links"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    params = {
        'pnr': pnr  # Pass the PNR as a query parameter
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Check for request errors

        # If successful, parse the check-in link from the response
        data = response.json()

        # Optionally, validate and return the response using CheckinResponse (optional)
        checkin_link = data.get('checkinLink', '')
        if checkin_link:
            return CheckinResponse(checkinLink=checkin_link)  # Returning as an object

        raise Exception("Check-in link not found in response.")

    except RequestException as e:
        raise Exception(f"Error retrieving check-in link: {str(e)}")
