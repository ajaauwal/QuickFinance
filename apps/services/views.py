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
    DataTopUpForm,
    SchoolFeesPaymentForm,
    UtilityBillsForm,
    WaecResultCheckForm,
    
)

# Models
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

import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

# Use environment variables for VTpass API details
VTPASS_BASE_URL = settings.VTPASS_BASE_URL
VTPASS_PUBLIC_KEY = settings.VTPASS_PUBLIC_KEY
VTPASS_SECRET_KEY = settings.VTPASS_SECRET_KEY

import requests
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings

@csrf_exempt
def purchase_airtime(request):
    if request.method == "POST":
        network_provider = request.POST.get('network_provider')
        amount = request.POST.get('amount')
        phone_number = request.POST.get('phone_number')

        # Create a unique request ID
        request_id = str(uuid.uuid4())

        payload = {
            "request_id": request_id,
            "serviceID": network_provider,
            "billersCode": phone_number,
            "variation_code": "",
            "amount": amount,
            "phone": phone_number
        }

        headers = {
            "Content-Type": "application/json"
        }

        # VTpass Authentication
        username = settings.VTPASS_USERNAME  # your vtpass email
        password = settings.VTPASS_PASSWORD  # your vtpass api key

        response = requests.post(
            "https://vtpass.com/api/pay",
            json=payload,
            headers=headers,
            auth=(username, password)
        )

        if response.status_code == 200:
            vtpass_response = response.json()
            if vtpass_response.get('code') == "000":  # successful
                return JsonResponse({"status": "success", "message": "Airtime purchased successfully"})
            else:
                return JsonResponse({"status": "failed", "message": vtpass_response.get('response_description', 'Error processing request')})
        else:
            return JsonResponse({"status": "failed", "message": "VTpass API error"})

    return JsonResponse({"status": "failed", "message": "Invalid request method"})



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



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string
from .models import Flight, Booking, FlightSearch
from .paystack import PaystackAPI  # Ensure your Paystack integration exists
from django.http import JsonResponse, Http404
import requests
from amadeus import Client, ResponseError
from django.conf import settings

# Amadeus API client initialization
amadeus = Client(
    client_id=settings.AMADEUS_API_KEY,
    client_secret=settings.AMADEUS_API_SECRET
)


@login_required
def flight_booking(request):
    wallet = get_object_or_404(Wallet, user=request.user)
    transactions = Transaction.objects.filter(user=request.user)

    categories = [
        {
            'name': 'Flight Class',
            'field_name': 'flight_class',
            'options': ['Economy', 'Business', 'First Class']
        },
        {
            'name': 'Flight Type',
            'field_name': 'flight_type',
            'options': ['One-Way', 'Round-Trip']
        },
    ]

    if request.method == 'POST':
        flight_id = request.POST.get('flight_id')
        seat_count = int(request.POST.get('seat_count'))
        payment_method = request.POST.get('payment_method')

        flight = get_object_or_404(Flight, id=flight_id)

        if seat_count > flight.available_seats:
            messages.error(request, "Not enough seats available.")
            return redirect('services:airport_search')

        total_price = seat_count * flight.price

        if payment_method == 'wallet':
            if wallet.balance >= total_price:
                wallet.balance -= total_price
                wallet.save()

                flight.available_seats -= seat_count
                flight.save()

                booking = Booking.objects.create(
                    user=request.user,
                    flight=flight,
                    seat_count=seat_count,
                    total_price=total_price,
                    booking_reference=get_random_string(length=12),
                    status='Paid'
                )

                Transaction.objects.create(
                    user=request.user,
                    amount=total_price,
                    transaction_type='debit',
                    purpose='Flight Booking',
                )

                messages.success(request, "Booking confirmed via wallet.")
                return redirect('services:booking_confirmation', booking_id=booking.id)
            else:
                messages.error(request, "Insufficient wallet balance.")
                return redirect('services:airport_search')

        elif payment_method == 'paystack':
            booking = Booking.objects.create(
                user=request.user,
                flight=flight,
                seat_count=seat_count,
                total_price=total_price,
                booking_reference=get_random_string(length=12),
                status='Pending'
            )
            redirect_url = PaystackAPI(request.user.email, total_price, booking.id)
            return redirect(redirect_url)

    context = {
        'wallet': wallet,
        'wallet_currencies': [{"currency": "NGN", "symbol": "₦", "balance": wallet.balance}],
        'transactions': transactions,
        'categories': categories,
    }
    return render(request, 'services/flight_booking.html', context)



def flight_search(request):
    origin = request.GET.get('origin')
    destination = request.GET.get('destination')
    date = request.GET.get('date')
    adults = request.GET.get('adults', 1)

    access_token = get_amadeus_access_token()
    if not access_token:
        return JsonResponse({'error': 'Failed to authenticate with Amadeus API'}, status=400)

    url = f'https://test.api.amadeus.com/v2/shopping/flight-offers'
    params = {
        'originLocationCode': origin,
        'destinationLocationCode': destination,
        'departureDate': date,
        'adults': adults,
        'max': 5
    }
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        data = response.json()['data']
        flights = [{
            'flight': f"{flight['itineraries'][0]['segments'][0]['departure']['iataCode']} ➡ {flight['itineraries'][0]['segments'][-1]['arrival']['iataCode']}",
            'price': flight['price']['grandTotal'],
            'date': date,
            'adults': adults
        } for flight in data]
        return JsonResponse(flights, safe=False)
    else:
        return JsonResponse({'error': 'Failed to fetch flight data from Amadeus API'}, status=400)


def search_hotels(request):
    city = request.GET.get('city')

    access_token = get_amadeus_access_token()
    if not access_token:
        return JsonResponse({'error': 'Failed to authenticate with Amadeus API'}, status=400)

    url = f'https://test.api.amadeus.com/v2/shopping/hotel-offers'
    params = {
        'cityCode': city,
        'adults': 1,
        'radius': 5,  # Limit search radius to 5km
        'radiusUnit': 'KM',
    }
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        data = response.json()['data']
        hotels = [{
            'hotel': hotel['hotel']['name'],
            'city': city,
            'price': hotel['offers'][0]['price']['total']
        } for hotel in data]
        return JsonResponse(hotels, safe=False)
    else:
        return JsonResponse({'error': 'Failed to fetch hotel data from Amadeus API'}, status=400)


@login_required
def manage_booking(request):
    booking = Booking.objects.filter(user=request.user).first()
    if not booking:
        messages.error(request, "No booking found.")
        return redirect('services:airport_search')

    context = {
        'booking': booking
    }
    return render(request, 'services/manage_booking.html', context)


@login_required
def booking_confirmation(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
    except Booking.DoesNotExist:
        raise Http404("Booking not found")

    context = {
        'booking': booking
    }
    return render(request, 'services/booking_confirmation.html', context)


@login_required
def update_booking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
    except Booking.DoesNotExist:
        raise Http404("Booking not found")

    if request.method == 'POST':
        new_seat_count = int(request.POST.get('seat_count'))

        if new_seat_count > booking.flight.available_seats:
            messages.error(request, "Not enough available seats.")
            return redirect('services:update_booking', booking_id=booking.id)

        booking.seat_count = new_seat_count
        booking.total_price = new_seat_count * booking.flight.price
        booking.save()

        booking.flight.available_seats -= new_seat_count
        booking.flight.save()

        messages.success(request, "Booking updated successfully!")
        return redirect('services:manage_booking')

    context = {
        'booking': booking
    }
    return render(request, 'services/update_booking.html', context)


@login_required
def cancel_booking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
    except Booking.DoesNotExist:
        raise Http404("Booking not found")

    if booking.status == 'Cancelled':
        messages.error(request, "Booking already cancelled.")
        return redirect('services:manage_booking')

    booking.status = 'Cancelled'
    booking.flight.available_seats += booking.seat_count
    booking.flight.save()
    booking.save()

    messages.success(request, "Booking cancelled successfully!")
    return redirect('services:manage_booking')

def get_amadeus_access_token():
    url = 'https://test.api.amadeus.com/v1/security/oauth2/token'
    data = {
        'grant_type': 'client_credentials',
        'client_id': settings.AMADEUS_CLIENT_ID,
        'client_secret': settings.AMADEUS_CLIENT_SECRET,
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        return None


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def paystack_callback(request, booking_id):
    ref = request.GET.get('reference')

    # Verify payment with Paystack
    headers = {
        "Authorization": "Bearer YOUR_PAYSTACK_SECRET_KEY"
    }
    url = f"https://api.paystack.co/transaction/verify/{ref}"
    response = requests.get(url, headers=headers).json()

    if response['data']['status'] == 'success':
        booking = Booking.objects.get(id=booking_id)
        booking.status = 'Paid'
        booking.save()

        # Update seat count
        booking.flight.available_seats -= booking.seat_count
        booking.flight.save()

        # Record transaction
        Transaction.objects.create(
            user=booking.user,
            amount=booking.total_price,
            transaction_type='debit',
            purpose='Flight Booking (Paystack)',
        )

        messages.success(request, "Payment successful and booking confirmed!")
        return redirect('services:booking_confirmation', booking_id=booking.id)
    else:
        messages.error(request, "Payment failed.")
        return redirect('services:airport_search')



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


from .models import Service

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
        # Fetch the wallet and transactions only if the user is authenticated
        wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None 
        transactions = Transaction.objects.filter(user=request.user) if request.user.is_authenticated else []

        form = WaecResultCheckForm()
        
        # Context data
        context = {
            'form': form,
            'wallet': wallet,
            'wallet_currencies': [
                {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
            ] if wallet else [],
            'transactions': transactions,
        }
        
        return render(request, 'services/waec_result_checker.html', context)

    def post(self, request):
        # Fetch the wallet and transactions only if the user is authenticated
        wallet = get_object_or_404(Wallet, user=request.user) if request.user.is_authenticated else None 
        transactions = Transaction.objects.filter(user=request.user) if request.user.is_authenticated else []
        
        form = WaecResultCheckForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            candidate_number = data['candidate_number']
            year_of_exam = data['year_of_exam']
            payment_method = data['payment_method']
            user = request.user
            email = data['email']
            card_details = data.get('card_details', '')

            if payment_method == 'wallet':
                # Handle payment via wallet
                if wallet.balance >= 500:  # Example cost for WAEC PIN
                    wallet.balance -= 500
                    wallet.save()
                    result_pin = self._generate_waec_result_pin()
                    self._log_transaction(user, 'WAEC Result Checker', 500)
                    return JsonResponse({"success": True, "pin": result_pin})
                else:
                    return JsonResponse({"error": "Insufficient wallet balance"}, status=400)
            
            elif payment_method == 'debit_card':
                # Handle payment via debit card (Paystack)
                response = self._process_paystack_payment(500, email, card_details)
                if response.get('status') == "success":
                    result_pin = self._generate_waec_result_pin()
                    return JsonResponse({"success": True, "pin": result_pin})
                else:
                    return JsonResponse({"error": response.get('message', 'Error processing payment')}, status=400)

        # In case the form is invalid, return the same page with the form errors
        context = {
            'form': form,
            'wallet': wallet,
            'wallet_currencies': [
                {"currency": "NGN", "symbol": "₦", "balance": wallet.balance if wallet else 0}
            ] if wallet else [],
            'transactions': transactions,
        }
        return render(request, 'services/waec_result_checker.html', context)

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

