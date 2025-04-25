from django.contrib import admin
from .models import AirtimeRecharge, UtilityBills, FlightBooking, DataTopUp
from django.contrib import admin
from .models import ServicePayment

@admin.register(ServicePayment)
class ServicePaymentAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'customer_name', 'amount', 'payment_date')
    search_fields = ('service_name', 'customer_name', 'phone_number')



admin.site.register(AirtimeRecharge)
admin.site.register(UtilityBills)
admin.site.register(FlightBooking)
admin.site.register(DataTopUp)