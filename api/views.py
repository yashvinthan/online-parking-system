from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions
from django.utils import timezone

from accounts.models import User
from bookings.models import ParkingSlot, Booking, PricingTier
from .serializers import UserSerializer, ParkingSlotSerializer, BookingSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class ParkingSlotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParkingSlot.objects.all()
    serializer_class = ParkingSlotSerializer
    permission_classes = [permissions.AllowAny]


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        slot_id = self.request.data.get('slot')
        slot = get_object_or_404(ParkingSlot, pk=slot_id)

        start_raw = self.request.data.get('start_time')
        end_raw = self.request.data.get('end_time')
        start_t = datetime.strptime(start_raw, '%H:%M:%S').time()
        end_t = datetime.strptime(end_raw, '%H:%M:%S').time()

        start_dt = timezone.datetime.combine(timezone.now().date(), start_t)
        end_dt = timezone.datetime.combine(timezone.now().date(), end_t)
        duration_seconds = (end_dt - start_dt).total_seconds()
        duration_hours = Decimal(duration_seconds) / Decimal('3600')

        tier = PricingTier.objects.filter(vehicle_type=slot.vehicle_type).first()
        hourly_rate = tier.hourly_rate if tier else Decimal(str(settings.BOOKING_HOURLY_RATE))
        amount = (duration_hours * hourly_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        minimum = hourly_rate.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if amount < minimum:
            amount = minimum

        serializer.save(
            user=self.request.user,
            slot=slot,
            vehicle_type=slot.vehicle_type,
            amount=amount,
        )
