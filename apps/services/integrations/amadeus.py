import os
from dotenv import load_dotenv
from amadeus import Client, ResponseError
import logging
import aiohttp
import asyncio
import requests

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

class AmadeusService:
    def __init__(self):
        # Get API credentials from environment variables
        self.api_key = os.getenv('AMADEUS_API_KEY')
        self.api_secret = os.getenv('AMADEUS_API_SECRET')
        self.base_url = os.getenv('AMADEUS_BASE_URL', 'https://test.api.amadeus.com')

        # Ensure API credentials are available
        if not self.api_key or not self.api_secret:
            raise ValueError("AMADEUS_API_KEY and AMADEUS_API_SECRET must be set in the .env file")

        # Initialize the Amadeus client
        self.amadeus = Client(
            client_id=self.api_key,
            client_secret=self.api_secret
        )

    def get_access_token(self):
        try:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.api_secret
            }
            response = requests.post(f"{self.base_url}/v1/security/oauth2/token", headers=headers, data=data)
            response.raise_for_status()
            access_token = response.json()['access_token']
            return access_token
        except requests.RequestException as e:
            logger.error(f"Error during API request: {e}")
            return None

    async def async_get_flight_checkin_links(self, airline_code):
        access_token = self.get_access_token()
        if not access_token:
            return None

        headers = {'Authorization': f'Bearer {access_token}'}
        flight_search_endpoint = f'{self.base_url}/v2/reference-data/urls/checkin-links'
        parameters = {"airlineCode": airline_code}

        async with aiohttp.ClientSession() as session:
            async with session.get(flight_search_endpoint, params=parameters, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.error(f"Error fetching flight check-in links: {resp.status}")
                    return None

    # Flight Services
    def search_flights(self, origin, destination, departure_date, adults=1, max_price=None):
        try:
            response = self.amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=departure_date,
                adults=adults,
                maxPrice=max_price
            )
            return response.data
        except ResponseError as e:
            logger.error(f"Error during flight search: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during flight search: {e}")
        return None

    def get_flight_inspiration(self, origin):
        try:
            response = self.amadeus.shopping.flight_destinations.get(origin=origin)
            return response.data
        except ResponseError as e:
            logger.error(f"Error fetching flight inspiration: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching flight inspiration: {e}")
        return None

    def get_flight_schedule(self, carrier_code, flight_number, scheduled_departure_date):
        try:
            response = self.amadeus.schedule.flights.get(
                carrierCode=carrier_code,
                flightNumber=flight_number,
                scheduledDepartureDate=scheduled_departure_date
            )
            return response.data
        except ResponseError as e:
            logger.error(f"Error fetching flight schedule: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching flight schedule: {e}")
        return None

    def get_airport_info(self, airport_code):
        try:
            response = self.amadeus.reference_data.locations.airports.get(airportCode=airport_code)
            return response.data
        except ResponseError as e:
            logger.error(f"Error fetching airport info: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching airport info: {e}")
        return None

    def get_airline_info(self, airline_code):
        try:
            response = self.amadeus.reference_data.airlines.get(airlineCodes=airline_code)
            return response.data
        except ResponseError as e:
            logger.error(f"Error fetching airline info: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching airline info: {e}")
        return None

    # Destination Experience Services
    def get_destination_experiences(self, city_code):
        try:
            response = self.amadeus.shopping.activities.get(
                location=city_code
            )
            return response.data
        except ResponseError as e:
            logger.error(f"Error fetching destination experiences: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching destination experiences: {e}")
        return None

    def get_points_of_interest(self, latitude, longitude):
        try:
            response = self.amadeus.reference_data.locations.points_of_interest.get(
                latitude=latitude,
                longitude=longitude
            )
            return response.data
        except ResponseError as e:
            logger.error(f"Error fetching points of interest: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching points of interest: {e}")
        return None

    def get_tours_and_activities(self, city_code):
        try:
            response = self.amadeus.shopping.activities.get(
                location=city_code
            )
            return response.data
        except ResponseError as e:
            logger.error(f"Error fetching tours and activities: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching tours and activities: {e}")
        return None

    def search_city(self, keyword):
        try:
            response = self.amadeus.reference_data.locations.get(
                keyword=keyword,
                subType='CITY'
            )
            return response.data
        except ResponseError as e:
            logger.error(f"Error searching city: {e}")
        except Exception as e:
            logger.error(f"Unexpected error searching city: {e}")
        return None

    # Market Insights Services
    def get_most_travelled_destinations(self, origin):
        try:
            response = self.amadeus.travel.analytics.air_traffic.traveled.get(originCityCode=origin)
            return response.data
        except ResponseError as e:
            logger.error(f"Error fetching most travelled destinations: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching most travelled destinations: {e}")
        return None

    def get_most_booked_destinations(self, origin):
        try:
            response = self.amadeus.travel.analytics.air_traffic.booked.get(originCityCode=origin)
            return response.data
        except ResponseError as e:
            logger.error(f"Error fetching most booked destinations: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching most booked destinations: {e}")
        return None

    def get_busiest_travelling_period(self, origin, destination):
        try:
            response = self.amadeus.travel.analytics.air_traffic.busiest_period.get(
                originCityCode=origin,
                destinationCityCode=destination
            )
            return response.data
        except ResponseError as e:
            logger.error(f"Error fetching busiest travelling period: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching busiest travelling period: {e}")
        return None

    def get_location_score(self, location_id):
        try:
            response = self.amadeus.safety.safety_rated_locations.get(locationId=location_id)
            return response.data
        except ResponseError as e:
            logger.error(f"Error fetching location score: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching location score: {e}")
        return None

    # Hotel Services
    def search_hotels(self, city_code, check_in_date, check_out_date, guests=1):
        try:
            response = self.amadeus.shopping.hotel_offers.get(
                cityCode=city_code,
                checkInDate=check_in_date,
                checkOutDate=check_out_date,
                adults=guests
            )
            return response.data
        except ResponseError as e:
            logger.error(f"Error fetching hotel offers: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching hotel offers: {e}")
        return None

    def get_hotel_list(self, city_code):
        try:
            response = self.amadeus.reference_data.locations.hotels.by_city.get(cityCode=city_code)
            return response.data
        except ResponseError as e:
            logger.error(f"Error fetching hotel list: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching hotel list: {e}")
        return None

    def book_hotel(self, offer_id):
        try:
            response = self.amadeus.booking.hotel_bookings.post(offerId=offer_id)
            return response.data
        except ResponseError as e:
            logger.error(f"Error booking hotel: {e}")
        except Exception as e:
            logger.error(f"Unexpected error booking hotel: {e}")
        return None

    def get_hotel_ratings(self, hotel_id):
        try:
            response = self.amadeus.e_reputation.hotel_sentiments.get(hotelIds=hotel_id)
            return response.data
        except ResponseError as e:
            logger.error(f"Error fetching hotel ratings: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching hotel ratings: {e}")
        return None

    def autocomplete_hotel_name(self, keyword):
        try:
            response = self.amadeus.reference_data.locations.hotels.get(keyword=keyword)
            return response.data
        except ResponseError as e:
            logger.error(f"Error autocompleting hotel name: {e}")
        except Exception as e:
            logger.error(f"Unexpected error autocompleting hotel name: {e}")
        return None

    # Itinerary Management Services
    def parse_trip(self, trip_data):
        try:
            response = self.amadeus.travel.trip_parser_jobs.post(body=trip_data)
            return response.data
        except ResponseError as e:
            logger.error(f"Error parsing trip: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing trip: {e}")
        return None

    def predict_trip_purpose(self, trip_data):
        try:
            response = self.amadeus.travel.predictions.trip_purpose.post(body=trip_data)
            return response.data
        except ResponseError as e:
            logger.error(f"Error predicting trip purpose: {e}")
        except Exception as e:
            logger.error(f"Unexpected error predicting trip purpose: {e}")
        return None