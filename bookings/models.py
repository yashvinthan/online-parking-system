from django.db import models
from django.conf import settings
from django.utils import timezone


class ParkingSlot(models.Model):
    STATUS_AVAILABLE = 'AVAILABLE'
    STATUS_BOOKED = 'BOOKED'
    STATUS_CHOICES = [
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_BOOKED, 'Booked'),
    ]

    VEHICLE_HATCHBACK = 'HATCHBACK'
    VEHICLE_SEDAN = 'SEDAN'
    VEHICLE_SUV = 'SUV'
    VEHICLE_EV = 'EV'
    VEHICLE_CHOICES = [
        (VEHICLE_HATCHBACK, 'Hatchback'),
        (VEHICLE_SEDAN, 'Sedan'),
        (VEHICLE_SUV, 'SUV'),
        (VEHICLE_EV, 'Electric Vehicle'),
    ]

    slot_number = models.CharField(max_length=10, unique=True)
    location = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=12, choices=VEHICLE_CHOICES, default=VEHICLE_SEDAN)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)

    def __str__(self):
        return f"Slot {self.slot_number} - {self.location}"


class PricingTier(models.Model):
    vehicle_type = models.CharField(max_length=12, choices=ParkingSlot.VEHICLE_CHOICES, unique=True)
    hourly_rate = models.DecimalField(max_digits=7, decimal_places=2)
    description = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ['vehicle_type']

    def __str__(self):
        return f"{self.get_vehicle_type_display()} - ₹{self.hourly_rate} per hour"


class Booking(models.Model):
    PAYMENT_PENDING = 'PENDING'
    PAYMENT_PAID = 'PAID'
    PAYMENT_FAILED = 'FAILED'
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, 'Pending'),
        (PAYMENT_PAID, 'Paid'),
        (PAYMENT_FAILED, 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE, related_name='bookings')
    vehicle_type = models.CharField(max_length=12, choices=ParkingSlot.VEHICLE_CHOICES, default=ParkingSlot.VEHICLE_SEDAN)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_PENDING)
    stripe_session_id = models.CharField(max_length=200, blank=True)
    qr_code_image = models.ImageField(upload_to='qr_codes/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking #{self.id} - {self.user} - {self.slot}"

    def overlaps(self, other_start, other_end):
        return max(self.start_time, other_start) < min(self.end_time, other_end)


# Create your models here.
