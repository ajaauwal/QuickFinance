import os
import random
import string
import requests
import json
from dotenv import load_dotenv
from django.conf import settings
from django.views import View
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
# Forms
from .forms import (
    AirtimeRechargeForm,
    DataTopUpForm,
    SchoolFeesPaymentForm,
    FlightBookingForm,
    LoanApplicationForm,
    UtilityBillForm,
    FlightPaymentForm,
    RescheduleFlightForm,
    CancelFlightForm,
    FlightResultsForm,
    PayForServiceForm,
    WAECResultCheckerForm,
)

# Models
from .models import FlightBooking, Service
from apps.transactions.models import Wallet, Transaction

# Integrations
from paystackapi.paystack import Paystack
from .vtpass import VTPassAPI
from .amadeus import AmadeusService

# Load environment variables
load_dotenv()

# VTPass API credentials
VTPASS_BASE_URL = os.getenv('VTPASS_API_BASE_URL')
VTPASS_PUBLIC_KEY = os.getenv('VTPASS_PUBLIC_KEY')
VTPASS_SECRET_KEY = os.getenv('VTPASS_SECRET_KEY')

# Paystack API credentials
PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY')
PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
PAYSTACK_BASE_URL = os.getenv('PAYSTACK_BASE_URL', 'https://api.paystack.co/')
PAYSTACK_PAYMENT_URL = os.getenv('PAYSTACK_PAYMENT_URL', 'https://api.paystack.co/transaction/initialize')
PAYSTACK_TRANSFER_URL = os.getenv('PAYSTACK_TRANSFER_URL', 'https://api.paystack.co/transfer')
PAYSTACK_CALLBACK_URL = os.getenv('PAYSTACK_CALLBACK_URL')

# Amadeus API credentials
AMADEUS_API_KEY = os.getenv('AMADEUS_API_KEY')
AMADEUS_API_SECRET = os.getenv('AMADEUS_API_SECRET')



# Constants
NETWORK_PROVIDERS = [
    {'value': 'mtn', 'name': 'MTN', 'logo': 'images/mtn.png'},
    {'value': 'airtel', 'name': 'Airtel', 'logo': 'images/airtel.png'},
    {'value': '9mobile', 'name': '9Mobile', 'logo': 'images/9mobile.png'},
    {'value': 'glo', 'name': 'Glo', 'logo': 'images/glo.png'},
]

AIRTIME_CATEGORIES = {
    'mtn': [
        {'category': 'MTN 100', 'amount': 100},
        {'category': 'MTN 200', 'amount': 200},
        {'category': 'MTN 500', 'amount': 500},
    ],
    'airtel': [
        {'category': 'Airtel 100', 'amount': 100},
        {'category': 'Airtel 200', 'amount': 200},
        {'category': 'Airtel 500', 'amount': 500},
    ],
    '9mobile': [
        {'category': '9Mobile 100', 'amount': 100},
        {'category': '9Mobile 200', 'amount': 200},
        {'category': '9Mobile 500', 'amount': 500},
    ],
    'glo': [
        {'category': 'Glo 100', 'amount': 100},
        {'category': 'Glo 200', 'amount': 200},
        {'category': 'Glo 500', 'amount': 500},
    ],
}


class PurchaseAirtimeView(View):
    def get(self, request):
        """Handles GET requests for the airtime purchase page."""
        form = AirtimeRechargeForm()
        network_provider = request.GET.get('network_provider', 'mtn')  # Default to 'mtn'
        categories = AIRTIME_CATEGORIES.get(network_provider, [])
        
        # Fetch wallet and transactions for authenticated users
        wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None
        transactions = Transaction.objects.filter(user=request.user) if request.user.is_authenticated else []

        context = {
            'form': form,
            'wallet': wallet,
            'wallet_currencies': [
                {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
            ] if wallet else [],
            'transactions': transactions,
            'categories': categories,
            'network_provider': network_provider,
            'network_providers': NETWORK_PROVIDERS,
        }

        return render(request, 'services/purchase_airtime.html', context)

    def post(self, request):
        """Handles POST requests for processing airtime purchase."""
        form = AirtimeRechargeForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            network_provider = data['network_provider']
            amount = data['amount']
            phone_number = data['phone_number']
            payment_method = data['payment_method']

            if payment_method == 'wallet':
                return self._process_wallet_payment(request, amount, form)
            elif payment_method == 'debit_card':
                return self._process_debit_card_payment(request, network_provider, phone_number, amount)

        # Handle invalid form submission
        network_provider = request.POST.get('network_provider', 'mtn')
        categories = AIRTIME_CATEGORIES.get(network_provider, [])
        context = {
            'form': form,
            'categories': categories,
            'network_provider': network_provider,
            'network_providers': NETWORK_PROVIDERS,
        }
        return render(request, 'services/purchase_airtime.html', context)

    def _process_wallet_payment(self, request, amount, form):
        """Processes payment using wallet balance."""
        wallet = get_object_or_404(Wallet, user=request.user)
        if wallet.balance >= amount:
            wallet.balance -= amount
            wallet.save()

            # Save the form with user association
            airtime_purchase = form.save(commit=False)
            airtime_purchase.user = request.user
            airtime_purchase.save()

            # Record the transaction
            Transaction.objects.create(
                user=request.user,
                service="Airtime Purchase",
                amount=amount,
                payment_method='wallet',
                wallet=wallet
            )
            messages.success(request, "Airtime purchase successful via wallet.")
        else:
            messages.error(request, "Insufficient wallet balance.")
        return redirect('services:purchase_airtime')

    def _process_debit_card_payment(self, request, network_provider, phone_number, amount):
        """Processes payment using debit card via VTPass API."""
        vtpass = VTPassAPI()
        response = vtpass.purchase_airtime(
            provider=network_provider,
            number=phone_number,
            amount=amount,
            reference="unique_transaction_reference"
        )
        if response.get('status') == 'success':
            Transaction.objects.create(
                user=request.user,
                service="Airtime Purchase",
                amount=amount,
                payment_method='debit_card'
            )
            messages.success(request, "Airtime purchase successful via debit card.")
        else:
            error_message = response.get('message', "Error processing debit card payment.")
            messages.error(request, error_message)
        return redirect('services:purchase_airtime')




class DataTopUpView(View):
    def get(self, request):
        """ Handles the GET request to load the data top-up form """
        form = DataTopUpForm()

        wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None
        transactions = Transaction.objects.filter(user=request.user) if request.user.is_authenticated else []

        context = {
            'form': form,
            'wallet': wallet,
            'wallet_currencies': [
                {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
            ] if wallet else [],
            'transactions': transactions,
            'network_providers': NETWORK_PROVIDERS,
        }

        return render(request, 'services/data_topup.html', context)

    def post(self, request):
        """ Handles the POST request for data top-up """
        form = DataTopUpForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            amount = data['amount']
            payment_method = data['payment_method']

            if payment_method == 'wallet':
                return self._process_wallet_payment(request, amount, form)

            elif payment_method == 'debit_card':
                return self._process_debit_card_payment(request, data)

        # If form is invalid, re-render the form with errors
        messages.error(request, "Please correct the errors below.")
        return render(request, 'services/data_topup.html', {'form': form})

    def _process_wallet_payment(self, request, amount, form):
        """ Processes data top-up using wallet payment """
        wallet = get_object_or_404(Wallet, user=request.user)
        
        if wallet.balance < amount:
            messages.error(request, "Insufficient wallet balance.")
            return redirect('services:data_topup')

        # Deduct from wallet balance
        wallet.balance -= amount
        wallet.save()

        # Save the form with user assignment
        topup = form.save(commit=False)
        topup.user = request.user
        topup.save()

        # Create a transaction record
        Transaction.objects.create(
            user=request.user,
            service=topup.service,
            amount=amount,
            payment_method='wallet'
        )

        messages.success(request, "Data top-up successful via wallet.")
        return redirect('services:data_topup')

    def _process_debit_card_payment(self, request, data):
        """ Processes data top-up using debit card (VTPass API) """
        vtpass = VTPassAPI()
        response = vtpass.purchase_data_plan(
            provider=data['provider'],
            number=data['phone_number'],
            plan=data['data_plan'],
            reference="unique_transaction_reference"
        )

        if response.get('status') == 'success':
            messages.success(request, "Data top-up successful via debit card.")
        else:
            messages.error(request, response.get('message', 'Error processing payment'))

        return redirect('services:data_topup')



class FlightBookingView(View):
    def get(self, request):
        form = FlightBookingForm()
        
        # Fetch the user's wallet and transactions if authenticated
        wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None
        transactions = Transaction.objects.filter(user=request.user)  # Filter by user
        
        # Context for rendering the page
        context = {
            'form': form,
            'wallet': wallet,
            'wallet_currencies': [
                {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
            ] if wallet else [],
            'transactions': transactions,
            }
        return render(request, 'services/flight_booking.html', context)

    def post(self, request):
        form = FlightBookingForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            origin = data['departure_city']
            destination = data['arrival_city']
            departure_date = data['departure_date']
            return_date = data['return_date']
            adults = data['number_of_passengers']
            children = data.get('children', 0)
            infants = data.get('infants', 0)

            # Using the AmadeusService for flight search
            amadeus_service = AmadeusService()
            flights = amadeus_service.search_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                adults=adults,
                children=children,
                infants=infants
            )

            if flights:
                return render(request, 'services/flight_results.html', {'flights': flights})
            else:
                return JsonResponse({"error": "No flights found"}, status=400)
        
        return render(request, 'services/flight_booking.html', {'form': form})

import os
import requests
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views import View
from .forms import FlightPaymentForm
from .models import Wallet

PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
PAYSTACK_PAYMENT_URL = "https://api.paystack.co/transaction/initialize"

class FlightPaymentView(View):
    def post(self, request):
        form = FlightPaymentForm(request.POST)
        if form.is_valid():
            flight_id = form.cleaned_data['flight_id']
            amount = form.cleaned_data['amount']
            payment_method = form.cleaned_data['payment_method']
            user = request.user

            if payment_method == 'wallet':
                try:
                    wallet = Wallet.objects.get(user=user)
                    if wallet.balance >= amount:
                        wallet.balance -= amount
                        wallet.save()
                        # Save the flight booking to the database
                        return redirect('services:flight_booked')
                    else:
                        return JsonResponse({"error": "Insufficient wallet balance"}, status=400)
                except Wallet.DoesNotExist:
                    return JsonResponse({"error": "Wallet not found"}, status=400)

            elif payment_method == 'debit_card':
                headers = {
                    "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                    "Content-Type": "application/json",
                }
                data = {
                    "email": user.email,
                    "amount": int(amount) * 100,  # Convert to kobo
                    "callback_url": "https://maaunquickfinance.com/paystack/callback",
                    "metadata": {
                        "user_id": user.id,
                        "flight_id": flight_id
                    }
                }
                response = requests.post(PAYSTACK_PAYMENT_URL, json=data, headers=headers)
                response_data = response.json()

                if response_data.get('status'):
                    return redirect(response_data['data']['authorization_url'])
                else:
                    return JsonResponse({"error": response_data.get('message', 'Error processing payment')}, status=400)

        return redirect('services:flight_results')


class RescheduleFlightView(View):
    def post(self, request):
        form = RescheduleFlightForm(request.POST)
        if form.is_valid():
            flight_id = form.cleaned_data['flight_id']
            new_date = form.cleaned_data['new_date']
            # Process rescheduling
            return redirect('services:flight_results')
        return redirect('services:flight_results')

class CancelFlightView(View):
    def post(self, request):
        form = CancelFlightForm(request.POST)
        if form.is_valid():
            flight_id = form.cleaned_data['flight_id']
            cancel_reason = form.cleaned_data['cancel_reason']
            # Process cancellation
            return redirect('services:flight_cancelled')
        return redirect('services:flight_results')

class FlightBookedView(View):
    def get(self, request):
        return render(request, 'services/flight_booked.html')

class FlightCancelledView(View):
    def get(self, request):
        return render(request, 'services/flight_cancelled.html')

import os
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views import View
from .forms import FlightResultsForm
from .models import Wallet, FlightBooking

PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
PAYSTACK_PAYMENT_URL = "https://api.paystack.co/transaction/initialize"

class FlightResultsView(View):
    def get(self, request):
        form = FlightResultsForm()
        return render(request, 'services/flight_results.html', {'form': form})

    def post(self, request):
        form = FlightResultsForm(request.POST)
        if form.is_valid():
            flight_id = form.cleaned_data.get('flight_id')
            amount = form.cleaned_data.get('amount')
            payment_method = form.cleaned_data.get('payment_method')
            new_date = form.cleaned_data.get('new_date')
            cancel_reason = form.cleaned_data.get('cancel_reason')
            booking_reference = form.cleaned_data.get('booking_reference')
            user = request.user

            if new_date:
                # Reschedule the flight
                flight = get_object_or_404(FlightBooking, flight_id=flight_id, user=user)
                flight.new_date = new_date
                flight.save()
                return redirect('services:flight_results')

            if cancel_reason:
                # Cancel the flight
                flight = get_object_or_404(FlightBooking, flight_id=flight_id, user=user)
                flight.cancel_reason = cancel_reason
                flight.status = 'Cancelled'
                flight.save()
                return redirect('services:flight_cancelled')

            if payment_method == 'wallet':
                try:
                    wallet = Wallet.objects.get(user=user)
                    if wallet.balance >= amount:
                        wallet.balance -= amount
                        wallet.save()
                        return redirect('services:flight_booked')
                    else:
                        return JsonResponse({"error": "Insufficient wallet balance"}, status=400)
                except Wallet.DoesNotExist:
                    return JsonResponse({"error": "Wallet not found"}, status=400)

            elif payment_method == 'debit_card':
                headers = {
                    "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                    "Content-Type": "application/json",
                }
                data = {
                    "email": user.email,
                    "amount": int(amount) * 100,  # Convert to kobo
                    "callback_url": "https://maaunquickfinance.com/paystack/callback",
                    "metadata": {
                        "user_id": user.id,
                        "flight_id": flight_id
                    }
                }
                response = requests.post(PAYSTACK_PAYMENT_URL, json=data, headers=headers)
                response_data = response.json()

                if response_data.get('status'):
                    return redirect(response_data['data']['authorization_url'])
                else:
                    return JsonResponse({"error": response_data.get('message', 'Error processing payment')}, status=400)

        return redirect('services:flight_results')

class FlightDetailView(View):
    def get(self, request, flight_id):
        flight = get_object_or_404(FlightBooking, flight_id=flight_id)
        data = {
            'flight_id': flight.flight_id,
            'amount': flight.amount,
            'payment_method': flight.payment_method,
            'status': flight.status,
            'booking_date': flight.booking_date,
            'cancel_reason': flight.cancel_reason,
            'new_date': flight.new_date,
            'booking_reference': flight.booking_reference,
        }
        return JsonResponse(data)

class AmadeusService:
    def search_flights(self, origin, destination, departure_date, return_date, adults, children, infants):
        # Placeholder logic for searching flights
        return [
            {'flight_number': 'AA123', 'origin': origin, 'destination': destination, 'departure_date': departure_date, 'return_date': return_date, 'price': 500},
            {'flight_number': 'BA456', 'origin': origin, 'destination': destination, 'departure_date': departure_date, 'return_date': return_date, 'price': 600},
        ]

    def destination_experiences(self, point_of_interest, tours_and_activities, city_search):
        """ Fetch destination experiences for a given city code. """
        return [
            {'title': 'Statue of Liberty Tour', 'description': 'Visit the iconic Statue of Liberty.', 'price': 25},
            {'title': 'Broadway Show', 'description': 'Enjoy a world-class Broadway show.', 'price': 100},
        ]

    def cars_transfers(self, transfer_booking, transfer_management, transfer_search):
        """ Fetch available car transfers. """
        return [
            {'car': 'Sedan', 'price': 50, 'availability': 'Available'},
            {'car': 'SUV', 'price': 80, 'availability': 'Available'},
            {'car': 'Luxury', 'price': 150, 'availability': 'Limited'},
        ]

    def market_insights(self, flight_most_travelled_destinations, flight_most_booked_destinantions, flight_busiest_travelling_period, location_store):
        """ Fetch market insights. """
        return {
            'top_destinations': ['New York', 'Paris', 'Tokyo'],
            'average_flight_cost': 500,
            'peak_season': 'Summer',
        }

    def hotels(self, hotel_list, hotel_search, hotel_booking, hotel_ratings, hotel_name_autocomplete):
        """ Fetch available hotels. """
        return [
            {'name': 'Grand Hotel', 'location': 'Downtown NYC', 'price': 200, 'rating': 4.5},
            {'name': 'Budget Inn', 'location': 'Brooklyn', 'price': 80, 'rating': 3.8},
            {'name': 'Luxury Suites', 'location': 'Midtown Manhattan', 'price': 500, 'rating': 5.0},
        ]

    def itinerary_management(self, trip_parser, trip_purpose_prediction):
        """ Fetch itinerary details for management. """
        return {
            'flights': [{'departure': 'JFK', 'arrival': 'LAX', 'time': '10:00 AM'}],
            'hotels': [{'name': 'Grand Hotel', 'check_in': '2024-01-10', 'check_out': '2024-01-15'}],
            'activities': [{'title': 'City Tour', 'time': '2:00 PM'}],
        }


def get_loan(request): 
    wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None
    transactions = Transaction.objects.filter(user=request.user) if request.user.is_authenticated else []
    
    if request.method == 'POST':
        form = LoanApplicationForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.user = request.user
            loan.save()
            return redirect('services:loan_success')
    else:
        form = LoanApplicationForm()
    
    # Context for rendering the page
    context = {
        'form': form,
        'wallet': wallet,
        'wallet_currencies': [
            {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
        ] if wallet else [],
        'transactions': transactions,
    }
    
    return render(request, 'services/get_loan.html', context)

def loan_success(request):
    return render(request, 'services/loan_success.html')




class SchoolFeesPaymentView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')  # Redirect unauthenticated users

        form = SchoolFeesPaymentForm()
        wallet = get_object_or_404(Wallet, user=request.user)
        transactions = Transaction.objects.filter(user=request.user)

        context = {
            'form': form,
            'wallet': wallet,
            'wallet_currencies': [
                {"currency": "NGN", "symbol": "₦", "balance": wallet.balance}
            ],
            'transactions': transactions,
        }
        return render(request, 'services/school_fees_payment.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login')  # Redirect unauthenticated users
        
        form = SchoolFeesPaymentForm(request.POST)
        wallet = get_object_or_404(Wallet, user=request.user)

        if form.is_valid():
            amount = form.cleaned_data['amount']
            if wallet.balance >= amount:
                # Deduct amount from wallet
                wallet.balance -= amount
                wallet.save()

                # Log transaction
                Transaction.objects.create(
                    user=request.user, 
                    amount=amount, 
                    description="School Fees Payment"
                )

                return redirect('services:school_fees_payment_success')  # Redirect on success
            else:
                form.add_error(None, "Insufficient balance")

        # If form is invalid, re-render the page
        transactions = Transaction.objects.filter(user=request.user)
        context = {
            'form': form,
            'wallet': wallet,
            'wallet_currencies': [{"currency": "NGN", "symbol": "₦", "balance": wallet.balance}],
            'transactions': transactions,
        }
        return render(request, 'services/school_fees_payment.html', context)

# Success Page View
def school_fees_payment_success(request):
    return render(request, 'services/school_fees_payment_success.html')




from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView
from .models import Service

class ServiceDetailView(DetailView):
    model = Service
    template_name = "services/service_detail.html"
    context_object_name = "service"

    def get(self, request, *args, **kwargs):
        service = get_object_or_404(Service, slug=self.kwargs.get("slug"))
        return redirect(service.get_absolute_url())  # Redirecting to the service URL




# Standalone function to process Paystack payment
def process_paystack_payment(amount, email, card_details):
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    url = "https://api.paystack.co/transaction/initialize"
    
    data = {
        "amount": int(amount * 100),  # Amount in kobo
        "email": email,
        "card": card_details,
        "currency": "NGN",
    }
    
    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()
    
    if response_data["status"] == "success":
        # Return the authorization URL if successful
        verification_url = response_data["data"]["authorization_url"]
        return {"status": "success", "verification_url": verification_url}
    
    return {"status": "failure", "message": response_data["message"]}

# Payment views for specific services
def electricity_payment(request):
    wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None 
    transactions = Transaction.objects.filter(user=request.user) if request.user.is_authenticated else []

    if request.method == 'POST':
        form = UtilityBillForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            amount = data['amount']
            payment_method = data['payment_method']
            user = request.user

            if payment_method == 'wallet':
                if wallet.balance >= amount:
                    wallet.balance -= amount
                    wallet.save()
                    form.save(commit=False)
                    form.instance.user = user
                    form.save()
                    return redirect('services:electricity_payment_success')
                else:
                    return JsonResponse({"error": "Insufficient wallet balance"}, status=400)
            elif payment_method == 'debit_card':
                response = process_paystack_payment(  # Call the function directly
                    amount=amount,
                    email=data['email'],
                    card_details=data['card_details']
                )
                if response.get('status') == "success":
                    return redirect('services:electricity_payment_success')
                else:
                    return JsonResponse({"error": response.get('message', 'Error processing payment')}, status=400)
    else:
        form = UtilityBillForm()

    context = {
        'form': form,
        'wallet': wallet,
        'wallet_currencies': [
            {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
        ] if wallet else [],
        'transactions': transactions,
    }

    return render(request, 'services/electricity_payment.html', context)

def electricity_payment_success(request):
    return render(request, 'services/electricity_payment_success.html')

def dstv_payment(request):
    wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None 
    transactions = Transaction.objects.filter(user=request.user) if request.user.is_authenticated else []

    if request.method == 'POST':
        form = UtilityBillForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            amount = data['amount']
            payment_method = data['payment_method']
            user = request.user

            if payment_method == 'wallet':
                if wallet.balance >= amount:
                    wallet.balance -= amount
                    wallet.save()
                    form.save(commit=False)
                    form.instance.user = user
                    form.save()
                    return redirect('services:dstv_payment_success')
                else:
                    return JsonResponse({"error": "Insufficient wallet balance"}, status=400)
            elif payment_method == 'debit_card':
                response = process_paystack_payment(
                    amount=amount,
                    email=data['email'],
                    card_details=data['card_details']
                )
                if response.get('status') == "success":
                    return redirect('services:dstv_payment_success')
                else:
                    return JsonResponse({"error": response.get('message', 'Error processing payment')}, status=400)
    else:
        form = UtilityBillForm()

    context = {
        'form': form,
        'wallet': wallet,
        'wallet_currencies': [
            {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
        ] if wallet else [],
        'transactions': transactions,
    }

    return render(request, 'services/dstv_payment.html', context)

def dstv_payment_success(request):
    return render(request, 'services/dstv_payment_success.html')

def gotv_payment(request):
    wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None 
    transactions = Transaction.objects.filter(user=request.user) if request.user.is_authenticated else []

    if request.method == 'POST':
        form = UtilityBillForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            amount = data['amount']
            payment_method = data['payment_method']
            user = request.user

            if payment_method == 'wallet':
                if wallet.balance >= amount:
                    wallet.balance -= amount
                    wallet.save()
                    form.save(commit=False)
                    form.instance.user = user
                    form.save()
                    return redirect('services:gotv_payment_success')
                else:
                    return JsonResponse({"error": "Insufficient wallet balance"}, status=400)
            elif payment_method == 'debit_card':
                response = process_paystack_payment(
                    amount=amount,
                    email=data['email'],
                    card_details=data['card_details']
                )
                if response.get('status') == "success":
                    return redirect('services:gotv_payment_success')
                else:
                    return JsonResponse({"error": response.get('message', 'Error processing payment')}, status=400)
    else:
        form = UtilityBillForm()

    context = {
        'form': form,
        'wallet': wallet,
        'wallet_currencies': [
            {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
        ] if wallet else [],
        'transactions': transactions,
    }

    return render(request, 'services/gotv_payment.html', context)

def gotv_payment_success(request):
    return render(request, 'services/gotv_payment_success.html')

def startimes_payment(request):
    wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None 
    transactions = Transaction.objects.filter(user=request.user) if request.user.is_authenticated else []

    if request.method == 'POST':
        form = UtilityBillForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            amount = data['amount']
            payment_method = data['payment_method']
            user = request.user

            if payment_method == 'wallet':
                if wallet.balance >= amount:
                    wallet.balance -= amount
                    wallet.save()
                    form.save(commit=False)
                    form.instance.user = user
                    form.save()
                    return redirect('services:startimes_payment_success')
                else:
                    return JsonResponse({"error": "Insufficient wallet balance"}, status=400)
            elif payment_method == 'debit_card':
                response = process_paystack_payment(
                    amount=amount,
                    email=data['email'],
                    card_details=data['card_details']
                )
                if response.get('status') == "success":
                    return redirect('services:startimes_payment_success')
                else:
                    return JsonResponse({"error": response.get('message', 'Error processing payment')}, status=400)
    else:
        form = UtilityBillForm()

    context = {
        'form': form,
        'wallet': wallet,
        'wallet_currencies': [
            {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
        ] if wallet else [],
        'transactions': transactions,
    }

    return render(request, 'services/startimes_payment.html', context)

def startimes_payment_success(request):
    return render(request, 'services/startimes_payment_success.html')

from django.http import JsonResponse
from django.db.models import Q
from .models import Service

def search_view(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        services = Service.objects.filter(Q(name__icontains=query))[:5]  # Limit results to 5
        results = [{"id": s.id, "name": s.name, "category": s.category} for s in services]

    return JsonResponse({"results": results})






class WAECResultCheckerView(View):
    def get(self, request):
        """Displays the WAEC Result Checker form."""
        form = WAECResultCheckerForm()
        wallet, transactions = None, None

        if request.user.is_authenticated:
            wallet, _ = Wallet.objects.get_or_create(user=request.user)  # Ensure wallet exists
            transactions = Transaction.objects.filter(user=request.user)

        context = {
            'form': form,
            'wallet': wallet,
            'wallet_currencies': [
                {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
            ] if wallet else [],
            'transactions': transactions or [],
        }
        return render(request, 'services/waec_result_checker.html', context)

    def post(self, request):
        """Processes the WAEC Result Checker form submission."""
        form = WAECResultCheckerForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = request.user
            payment_method = data['payment_method']
            email = data['email']

            if payment_method == 'wallet':
                wallet = get_object_or_404(Wallet, user=user)
                if wallet.balance >= 500:  # Example cost for WAEC PIN
                    wallet.balance -= 500
                    wallet.save()

                    # Generate WAEC PIN and log transaction
                    result_pin = self._generate_waec_result_pin()
                    self._log_transaction(user, 'WAEC Result Checker', 500)

                    return JsonResponse({"success": True, "pin": result_pin})
                return JsonResponse({"error": "Insufficient wallet balance"}, status=400)

            elif payment_method == 'debit_card':
                paystack_response = self._process_paystack_payment(500, email)
                if paystack_response.get('status') == "success":
                    return JsonResponse({"success": True, "redirect_url": paystack_response['verification_url']})
                return JsonResponse({"error": paystack_response.get('message', 'Error processing payment')}, status=400)

        return render(request, 'services/waec_result_checker.html', {'form': form})

    def _generate_waec_result_pin(self):
        """Generates a random 12-character alphanumeric PIN for WAEC result checking."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

    def _process_paystack_payment(self, amount, email):
        """Initializes Paystack payment and returns the redirection URL."""
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "amount": int(amount * 100),  # Convert amount to kobo
            "email": email,
            "currency": "NGN",
            "callback_url": "https://maaunquickfinance.com/paystack/callback",
        }

        response = requests.post(PAYSTACK_PAYMENT_URL, json=data, headers=headers)
        response_data = response.json()

        if response_data.get("status") is True:
            return {"status": "success", "verification_url": response_data["data"]["authorization_url"]}

        return {"status": "failure", "message": response_data.get("message", "Error processing payment")}

    def _log_transaction(self, user, description, amount):
        """Logs a transaction in the database."""
        Transaction.objects.create(
            user=user,
            description=description,
            amount=amount,
            transaction_type="debit"
        )





class PayForServiceView(View):
    def get(self, request):
        # Display the form for selecting the service and payment method
        form = PayForServiceForm()
        wallet = None
        transactions = []

        if request.user.is_authenticated:
            wallet, _ = Wallet.objects.get_or_create(user=request.user)  # Ensure wallet exists
            transactions = Transaction.objects.filter(user=request.user)

        context = {
            'form': form,
            'wallet': wallet,
            'wallet_currencies': [
                {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
            ] if wallet else [],
            'transactions': transactions,
        }
        return render(request, 'services/pay_for_service.html', context)

    def post(self, request):
        form = PayForServiceForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            amount = data['amount']
            payment_method = data['payment_method']
            user = request.user

            if payment_method == 'wallet':
                wallet, _ = Wallet.objects.get_or_create(user=user)  # Ensure wallet exists
                if wallet.balance >= amount:
                    wallet.balance -= amount
                    wallet.save()
                    form.instance.user = user
                    form.save()
                    self._log_transaction(user, 'Service Payment', amount)
                    return redirect('services:payment_success')
                else:
                    return JsonResponse({"error": "Insufficient wallet balance"}, status=400)

            elif payment_method == 'debit_card':
                response = self._process_paystack_payment(amount, data['email'], data['card_details'])
                if response.get('status') == 'success':
                    self._log_transaction(user, 'Service Payment', amount)
                    return redirect('services:payment_success')
                else:
                    return JsonResponse({"error": response.get('message', 'Error processing payment')}, status=400)

        return render(request, 'services/pay_for_service.html', {'form': form})

    def _process_paystack_payment(self, amount, email, card_details):
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        url = "https://api.paystack.co/transaction/initialize"
        
        data = {
            "amount": int(amount * 100),  # Amount in kobo
            "email": email,
            "card": card_details,
            "currency": "NGN",
        }
        
        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()
        
        if response_data["status"] == "success":
            # Verify the transaction after successful initialization
            verification_url = response_data["data"]["authorization_url"]
            return {"status": "success", "verification_url": verification_url}
        
        return {"status": "failure", "message": response_data["message"]}

    def _log_transaction(self, user, description, amount):
        # Log the transaction (this could be saved in your `Transaction` model)
        Transaction.objects.create(
            user=user,
            description=description,
            amount=amount,
            transaction_type="debit"
        )


def payment_success(request):
    return render(request, 'services/payment_success.html')


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import logging
from apps.services.models import Service
from apps.transactions.models import Wallet, Transaction

logger = logging.getLogger(__name__)

@login_required
def utility_bills(request):
    services = Service.objects.filter(category="Bills")  # Fetch services under "Bills"
    
    # Retrieve or create the wallet
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Ensure wallet is a Wallet instance
    if not isinstance(wallet, Wallet):
        logger.error(f"Unexpected wallet type: {type(wallet)}. Attempting to refetch.")
        wallet = Wallet.objects.filter(user=request.user).first()

    # Handle the case where wallet is still invalid
    if not wallet:
        logger.error("Failed to retrieve a valid Wallet instance. Returning empty transactions.")
        transactions = Transaction.objects.none()
        wallet_balance = 0.0
    else:
        transactions = Transaction.objects.filter(wallet=wallet)
        wallet_balance = wallet.balance

    context = {
        'services': services,
        'wallet': wallet,
        'wallet_currencies': [{"currency": "NGN", "symbol": "₦", "balance": wallet_balance}],
        'transactions': transactions,
    }

    return render(request, 'services/utility_bills.html', context)


def service_details(request, slug):
    service = get_object_or_404(Service, slug=slug)
    return render(request, 'services/service_details.html', {'service': service})
