from django.contrib import admin
from .models import (
    Service, PurchaseAirtime, DataTopUp, UtilityBills, ElectricityPayment, 
    DstvSubscription, GoTVSubscription, StarTimesSubscription, SchoolFeesPayment, 
    WaecResultCheck, Flight, Booking, FlightSearch, PaystackTransaction, ServiceType,
    ServicePayment
)

# Register the Service model
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type')
    search_fields = ('name',)

# Admin for ServiceType
@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']



# Register AirtimeRecharge model
@admin.register(PurchaseAirtime)
class PurchaseAirtimeAdmin(admin.ModelAdmin):
    list_display = ('user', 'network_provider', 'amount', 'payment_method', 'date_created')
    search_fields = ('user__username', 'network_provider', 'phone_number')

# Register DataTopUp model
@admin.register(DataTopUp)
class DataTopUpAdmin(admin.ModelAdmin):
    list_display = ('user', 'network_provider', 'amount', 'payment_method', 'date_created')
    search_fields = ('user__username', 'network_provider', 'phone_number')

# Register UtilityBills model
@admin.register(UtilityBills)
class UtilityBillsAdmin(admin.ModelAdmin):
    list_display = ('user', 'service_type', 'amount', 'payment_method', 'date_created')
    search_fields = ('user__username', 'service_type', 'account_number')

# Register ElectricityPayment model
@admin.register(ElectricityPayment)
class ElectricityPaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'meter_type', 'meter_number', 'amount', 'created_at')
    search_fields = ('user__username', 'meter_number')

# Register DSTV Subscription model
@admin.register(DstvSubscription)
class DstvSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'customer_type', 'package', 'amount', 'created_at')
    search_fields = ('user__username', 'smart_card_number', 'package')

# Register GoTV Subscription model
@admin.register(GoTVSubscription)
class GoTVSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'customer_type', 'package', 'amount', 'created_at')
    search_fields = ('user__username', 'smart_card_number', 'package')

# Register StarTimes Subscription model
@admin.register(StarTimesSubscription)
class StarTimesSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'customer_type', 'package', 'amount', 'created_at')
    search_fields = ('user__username', 'smart_card_number', 'package')

# Register SchoolFeesPayment model
@admin.register(SchoolFeesPayment)
class SchoolFeesPaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_name', 'amount', 'payment_method', 'date_created')
    search_fields = ('user__username', 'student_name')

# Register WAEC Result Check model
@admin.register(WaecResultCheck)
class WaecResultCheckAdmin(admin.ModelAdmin):
    list_display = ('user', 'exam_number', 'exam_year', 'amount', 'created_at')
    search_fields = ('user__username', 'exam_number')

# Register Flight model
@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ('flight_number', 'departure', 'destination', 'arrival_time', 'price', 'available_seats')  # Removed departure_time as it's not a valid field
    search_fields = ('flight_number', 'departure', 'destination')

# Register Booking model
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'flight', 'booking_reference', 'passengers', 'status')  # Fixed seat_count to passengers, as 'seat_count' does not exist
    search_fields = ('user__username', 'booking_reference', 'flight__flight_number')  # Added flight number search

admin.site.register(Booking, BookingAdmin)

# Register FlightSearch model
@admin.register(FlightSearch)
class FlightSearchAdmin(admin.ModelAdmin):
    list_display = ('origin', 'destination', 'date')
    search_fields = ('origin', 'destination')

# Register PaystackTransaction model
@admin.register(PaystackTransaction)
class PaystackTransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'status', 'amount', 'created_at')
    search_fields = ('reference',)


# Register ServicePayment model
@admin.register(ServicePayment)
class ServicePaymentAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'customer_name', 'amount', 'payment_date', 'status')
    search_fields = ('service_name', 'customer_name', 'phone_number')
