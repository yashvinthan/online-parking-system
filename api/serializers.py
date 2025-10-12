from rest_framework import serializers
from accounts.models import User
from bookings.models import ParkingSlot, Booking


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone')


class ParkingSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingSlot
        fields = ('id', 'slot_number', 'location', 'vehicle_type', 'status')


class BookingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = (
            'id', 'user', 'slot', 'vehicle_type', 'date', 'start_time', 'end_time',
            'amount', 'payment_status', 'created_at'
        )
        read_only_fields = ('amount', 'payment_status', 'vehicle_type')
