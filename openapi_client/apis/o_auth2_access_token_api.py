import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class OAuth2AccessTokenAPI:
    def __init__(self, api_key=None, api_secret=None):
        # Use environment variables or parameters for API key and secret
        self.api_key = api_key or os.getenv('AMADEUS_API_KEY')
        self.api_secret = api_secret or os.getenv('AMADEUS_API_SECRET')
        self.base_url = os.getenv('AMADEUS_BASE_URL', 'https://test.api.amadeus.com')

    def get_access_token(self):
        url = f"{self.base_url}/security/oauth2/token"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.api_secret
        }

        response = requests.post(url, data=data, headers=headers)

        if response.status_code == 200:
            access_token = response.json().get('access_token')
            return access_token
        else:
            raise Exception(f"Failed to get access token: {response.text}")

# Usage example
if __name__ == "__main__":
    # Optionally, you can provide API credentials directly or use .env
    oauth_api = OAuth2AccessTokenAPI()  # Uses values from .env by default
    try:
        token = oauth_api.get_access_token()
        print(f"Access Token: {token}")
    except Exception as e:
        print(f"Error: {str(e)}")
