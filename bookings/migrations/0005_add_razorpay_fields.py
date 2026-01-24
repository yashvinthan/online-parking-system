from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0004_seed_pricing_tiers'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='payment_method',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='booking',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='booking',
            name='razorpay_payment_id',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
