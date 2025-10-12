from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ParkingSlotViewSet, BookingViewSet


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'slots', ParkingSlotViewSet, basename='slot')
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
]

