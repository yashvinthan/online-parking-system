from django.contrib import admin
from .models import ParkingSlot, Booking, PricingTier


@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    list_display = ('slot_number', 'location', 'vehicle_type', 'status')
    list_filter = ('status', 'vehicle_type')
    search_fields = ('slot_number', 'location')


@admin.register(PricingTier)
class PricingTierAdmin(admin.ModelAdmin):
    list_display = ('vehicle_type', 'hourly_rate', 'description')
    list_editable = ('hourly_rate',)
    ordering = ('vehicle_type',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'slot', 'vehicle_type', 'date', 'start_time', 'end_time', 'amount', 'payment_status')
    list_filter = ('payment_status', 'date', 'vehicle_type')
    search_fields = ('user__username', 'slot__slot_number')

# Register your models here.
