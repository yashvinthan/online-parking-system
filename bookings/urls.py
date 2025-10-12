from django.urls import path
from . import views


app_name = 'bookings'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('book/', views.book_slot, name='book_slot'),
    path('checkout/<int:booking_id>/', views.create_checkout_session, name='checkout'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('admin/reports/daily/', views.daily_revenue_report, name='daily_report'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
