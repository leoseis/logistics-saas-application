from django.db import transaction
from datetime import timedelta
from decimal import Decimal
import secrets
from django.db.models import Avg, Count, DecimalField, Q, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import Order, PricingConfiguration, Rider, Vehicle, Vendor
from .serializers import OrderDetailSerializer, OrderSerializer, PricingConfigurationSerializer, RiderSerializer, VehicleSerializer, VendorSerializer

def paginated_response(request, queryset, serializer_class):
    paginator = PageNumberPagination()
    paginator.page_size = min(int(request.query_params.get('page_size', 20)), 100)
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response(serializer_class(page, many=True, context={'request': request}).data)

def resource_detail(request, instance, serializer_class):
    if request.method == 'GET': return Response(serializer_class(instance, context={'request': request}).data)
    if request.method == 'DELETE': instance.delete(); return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = serializer_class(instance, data=request.data, partial=request.method == 'PATCH', context={'request': request})
    serializer.is_valid(raise_exception=True); serializer.save()
    return Response(serializer.data)

@api_view(['GET', 'POST'])
def vendor_list(request):
    if request.method == 'POST':
        serializer = VendorSerializer(data=request.data); serializer.is_valid(raise_exception=True); serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    query = request.query_params.get('q', '')
    vendors = Vendor.objects.annotate(order_count=Count('orders')).filter(Q(name__icontains=query) | Q(owner_name__icontains=query) | Q(email__icontains=query)).order_by('name')
    if value := request.query_params.get('status'): vendors = vendors.filter(status=value)
    return paginated_response(request, vendors, VendorSerializer)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def vendor_detail(request, vendor_id): return resource_detail(request, get_object_or_404(Vendor.objects.annotate(order_count=Count('orders')), id=vendor_id), VendorSerializer)

@api_view(['GET', 'POST'])
def rider_list(request):
    if request.method == 'POST':
        serializer = RiderSerializer(data=request.data); serializer.is_valid(raise_exception=True); serializer.save(); return Response(serializer.data, status=status.HTTP_201_CREATED)
    query = request.query_params.get('q', '')
    riders = Rider.objects.annotate(active_order_count=Count('orders', filter=Q(orders__status__in=['assigned', 'picked_up']))).filter(Q(full_name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query)).order_by('full_name')
    if value := request.query_params.get('status'): riders = riders.filter(status=value)
    return paginated_response(request, riders, RiderSerializer)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def rider_detail(request, rider_id): return resource_detail(request, get_object_or_404(Rider.objects.annotate(active_order_count=Count('orders', filter=Q(orders__status__in=['assigned', 'picked_up']))), id=rider_id), RiderSerializer)

@api_view(['GET', 'POST'])
def vehicle_list(request):
    if request.method == 'POST':
        serializer = VehicleSerializer(data=request.data); serializer.is_valid(raise_exception=True); serializer.save(); return Response(serializer.data, status=status.HTTP_201_CREATED)
    vehicles = Vehicle.objects.select_related('assigned_rider').order_by('registration_number')
    if value := request.query_params.get('status'): vehicles = vehicles.filter(status=value)
    return paginated_response(request, vehicles, VehicleSerializer)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def vehicle_detail(request, vehicle_id): return resource_detail(request, get_object_or_404(Vehicle.objects.select_related('assigned_rider'), id=vehicle_id), VehicleSerializer)

@api_view(['GET', 'POST'])
def order_list(request):
    if request.method == 'POST':
        serializer = OrderSerializer(data=request.data, context={'request': request}); serializer.is_valid(raise_exception=True); serializer.save(); return Response(serializer.data, status=status.HTTP_201_CREATED)
    orders = Order.objects.select_related('vendor', 'rider')
    if value := request.query_params.get('q'):
        orders = orders.filter(Q(reference__icontains=value) | Q(vendor__name__icontains=value) | Q(recipient_name__icontains=value) | Q(recipient_phone__icontains=value) | Q(pickup_address__icontains=value) | Q(delivery_address__icontains=value))
    if value := request.query_params.get('status'): orders = orders.filter(status=value)
    if value := request.query_params.get('vendor'): orders = orders.filter(vendor_id=value)
    return paginated_response(request, orders, OrderSerializer)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def order_detail(request, order_id):
    if request.method in ['PUT', 'PATCH']:
        with transaction.atomic():
            order = get_object_or_404(Order.objects.select_for_update().select_related('vendor', 'rider'), id=order_id)
            serializer = OrderDetailSerializer(order, data=request.data, partial=request.method == 'PATCH', context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
    return resource_detail(request, get_object_or_404(Order.objects.select_related('vendor', 'rider'), id=order_id), OrderDetailSerializer)

@api_view(['POST'])
def verify_order_pickup(request, order_id):
    submitted_code = str(request.data.get('pickup_code', '')).strip()
    with transaction.atomic():
        order = get_object_or_404(Order.objects.select_for_update().select_related('vendor', 'rider'), id=order_id)
        if order.status != Order.Status.ASSIGNED or order.rider_id is None:
            return Response({'detail': 'Pickup can only be verified for an assigned order.'}, status=status.HTTP_400_BAD_REQUEST)
        if not submitted_code or not secrets.compare_digest(submitted_code, order.pickup_code):
            return Response({'pickup_code': ['Invalid pickup code.']}, status=status.HTTP_400_BAD_REQUEST)
        order.status = Order.Status.PICKED_UP
        order.save(update_fields=['status', 'updated_at'])
    return Response(OrderDetailSerializer(order, context={'request': request}).data)

@api_view(['GET'])
def current_pricing(request):
    pricing = PricingConfiguration.current()
    if pricing is None:
        return Response({'detail': 'Delivery pricing is not configured.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response(PricingConfigurationSerializer(pricing).data)

@api_view(['GET'])
def dashboard_analytics(request):
    zero_money = Decimal('0.00')
    money_field = DecimalField(max_digits=14, decimal_places=2)
    orders = Order.objects.all()
    order_counts = {row['status']: row['count'] for row in orders.values('status').annotate(count=Count('id'))}
    reportable = orders.exclude(status=Order.Status.CANCELLED)
    delivered = orders.filter(status=Order.Status.DELIVERED)
    expected = orders.filter(status__in=[Order.Status.PENDING, Order.Status.ASSIGNED, Order.Status.PICKED_UP])
    revenue = reportable.aggregate(
        average=Coalesce(Avg('delivery_fee'), zero_money, output_field=money_field),
    )
    delivered_totals = delivered.aggregate(
        revenue=Coalesce(Sum('delivery_fee'), zero_money, output_field=money_field),
        weight=Coalesce(Sum('weight_kg'), zero_money, output_field=money_field),
    )
    expected_revenue = expected.aggregate(
        revenue=Coalesce(Sum('delivery_fee'), zero_money, output_field=money_field),
    )['revenue']
    weight = reportable.aggregate(
        total=Coalesce(Sum('weight_kg'), zero_money, output_field=money_field),
        average=Coalesce(Avg('weight_kg'), zero_money, output_field=money_field),
    )
    vendor_counts = {row['status']: row['count'] for row in Vendor.objects.values('status').annotate(count=Count('id'))}
    rider_counts = {row['status']: row['count'] for row in Rider.objects.values('status').annotate(count=Count('id'))}

    today = timezone.localdate()
    trend_start = today - timedelta(days=6)
    trend_rows = delivered.filter(created_at__date__gte=trend_start).annotate(date=TruncDate('created_at')).values('date').annotate(
        revenue=Coalesce(Sum('delivery_fee'), zero_money, output_field=money_field),
    ).order_by('date')
    revenue_by_date = {row['date']: row['revenue'] for row in trend_rows}
    revenue_trend = [
        {'date': (trend_start + timedelta(days=offset)).isoformat(), 'revenue': str(revenue_by_date.get(trend_start + timedelta(days=offset), zero_money))}
        for offset in range(7)
    ]
    recent_orders = orders.select_related('vendor', 'rider')[:5]

    return Response({
        'total_orders': sum(order_counts.values()),
        **{f'{status_value}_orders': order_counts.get(status_value, 0) for status_value in Order.Status.values},
        # Revenue is earned only when an order is delivered. Expected revenue is reported separately.
        'total_revenue': str(delivered_totals['revenue']),
        'delivered_revenue': str(delivered_totals['revenue']),
        'pending_revenue': str(expected_revenue),
        'average_order_value': str(revenue['average']),
        'total_weight_kg': str(weight['total']),
        'delivered_weight_kg': str(delivered_totals['weight']),
        'average_order_weight_kg': str(weight['average']),
        'total_vendors': sum(vendor_counts.values()),
        'active_vendors': vendor_counts.get(Vendor.Status.ACTIVE, 0),
        'pending_vendors': vendor_counts.get(Vendor.Status.PENDING, 0),
        'inactive_vendors': vendor_counts.get(Vendor.Status.INACTIVE, 0),
        'total_riders': sum(rider_counts.values()),
        'available_riders': rider_counts.get(Rider.Status.AVAILABLE, 0),
        'riders_on_delivery': rider_counts.get(Rider.Status.ON_DELIVERY, 0),
        'inactive_riders': rider_counts.get(Rider.Status.OFFLINE, 0),
        'recent_orders': [{
            'id': str(order.id), 'reference': order.reference,
            'vendor': order.vendor.name, 'recipient': order.recipient_name,
            'status': order.status, 'weight_kg': str(order.weight_kg) if order.weight_kg is not None else None,
            'delivery_fee': str(order.delivery_fee),
            'assigned_rider': order.rider.full_name if order.rider else None,
            'created_at': order.created_at,
        } for order in recent_orders],
        'revenue_trend': revenue_trend,
    })

@api_view(['GET'])
def vendor_dashboard(request):
    counts = Vendor.objects.values('status').annotate(count=Count('id'))
    summary = {item['status']: item['count'] for item in counts}
    return Response({'total_vendors': sum(summary.values()), 'active_vendors': summary.get('active', 0), 'inactive_vendors': summary.get('inactive', 0), 'pending_vendors': summary.get('pending', 0), 'pending': VendorSerializer(Vendor.objects.filter(status='pending')[:5], many=True).data})
