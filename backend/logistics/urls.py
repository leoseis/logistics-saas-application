from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/vendors/', views.vendor_dashboard, name='vendor-dashboard'),
    path('vendors/', views.vendor_list, name='vendor-list'), path('vendors/<uuid:vendor_id>/', views.vendor_detail, name='vendor-detail'),
    path('riders/', views.rider_list, name='rider-list'), path('riders/<uuid:rider_id>/', views.rider_detail, name='rider-detail'),
    path('vehicles/', views.vehicle_list, name='vehicle-list'), path('vehicles/<uuid:vehicle_id>/', views.vehicle_detail, name='vehicle-detail'),
    path('orders/', views.order_list, name='order-list'), path('orders/<uuid:order_id>/', views.order_detail, name='order-detail'),
    path('pricing/', views.current_pricing, name='current-pricing'),
]
