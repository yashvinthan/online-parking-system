from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    PHONE_MAX_LENGTH = 20
    PAYMENT_METHOD_GPAY = 'gpay'
    PAYMENT_METHOD_PAYTM = 'paytm'
    PAYMENT_METHOD_CARD = 'card'
    PAYMENT_CHOICES = [
        (PAYMENT_METHOD_GPAY, 'Google Pay / UPI'),
        (PAYMENT_METHOD_PAYTM, 'Paytm Wallet'),
        (PAYMENT_METHOD_CARD, 'Credit / Debit Card'),
    ]

    phone = models.CharField(max_length=PHONE_MAX_LENGTH, blank=True)
    preferred_payment_method = models.CharField(
        max_length=20,
        blank=True,
        choices=PAYMENT_CHOICES,
    )

    def __str__(self):
        return self.username


# Create your models here.
