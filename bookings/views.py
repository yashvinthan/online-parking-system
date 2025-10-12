from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count
import stripe
import io
import qrcode
from django.core.files.images import ImageFile

from accounts.models import User
from .models import ParkingSlot, Booking, PricingTier
from .forms import BookingForm

MONEY_QUANT = Decimal('0.01')


def _current_availability_map():
    now = timezone.localtime()
    current_time = now.time()
    today = now.date()
    availability = {}
    for slot in ParkingSlot.objects.all().order_by('slot_number'):
        active = Booking.objects.filter(
            slot=slot,
            date=today,
            start_time__lte=current_time,
            end_time__gt=current_time,
            payment_status=Booking.PAYMENT_PAID,
        ).exists()
        availability[slot.id] = not active
    return availability


def _get_hourly_rate(vehicle_type: str) -> Decimal:
    tier = PricingTier.objects.filter(vehicle_type=vehicle_type).first()
    if tier:
        return tier.hourly_rate
    return Decimal(str(settings.BOOKING_HOURLY_RATE))


def _slot_tile_context():
    slots = list(ParkingSlot.objects.all().order_by('slot_number'))
    availability = _current_availability_map()
    tier_map = {tier.vehicle_type: tier for tier in PricingTier.objects.all()}
    tiles = []
    for slot in slots:
        vehicle_type = slot.vehicle_type
        rate = tier_map.get(vehicle_type).hourly_rate if tier_map.get(vehicle_type) else _get_hourly_rate(vehicle_type)
        tiles.append({
            'slot': slot,
            'id': str(slot.id),
            'code': slot.slot_number,
            'location': slot.location,
            'available': availability.get(slot.id, True) and slot.status != ParkingSlot.STATUS_BOOKED,
            'vehicle': vehicle_type,
            'vehicle_label': slot.get_vehicle_type_display(),
            'rate': rate,
            })
    locations = sorted({slot.location for slot in slots})
    vehicle_choices = [
        {
            'value': value,
            'label': label,
            'rate': tier_map.get(value).hourly_rate if tier_map.get(value) else _get_hourly_rate(value),
        }
        for value, label in ParkingSlot.VEHICLE_CHOICES
    ]
    return slots, tiles, locations, vehicle_choices


def _calculate_amount(start_time, end_time, hourly_rate: Decimal) -> Decimal:
    start_dt = timezone.datetime.combine(timezone.now().date(), start_time)
    end_dt = timezone.datetime.combine(timezone.now().date(), end_time)
    duration_seconds = (end_dt - start_dt).total_seconds()
    duration_hours = Decimal(duration_seconds) / Decimal('3600')
    hourly_rate = Decimal(hourly_rate)
    amount = (duration_hours * hourly_rate).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
    minimum = hourly_rate.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
    return amount if amount >= minimum else minimum


@login_required
def dashboard(request):
    _, tiles, _, _ = _slot_tile_context()
    total_slots = len(tiles)
    available_count = sum(1 for tile in tiles if tile['available'])
    booked_count = total_slots - available_count
    today = timezone.localdate()
    user_bookings = Booking.objects.filter(user=request.user)
    total_user_bookings = user_bookings.count()
    upcoming = user_bookings.filter(date__gte=today).order_by('date', 'start_time')[:5]
    recent = user_bookings.order_by('-created_at')[:5]
    occupancy = round((booked_count / total_slots) * 100, 1) if total_slots else 0

    context = {
        'slot_tiles': tiles,
        'available_count': available_count,
        'booked_count': booked_count,
        'total_slots': total_slots,
        'occupancy': occupancy,
        'upcoming_bookings': upcoming,
        'recent_bookings': recent,
        'total_user_bookings': total_user_bookings,
    }
    return render(request, 'bookings/dashboard.html', context)


@login_required
def book_slot(request):
    slots, tiles, locations, vehicle_choices = _slot_tile_context()
    form = BookingForm(request.POST or None)
    form.fields['slot'].queryset = ParkingSlot.objects.order_by('slot_number')
    selected_slot_id = None
    preferred_method = request.user.preferred_payment_method or User.PAYMENT_METHOD_GPAY

    if request.method == 'POST':
        posted_method = request.POST.get('payment_method') or preferred_method
        payment_choices = dict(User.PAYMENT_CHOICES)
        if posted_method in payment_choices and posted_method != request.user.preferred_payment_method:
            request.user.preferred_payment_method = posted_method
            request.user.save(update_fields=['preferred_payment_method'])
        preferred_method = posted_method

        if form.is_valid():
            slot = form.cleaned_data['slot']
            date = form.cleaned_data['date']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']

            overlap_exists = Booking.objects.filter(
                slot=slot, date=date, payment_status=Booking.PAYMENT_PAID
            ).filter(start_time__lt=end_time, end_time__gt=start_time).exists()
            if overlap_exists:
                messages.error(request, 'Selected slot/time is not available.')
            else:
                hourly_rate = _get_hourly_rate(slot.vehicle_type)
                amount = _calculate_amount(start_time, end_time, hourly_rate)
                booking = Booking.objects.create(
                    user=request.user,
                    slot=slot,
                    vehicle_type=slot.vehicle_type,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    amount=amount,
                    payment_status=Booking.PAYMENT_PENDING,
                )
                return redirect('bookings:checkout', booking_id=booking.id)
        selected_slot_id = request.POST.get('slot')
    else:
        preferred_method = request.user.preferred_payment_method or User.PAYMENT_METHOD_GPAY

    default_rate = vehicle_choices[0]['rate'] if vehicle_choices else _get_hourly_rate(ParkingSlot.VEHICLE_SEDAN)

    if selected_slot_id:
        selected_slot_id = str(selected_slot_id)

    selected_vehicle = 'all'
    if selected_slot_id:
        selected_slot_id = str(selected_slot_id)
        selected_slot = next((t['slot'] for t in tiles if str(t['id']) == selected_slot_id), None)
        if selected_slot:
            selected_vehicle = selected_slot.vehicle_type

    context = {
        'form': form,
        'slot_tiles': tiles,
        'locations': locations,
        'vehicle_choices': vehicle_choices,
        'selected_slot_id': selected_slot_id,
        'default_rate': default_rate,
        'preferred_payment_method': preferred_method,
        'selected_vehicle': selected_vehicle,
    }
    return render(request, 'bookings/booking_form.html', context)


@login_required
def create_checkout_session(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    if not settings.STRIPE_PUBLIC_KEY or not settings.STRIPE_SECRET_KEY:
        # Test-mode fallback so bookings still succeed without Stripe keys
        if booking.payment_status != Booking.PAYMENT_PAID:
            booking.payment_status = Booking.PAYMENT_PAID
            booking.save(update_fields=['payment_status'])
            _generate_qr_for_booking(booking)
        messages.info(request, 'Stripe keys not configured. Booking confirmed in local test mode.')
        return render(request, 'bookings/confirmation.html', {'booking': booking, 'test_mode': True})

    amount_in_minor = int(Decimal(booking.amount) * 100)
    currency = settings.STRIPE_CURRENCY

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': currency,
                'product_data': {
                    'name': f'Parking Slot {booking.slot.slot_number} ({booking.date} {booking.start_time}-{booking.end_time})',
                },
                'unit_amount': amount_in_minor,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(f"/bookings/payment/success/?session_id={{CHECKOUT_SESSION_ID}}"),
        cancel_url=request.build_absolute_uri("/bookings/payment/cancel/"),
    )
    booking.stripe_session_id = session.id
    booking.save(update_fields=['stripe_session_id'])

    return render(request, 'bookings/checkout.html', {
        'session_id': session.id,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    })


def _generate_qr_for_booking(booking: Booking):
    data = f"BOOKING:{booking.id}|USER:{booking.user.username}|SLOT:{booking.slot.slot_number}|DATE:{booking.date}|TIME:{booking.start_time}-{booking.end_time}|AMOUNT:{booking.amount}"
    img = qrcode.make(data)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    booking.qr_code_image.save(f"booking_{booking.id}.png", ImageFile(buffer), save=True)


@login_required
def payment_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, 'Missing payment session.')
        return redirect('bookings:dashboard')

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception:
        messages.error(request, 'Unable to verify payment.')
        return redirect('bookings:dashboard')

    booking = get_object_or_404(Booking, stripe_session_id=session_id, user=request.user)
    if session.payment_status == 'paid':
        if booking.payment_status != Booking.PAYMENT_PAID:
            booking.payment_status = Booking.PAYMENT_PAID
            booking.save(update_fields=['payment_status'])
            _generate_qr_for_booking(booking)
        return render(request, 'bookings/confirmation.html', {'booking': booking})
    else:
        booking.payment_status = Booking.PAYMENT_FAILED
        booking.save(update_fields=['payment_status'])
        messages.error(request, 'Payment was not successful.')
        return redirect('bookings:book_slot')


@login_required
def payment_cancel(request):
    messages.info(request, 'Payment cancelled.')
    return redirect('bookings:book_slot')


@staff_member_required
def daily_revenue_report(request):
    today = timezone.localdate()
    total = Booking.objects.filter(date=today, payment_status=Booking.PAYMENT_PAID).aggregate(total=Sum('amount'))['total'] or 0
    count = Booking.objects.filter(date=today, payment_status=Booking.PAYMENT_PAID).count()
    return render(request, 'bookings/daily_report.html', {'date': today, 'total': total, 'count': count})


@staff_member_required
def admin_dashboard(request):
    today = timezone.localdate()
    seven_days_ago = today - timedelta(days=6)
    revenue_series = (
        Booking.objects.filter(payment_status=Booking.PAYMENT_PAID, date__range=[seven_days_ago, today])
        .values('date').annotate(total=Sum('amount'), count=Count('id')).order_by('date')
    )
    revenue_labels = [entry['date'].strftime('%d %b') for entry in revenue_series]
    revenue_data = [float(entry['total']) for entry in revenue_series]

    vehicle_mix = (
        Booking.objects.filter(payment_status=Booking.PAYMENT_PAID)
        .values('vehicle_type').annotate(total=Sum('amount'))
    )
    vehicle_labels = [dict(ParkingSlot.VEHICLE_CHOICES).get(entry['vehicle_type'], entry['vehicle_type']) for entry in vehicle_mix]
    vehicle_data = [float(entry['total']) if entry['total'] else 0 for entry in vehicle_mix]

    slot_count = ParkingSlot.objects.count()
    active_today = Booking.objects.filter(payment_status=Booking.PAYMENT_PAID, date=today).count()
    revenue_total = Booking.objects.filter(payment_status=Booking.PAYMENT_PAID).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    context = {
        'slot_count': slot_count,
        'active_today': active_today,
        'revenue_total': revenue_total,
        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
        'vehicle_labels': vehicle_labels,
        'vehicle_data': vehicle_data,
    }
    return render(request, 'bookings/admin_dashboard.html', context)














