from django.contrib import admin
from .models import Order, PricingConfiguration, Rider, Vehicle, Vendor

@admin.register(PricingConfiguration)
class PricingConfigurationAdmin(admin.ModelAdmin):
    list_display = ['price_per_kg', 'is_active', 'updated_at']
    list_editable = ['is_active']

admin.site.register([Vendor, Rider, Vehicle, Order])
