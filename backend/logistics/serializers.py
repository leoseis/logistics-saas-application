from rest_framework import serializers
from .models import Order, Rider, Vehicle, Vendor

class VendorSerializer(serializers.ModelSerializer):
    order_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'business_type', 'owner_name', 'phone', 'email', 'address', 'status', 'order_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'order_count', 'created_at', 'updated_at']

class RiderSerializer(serializers.ModelSerializer):
    active_order_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Rider
        fields = ['id', 'full_name', 'phone', 'email', 'status', 'rating', 'active_order_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'active_order_count', 'created_at', 'updated_at']

class VehicleSerializer(serializers.ModelSerializer):
    assigned_rider_name = serializers.CharField(source='assigned_rider.full_name', read_only=True)
    class Meta:
        model = Vehicle
        fields = ['id', 'registration_number', 'vehicle_type', 'capacity_kg', 'status', 'assigned_rider', 'assigned_rider_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'assigned_rider_name', 'created_at', 'updated_at']
    def validate(self, attrs):
        rider = attrs.get('assigned_rider', getattr(self.instance, 'assigned_rider', None))
        status = attrs.get('status', getattr(self.instance, 'status', None))
        if rider and status == Vehicle.Status.MAINTENANCE:
            raise serializers.ValidationError('A vehicle in maintenance cannot be assigned to a rider.')
        return attrs

class OrderSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    rider_name = serializers.CharField(source='rider.full_name', read_only=True)
    class Meta:
        model = Order
        fields = ['id', 'reference', 'vendor', 'vendor_name', 'rider', 'rider_name', 'pickup_address', 'delivery_address', 'recipient_name', 'recipient_phone', 'status', 'delivery_fee', 'created_at', 'updated_at']
        read_only_fields = ['id', 'vendor_name', 'rider_name', 'created_at', 'updated_at']
    def validate(self, attrs):
        vendor = attrs.get('vendor', getattr(self.instance, 'vendor', None))
        rider = attrs.get('rider', getattr(self.instance, 'rider', None))
        status = attrs.get('status', getattr(self.instance, 'status', None))
        if vendor and vendor.status != Vendor.Status.ACTIVE:
            raise serializers.ValidationError({'vendor': 'Orders can only be created for active vendors.'})
        if rider and rider.status == Rider.Status.OFFLINE:
            raise serializers.ValidationError({'rider': 'An offline rider cannot be assigned to an order.'})
        if status in [Order.Status.ASSIGNED, Order.Status.PICKED_UP] and not rider:
            raise serializers.ValidationError({'rider': 'A rider is required once an order is assigned.'})
        return attrs
