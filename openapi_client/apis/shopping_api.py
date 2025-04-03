# flight_search.py

from openapi_client.apis.shopping_api import ShoppingAPI  # Correct import

# Define your API client class or function
class FlightSearch:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.shopping_api = ShoppingAPI(self.api_key, self.api_secret)  # Instantiate the API client

    def search_flights(self, query):
        # Use the shopping_api instance to perform a flight search
        result = self.shopping_api.search(query)
        return result
