from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    PHONE_MAX_LENGTH = 20
    PAYMENT_METHOD_GPAY = 'gpay'
    PAYMENT_CHOICES = [
        (PAYMENT_METHOD_GPAY, 'Google Pay / UPI'),
    ]

    phone = models.CharField(max_length=PHONE_MAX_LENGTH, blank=True)
    preferred_payment_method = models.CharField(
        max_length=20,
        blank=True,
        choices=PAYMENT_CHOICES,
        default=PAYMENT_METHOD_GPAY,
    )

    def __str__(self):
        return self.username


# Create your models here.
