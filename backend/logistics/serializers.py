from django.db import transaction
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
    rider_phone = serializers.CharField(source='rider.phone', read_only=True)
    rider_status = serializers.CharField(source='rider.status', read_only=True)
    class Meta:
        model = Order
        fields = ['id', 'reference', 'vendor', 'vendor_name', 'rider', 'rider_name', 'rider_phone', 'rider_status', 'pickup_address', 'delivery_address', 'recipient_name', 'recipient_phone', 'status', 'delivery_fee', 'created_at', 'updated_at']
        read_only_fields = ['id', 'vendor_name', 'rider_name', 'rider_phone', 'rider_status', 'created_at', 'updated_at']
    def validate(self, attrs):
        vendor = attrs.get('vendor', getattr(self.instance, 'vendor', None))
        rider = attrs.get('rider', getattr(self.instance, 'rider', None))
        status = attrs.get('status', getattr(self.instance, 'status', None))
        if vendor and vendor.status != Vendor.Status.ACTIVE:
            raise serializers.ValidationError({'vendor': 'Orders can only be created for active vendors.'})
        assigning = 'rider' in attrs and rider and rider != getattr(self.instance, 'rider', None)
        if assigning and status in [Order.Status.DELIVERED, Order.Status.CANCELLED]:
            raise serializers.ValidationError({'rider': 'Delivered or cancelled orders cannot be assigned.'})
        if assigning and rider.status != Rider.Status.AVAILABLE:
            raise serializers.ValidationError({'rider': 'Only an available rider can be assigned to an order.'})
        if status in [Order.Status.ASSIGNED, Order.Status.PICKED_UP] and not rider:
            raise serializers.ValidationError({'rider': 'A rider is required once an order is assigned.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        rider = validated_data.get('rider')
        if rider:
            rider = Rider.objects.select_for_update().get(pk=rider.pk)
            if rider.status != Rider.Status.AVAILABLE:
                raise serializers.ValidationError({'rider': 'Only an available rider can be assigned to an order.'})
            validated_data['rider'] = rider
            if validated_data.get('status', Order.Status.PENDING) == Order.Status.PENDING:
                validated_data['status'] = Order.Status.ASSIGNED
            rider.status = Rider.Status.ON_DELIVERY
            rider.save(update_fields=['status', 'updated_at'])
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        order = Order.objects.select_for_update().select_related('rider').get(pk=instance.pk)
        old_rider = order.rider
        new_rider = validated_data.get('rider', old_rider)
        assigning = 'rider' in validated_data and new_rider and new_rider != old_rider
        new_status = validated_data.get('status', order.status)

        if assigning:
            if order.status in [Order.Status.DELIVERED, Order.Status.CANCELLED]:
                raise serializers.ValidationError({'rider': 'Delivered or cancelled orders cannot be assigned.'})
            new_rider = Rider.objects.select_for_update().get(pk=new_rider.pk)
            if new_rider.status != Rider.Status.AVAILABLE:
                raise serializers.ValidationError({'rider': 'Only an available rider can be assigned to an order.'})
            if Rider.objects.filter(pk=new_rider.pk, orders__status__in=[Order.Status.ASSIGNED, Order.Status.PICKED_UP]).exists():
                raise serializers.ValidationError({'rider': 'This rider already has an active order.'})
            validated_data['rider'] = new_rider
            if new_status == Order.Status.PENDING:
                validated_data['status'] = Order.Status.ASSIGNED
                new_status = Order.Status.ASSIGNED
            new_rider.status = Rider.Status.ON_DELIVERY
            new_rider.save(update_fields=['status', 'updated_at'])
            if old_rider:
                locked_old_rider = Rider.objects.select_for_update().get(pk=old_rider.pk)
                locked_old_rider.status = Rider.Status.AVAILABLE
                locked_old_rider.save(update_fields=['status', 'updated_at'])

        if old_rider and new_status in [Order.Status.DELIVERED, Order.Status.CANCELLED]:
            locked_old_rider = Rider.objects.select_for_update().get(pk=old_rider.pk)
            if locked_old_rider.status == Rider.Status.ON_DELIVERY:
                locked_old_rider.status = Rider.Status.AVAILABLE
                locked_old_rider.save(update_fields=['status', 'updated_at'])

        return super().update(order, validated_data)
