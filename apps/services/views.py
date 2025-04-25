from django.views import View
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
import os
import requests
from dotenv import load_dotenv

# Forms
from .forms import (
    AirtimeRechargeForm,
    DataTopUpForm,
    SchoolFeesPaymentForm,
    FlightBookingForm,
    LoanApplicationForm,
    UtilityBillsForm,
    FlightPaymentForm,
    RescheduleFlightForm,
    CancelFlightForm,
    FlightResultsForm,
    WAECResultCheckerForm,
)

# Models
from .models import FlightBooking, Service
from apps.transactions.models import Wallet, Transaction

# Integrations
from .paystack import PaystackAPI
from .vtpass import VTPassAPI
from .amadeus import AmadeusService
from django.conf import settings
import random
import string
import requests
from django.conf import settings



# Load environment variables
load_dotenv()

# VTPass API credentials from .env
VTPASS_API_KEY = os.getenv("VTPASS_API_KEY")
VTPASS_SECRET_KEY = os.getenv("VTPASS_SECRET_KEY")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")


def process_vtpass_payment(service_code, amount, email, phone_number):
    """
    Process payment with VTPass using details from the environment.
    """
    headers = {
        'Authorization': f'Bearer {settings.VTPASS_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "service_code": service_code,  # Service code (electricity, DSTV, etc.)
        "amount": amount,  # Amount to be paid
        "email": email,  # User's email
        "phone_number": phone_number  # User's phone number
    }
    
    response = requests.post(settings.VTPASS_API_URL, json=data, headers=headers)
    
    if response.status_code == 200:
        return response.json()  # Returns the response in JSON format
    else:
        return {"status": "failure", "message": "Error processing VTPass payment"}





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
        vtpass = VTPassAPI()  # Instantiate the VTPass SDK
        
        response = vtpass.purchase_airtime(
            provider=network_provider,
            number=phone_number,
            amount=amount,
            reference="unique_transaction_reference"
        )
        
        if response.get('status') == 'success':
            # Record the transaction
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
        form = DataTopUpForm()

        wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None
        transactions = Transaction.objects.filter(user=request.user)

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
        form = DataTopUpForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            amount = data['amount']
            payment_method = data['payment_method']
            user = request.user

            if payment_method == 'wallet':
                return self._process_wallet_payment(request, amount, form)

            elif payment_method == 'debit_card':
                return self._process_debit_card_payment(request, data)

        return render(request, 'services/data_topup.html', {'form': form})

    def _process_wallet_payment(self, request, amount, form):
        wallet = get_object_or_404(Wallet, user=request.user)
        if wallet.balance >= amount:
            wallet.balance -= amount
            wallet.save()

            form.save(commit=False)
            form.instance.user = request.user
            form.save()

            Transaction.objects.create(
                user=request.user,
                service=form.instance.service,
                amount=amount,
                payment_method='wallet'
            )
            messages.success(request, "Data top-up successful via wallet.")
            return redirect('services:data_topup')
        else:
            messages.error(request, "Insufficient wallet balance.")
            return redirect('services:data_topup')

    def _process_debit_card_payment(self, request, data):
        vtpass = VTPassAPI()  # Instantiate the VTPass SDK
        response = vtpass.purchase_data_plan(
            provider=data['provider'],
            number=data['phone_number'],
            plan=data['data_plan'],
            reference="unique_transaction_reference"
        )
        
        if response.get('status') == 'success':
            messages.success(request, "Data top-up successful via debit card.")
            return redirect('services:data_topup')
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

class FlightPaymentView(View):
    def post(self, request):
        form = FlightPaymentForm(request.POST)
        if form.is_valid():
            flight_id = form.cleaned_data['flight_id']
            amount = form.cleaned_data['amount']
            payment_method = form.cleaned_data['payment_method']
            user = request.user

            if payment_method == 'wallet':
                wallet = Wallet.objects.get(user=user)
                if wallet.balance >= amount:
                    wallet.balance -= amount
                    wallet.save()
                    # Save the flight booking to the database
                    return redirect('services:flight_booked')
                else:
                    return JsonResponse({"error": "Insufficient wallet balance"}, status=400)
            elif payment_method == 'debit_card':
                paystack = PaystackAPI()
                response = paystack.initialize_transaction(
                    reference="unique_transaction_reference",
                    amount=amount,
                    email=user.email,
                    callback_url="https://maaunquickfinance.com/paystack/callback",
                    metadata={"user_id": user.id}
                )
                if response.get('status'):
                    return redirect(response['data']['authorization_url'])
                else:
                    return JsonResponse({"error": response.get('message', 'Error processing payment')}, status=400)
        
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

class FlightResultsView(View):
    def get(self, request):
        form = FlightResultsForm()
        return render(request, 'services/flight_results.html')

    def post(self, request):
        form = FlightResultsForm(request.POST)
        if form.is_valid():
            flight_id = form.cleaned_data['flight_id']
            amount = form.cleaned_data['amount']
            payment_method = form.cleaned_data['payment_method']
            new_date = form.cleaned_data['new_date']
            cancel_reason = form.cleaned_data['cancel_reason']
            booking_reference = form.cleaned_data['booking_reference']
            user = request.user

            if payment_method == 'wallet':
                wallet = Wallet.objects.get(user=user)
                if wallet.balance >= amount:
                    wallet.balance -= amount
                    wallet.save()
                    # Save the flight booking to the database
                    return redirect('services:flight_booked')
                else:
                    return JsonResponse({"error": "Insufficient wallet balance"}, status=400)
            elif payment_method == 'debit_card':
                paystack = PaystackAPI()
                response = paystack.initialize_transaction(
                    reference="unique_transaction_reference",
                    amount=amount,
                    email=user.email,
                    callback_url="https://maaunquickfinance.com/paystack/callback",
                    metadata={"user_id": user.id}
                )
                if response.get('status'):
                    return redirect(response['data']['authorization_url'])
                else:
                    return JsonResponse({"error": response.get('message', 'Error processing payment')}, status=400)
            elif new_date:
                # Process rescheduling
                flight = get_object_or_404(FlightBooking, flight_id=flight_id)
                flight.new_date = new_date
                flight.save()
                return redirect('services:flight_results')
            elif cancel_reason:
                # Process cancellation
                flight = get_object_or_404(FlightBooking, flight_id=flight_id)
                flight.cancel_reason = cancel_reason
                flight.status = 'Cancelled'
                flight.save()
                return redirect('services:flight_cancelled')
        
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
        form = SchoolFeesPaymentForm()
        wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None
        transactions = Transaction.objects.filter(user=request.user) if request.user.is_authenticated else []
        context = {
            'form': form,
            'wallet': wallet,
            'wallet_currencies': [
                {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
            ] if wallet else [],
            'transactions': transactions,
        }
        return render(request, 'services/school_fees_payment.html', context)

    def post(self, request):
        form = SchoolFeesPaymentForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            amount = data['amount']
            payment_method = data['payment_method']
            user = request.user

            if payment_method == 'wallet':
                wallet = Wallet.objects.get(user=user)
                if wallet.balance >= amount:
                    wallet.balance -= amount
                    wallet.save()
                    form.save(commit=False)
                    form.instance.user = user
                    form.save()
                    return redirect('services:school_fees_payment_success')
                else:
                    return JsonResponse({"error": "Insufficient wallet balance"}, status=400)
            
            elif payment_method == 'debit_card':
                vtpass = VTPassAPI()  # Assuming this is your VTPass SDK wrapper
                response = vtpass.pay_school_fees(
                    user_id=user.id,
                    amount=amount,
                    reference="unique_transaction_reference",
                    email=user.email
                )

                if response.get('status') == 'success':
                    # Log the successful transaction
                    Transaction.objects.create(
                        user=user,
                        service="School Fees Payment",
                        amount=amount,
                        payment_method='debit_card',
                        status='success'
                    )
                    return redirect('services:school_fees_payment_success')
                else:
                    return JsonResponse({"error": response.get('message', 'Error processing payment')}, status=400)

        return render(request, 'services/school_fees_payment.html', {'form': form})

def school_fees_payment_success(request):
    return render(request, 'services/school_fees_payment_success.html')





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

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UtilityBills
from .forms import UtilityBillsForm

@login_required
def utility_bills(request):
    user = request.user
    wallet = get_object_or_404(Wallet, user=user)
    transactions = Transaction.objects.filter(user=user).order_by('-created_at')

    if request.method == 'POST':
        form = UtilityBillsForm(request.POST)
        if form.is_valid():
            provider = form.cleaned_data['provider']
            account_number = form.cleaned_data['account_number']
            amount = form.cleaned_data['amount']
            email = form.cleaned_data['email']

            # Check wallet balance
            if wallet.balance >= amount:
                wallet.balance -= amount
                wallet.save()

                # Save to UtilityBills
                UtilityBills.objects.create(
                    user=user,
                    service_type=provider,
                    account_number=account_number,
                    amount=amount,
                    cable_provider=provider,  # Optional; reused here
                    payment_method='wallet',
                )

                # Log transaction
                Transaction.objects.create(
                    user=user,
                    service=provider,
                    amount=amount,
                    payment_method='wallet',
                    status='success'
                )

                messages.success(request, f"{provider.title()} bill paid successfully using wallet.")
                return redirect('utility_bills_history')
            else:
                messages.error(request, "Insufficient wallet balance.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = UtilityBillsForm()

    context = {
        'form': form,
        'wallet': wallet,
        'wallet_currencies': [
            {"currency": "NGN", "symbol": "₦", "balance": wallet.balance}
        ],
        'transactions': transactions,
    }

    return render(request, 'services/utility_bills.html', context)



@login_required
def utility_bills_history(request):
    bills = UtilityBills.objects.filter(user=request.user).order_by('-date_created')
    return render(request, 'services/utility_bills_history.html', {'bills': bills})



def electricity_payment(request):
    wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None 
    transactions = Transaction.objects.filter(user=request.user) if request.user.is_authenticated else []

    if request.method == 'POST':
        form = UtilityBillsForm(request.POST)
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
                response = process_paystack_payment(
                    amount=amount,
                    email=data['email'],
                    card_details=data['card_details']
                )
                if response.get('status') == "success":
                    return redirect('services:electricity_payment_success')
                else:
                    return JsonResponse({"error": response.get('message', 'Error processing payment')}, status=400)
            elif payment_method == 'vtpass':
                vtpass_service_code = "electricity_service_code"  # Replace with actual VTPass service code for Electricity
                response = process_vtpass_payment(
                    service_code=vtpass_service_code,
                    amount=amount,
                    email=data['email'],
                    phone_number=data['phone_number']
                )
                if response.get('status') == "success":
                    return redirect('services:electricity_payment_success')
                else:
                    return JsonResponse({"error": response.get('message', 'Error processing VTPass payment')}, status=400)
    else:
        form = UtilityBillsForm()

    context = {
        'form': form,
        'wallet': wallet,
        'wallet_currencies': [
            {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
        ] if wallet else [],
        'transactions': transactions,
    }

    return render(request, 'services/electricity_payment.html', context)



def dstv_payment(request):
    wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None 
    transactions = Transaction.objects.filter(user=request.user) if request.user.is_authenticated else []

    if request.method == 'POST':
        form = UtilityBillsForm(request.POST)
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
            elif payment_method == 'vtpass':
                vtpass_service_code = "dstv_service_code"  # Replace with actual VTPass service code for DSTV
                response = process_vtpass_payment(
                    service_code=vtpass_service_code,
                    amount=amount,
                    email=data['email'],
                    phone_number=data['phone_number']
                )
                if response.get('status') == "success":
                    return redirect('services:dstv_payment_success')
                else:
                    return JsonResponse({"error": response.get('message', 'Error processing VTPass payment')}, status=400)
    else:
        form = UtilityBillsForm()

    context = {
        'form': form,
        'wallet': wallet,
        'wallet_currencies': [
            {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
        ] if wallet else [],
        'transactions': transactions,
    }

    return render(request, 'services/dstv_payment.html', context)



def gotv_payment(request):
    wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None 
    transactions = Transaction.objects.filter(user=request.user) if request.user.is_authenticated else []

    if request.method == 'POST':
        form = UtilityBillsForm(request.POST)
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
            elif payment_method == 'vtpass':
                vtpass_service_code = "gotv_service_code"  # Replace with actual VTPass service code for GOTV
                response = process_vtpass_payment(
                    service_code=vtpass_service_code,
                    amount=amount,
                    email=data['email'],
                    phone_number=data['phone_number']
                )
                if response.get('status') == "success":
                    return redirect('services:gotv_payment_success')
                else:
                    return JsonResponse({"error": response.get('message', 'Error processing VTPass payment')}, status=400)
    else:
        form = UtilityBillsForm()

    context = {
        'form': form,
        'wallet': wallet,
        'wallet_currencies': [
            {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
        ] if wallet else [],
        'transactions': transactions,
    }

    return render(request, 'services/gotv_payment.html', context)


def startimes_payment(request):
    wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None 
    transactions = Transaction.objects.filter(user=request.user) if request.user.is_authenticated else []

    if request.method == 'POST':
        form = UtilityBillsForm(request.POST)
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
            elif payment_method == 'vtpass':
                vtpass_service_code = "startimes_service_code"  # Replace with actual VTPass service code for Startimes
                response = process_vtpass_payment(
                    service_code=vtpass_service_code,
                    amount=amount,
                    email=data['email'],
                    phone_number=data['phone_number']
                )
                if response.get('status') == "success":
                    return redirect('services:startimes_payment_success')
                else:
                    return JsonResponse({"error": response.get('message', 'Error processing VTPass payment')}, status=400)
    else:
        form = UtilityBillsForm()

    context = {
        'form': form,
        'wallet': wallet,
        'wallet_currencies': [
            {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
        ] if wallet else [],
        'transactions': transactions,
    }

    return render(request, 'services/startimes_payment.html', context)


def search_view(request):
    query = request.GET.get('q', '')  # Get the query parameter from the URL
    results = []  # Default empty result list

    if query:
        # Perform a case-insensitive search on name and description fields
        results = Service.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # Render the results in the search_results.html template
    return render(request, 'services/search_results.html', {'query': query, 'results': results})


class WAECResultCheckerView(View):
    def get(self, request):
        form = WAECResultCheckerForm()
        return render(request, 'services/waec_result_checker.html', {'form': form})

    def post(self, request):
        form = WAECResultCheckerForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            candidate_number = data['candidate_number']
            year_of_exam = data['year_of_exam']
            payment_method = data['payment_method']
            user = request.user
            email = data['email']
            card_details = data.get('card_details', '')

            if payment_method == 'wallet':
                wallet = Wallet.objects.get(user=user)
                if wallet.balance >= 500:  # Example cost for WAEC PIN
                    wallet.balance -= 500
                    wallet.save()
                    result_pin = self._generate_waec_result_pin()
                    self._log_transaction(user, 'WAEC Result Checker', 500)
                    return JsonResponse({"success": True, "pin": result_pin})
                else:
                    return JsonResponse({"error": "Insufficient wallet balance"}, status=400)
            
            elif payment_method == 'debit_card':
                response = self._process_paystack_payment(500, email, card_details)
                if response.get('status') == "success":
                    result_pin = self._generate_waec_result_pin()
                    return JsonResponse({"success": True, "pin": result_pin})
                else:
                    return JsonResponse({"error": response.get('message', 'Error processing payment')}, status=400)

        return render(request, 'services/waec_result_checker.html', {'form': form})

    def _generate_waec_result_pin(self):
        # Generate a random 12-character alphanumeric PIN for result checking
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

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


def dstv_payment_success(request):
    return render(request, 'services/dstv_payment_success.html')

def gotv_payment_success(request):
    return render(request, 'services/gotv_payment_success.html')

def startimes_payment_success(request):
    return render(request, 'services/startimes_payment_success.html')

def electricity_payment_success(request):
    return render(request, 'services/electricity_payment_success.html')

