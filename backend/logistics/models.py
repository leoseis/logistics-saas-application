import uuid
from django.core.validators import MinValueValidator
from django.db import models

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
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status']), models.Index(fields=['reference'])]
    def __str__(self): return self.reference
