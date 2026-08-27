import uuid
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

POSITIVE_DECIMAL = Decimal('0.01')

class TimeStampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Vendor(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        PENDING = 'pending', 'Pending'
    name = models.CharField(max_length=160)
    business_type = models.CharField(max_length=80)
    owner_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['status']), models.Index(fields=['name'])]
    def __str__(self): return self.name

class Rider(TimeStampedModel):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        ON_DELIVERY = 'on_delivery', 'On delivery'
        OFFLINE = 'offline', 'Offline'
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32, unique=True)
    email = models.EmailField(unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.AVAILABLE)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5.0, validators=[MinValueValidator(0)])
    def __str__(self): return self.full_name

class Vehicle(TimeStampedModel):
    class Type(models.TextChoices):
        BIKE = 'bike', 'Bike'
        VAN = 'van', 'Van'
        TRUCK = 'truck', 'Truck'
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        IN_SERVICE = 'in_service', 'In service'
        MAINTENANCE = 'maintenance', 'Maintenance'
    registration_number = models.CharField(max_length=32, unique=True)
    vehicle_type = models.CharField(max_length=16, choices=Type.choices)
    capacity_kg = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.AVAILABLE)
    assigned_rider = models.OneToOneField(Rider, null=True, blank=True, on_delete=models.SET_NULL, related_name='vehicle')
    def __str__(self): return self.registration_number

class PricingConfiguration(TimeStampedModel):
    price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(POSITIVE_DECIMAL)],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'NGN {self.price_per_kg} / kg'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            type(self).objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)

    @classmethod
    def current(cls):
        return cls.objects.filter(is_active=True).first()

class Order(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ASSIGNED = 'assigned', 'Assigned'
        PICKED_UP = 'picked_up', 'Picked up'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'
    reference = models.CharField(max_length=40, unique=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='orders')
    rider = models.ForeignKey(Rider, null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
    pickup_address = models.CharField(max_length=255)
    delivery_address = models.CharField(max_length=255)
    recipient_name = models.CharField(max_length=120)
    recipient_phone = models.CharField(max_length=32)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    # Nullable only to preserve orders created before weight-based pricing.
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(POSITIVE_DECIMAL)])
    # Snapshot the rate used so later configuration changes do not rewrite history.
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(POSITIVE_DECIMAL)])
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status']), models.Index(fields=['reference'])]
    def __str__(self): return self.reference

    def save(self, *args, **kwargs):
        weight_changed = self._state.adding
        if not self._state.adding:
            previous_weight = type(self).objects.filter(pk=self.pk).values_list('weight_kg', flat=True).first()
            weight_changed = previous_weight != self.weight_kg
        if self.weight_kg is not None and weight_changed:
            pricing = PricingConfiguration.current()
            if pricing is None:
                raise ValidationError({'weight_kg': 'Delivery pricing is not configured.'})
            self.price_per_kg = pricing.price_per_kg
            self.delivery_fee = self.weight_kg * pricing.price_per_kg
            if update_fields := kwargs.get('update_fields'):
                kwargs['update_fields'] = set(update_fields) | {'price_per_kg', 'delivery_fee'}
        super().save(*args, **kwargs)
