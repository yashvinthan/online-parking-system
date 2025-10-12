from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Contact', {'fields': ('phone', 'preferred_payment_method')}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (None, {'fields': ('phone', 'preferred_payment_method')}),
    )
    list_display = ('username', 'email', 'phone', 'preferred_payment_method', 'is_staff', 'is_active')

# Register your models here.
