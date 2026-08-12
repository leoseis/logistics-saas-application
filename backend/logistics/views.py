from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import Order, Rider, Vehicle, Vendor
from .serializers import OrderSerializer, RiderSerializer, VehicleSerializer, VendorSerializer

def paginated_response(request, queryset, serializer_class):
    paginator = PageNumberPagination()
    paginator.page_size = min(int(request.query_params.get('page_size', 20)), 100)
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response(serializer_class(page, many=True).data)

def resource_detail(request, instance, serializer_class):
    if request.method == 'GET': return Response(serializer_class(instance).data)
    if request.method == 'DELETE': instance.delete(); return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = serializer_class(instance, data=request.data, partial=request.method == 'PATCH')
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
    riders = Rider.objects.annotate(active_order_count=Count('orders', filter=Q(orders__status__in=['assigned', 'picked_up']))).filter(Q(full_name__icontains=query) | Q(phone__icontains=query)).order_by('full_name')
    return paginated_response(request, riders, RiderSerializer)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def rider_detail(request, rider_id): return resource_detail(request, get_object_or_404(Rider.objects.annotate(active_order_count=Count('orders')), id=rider_id), RiderSerializer)

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
        serializer = OrderSerializer(data=request.data); serializer.is_valid(raise_exception=True); serializer.save(); return Response(serializer.data, status=status.HTTP_201_CREATED)
    orders = Order.objects.select_related('vendor', 'rider')
    if value := request.query_params.get('status'): orders = orders.filter(status=value)
    if value := request.query_params.get('vendor'): orders = orders.filter(vendor_id=value)
    return paginated_response(request, orders, OrderSerializer)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def order_detail(request, order_id): return resource_detail(request, get_object_or_404(Order.objects.select_related('vendor', 'rider'), id=order_id), OrderSerializer)

@api_view(['GET'])
def vendor_dashboard(request):
    counts = Vendor.objects.values('status').annotate(count=Count('id'))
    summary = {item['status']: item['count'] for item in counts}
    return Response({'total_vendors': sum(summary.values()), 'active_vendors': summary.get('active', 0), 'inactive_vendors': summary.get('inactive', 0), 'pending_vendors': summary.get('pending', 0), 'pending': VendorSerializer(Vendor.objects.filter(status='pending')[:5], many=True).data})
