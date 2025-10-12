from django.db import migrations


def create_slots(apps, schema_editor):
    ParkingSlot = apps.get_model('bookings', 'ParkingSlot')
    if ParkingSlot.objects.count() == 0:
        objs = []
        for i in range(1, 11):
            objs.append(ParkingSlot(slot_number=str(i), location=f"Ground Floor - {i}"))
        ParkingSlot.objects.bulk_create(objs)


def reverse_slots(apps, schema_editor):
    ParkingSlot = apps.get_model('bookings', 'ParkingSlot')
    ParkingSlot.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_slots, reverse_slots),
    ]

