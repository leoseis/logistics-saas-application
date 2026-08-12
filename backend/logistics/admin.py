from django.contrib import admin
from .models import Order, Rider, Vehicle, Vendor
admin.site.register([Vendor, Rider, Vehicle, Order])
