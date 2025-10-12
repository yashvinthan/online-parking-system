from django.db import migrations


def seed_pricing_tiers(apps, schema_editor):
    PricingTier = apps.get_model('bookings', 'PricingTier')
    ParkingSlot = apps.get_model('bookings', 'ParkingSlot')

    if PricingTier.objects.exists():
        return

    tiers = [
        ('HATCHBACK', 40),
        ('SEDAN', 50),
        ('SUV', 70),
        ('EV', 60),
    ]
    for vehicle_type, rate in tiers:
        PricingTier.objects.create(vehicle_type=vehicle_type, hourly_rate=rate)

    vehicle_cycle = [t[0] for t in tiers]
    for index, slot in enumerate(ParkingSlot.objects.all().order_by('id')):
        slot.vehicle_type = vehicle_cycle[index % len(vehicle_cycle)]
        slot.save(update_fields=['vehicle_type'])


def unseed_pricing_tiers(apps, schema_editor):
    PricingTier = apps.get_model('bookings', 'PricingTier')
    PricingTier.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0003_pricingtier_booking_vehicle_type_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_pricing_tiers, unseed_pricing_tiers),
    ]
