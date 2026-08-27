from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Order, PricingConfiguration, Rider, Vendor

class LogisticsApiTests(APITestCase):
    def setUp(self):
        self.vendor = Vendor.objects.create(name='Harbor Goods', business_type='Clothing', owner_name='Darlene Robertson', phone='+234800000', email='vendor@example.com', address='12 Marina Road', status='active')

    def test_creates_and_filters_vendors(self):
        response = self.client.get('/api/vendors/?status=active&q=Harbor')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Harbor Goods')

    def test_rejects_order_for_inactive_vendor(self):
        self.vendor.status = 'inactive'; self.vendor.save()
        response = self.client.post('/api/orders/', {'reference':'ORD-1001', 'vendor':str(self.vendor.id), 'pickup_address':'A', 'delivery_address':'B', 'recipient_name':'Sam', 'recipient_phone':'+234801', 'delivery_fee':'2000.00'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_offline_rider_assignment(self):
        rider = Rider.objects.create(full_name='Ada Okafor', phone='+23480999', email='ada@example.com', status='offline')
        response = self.client.post('/api/orders/', {'reference':'ORD-1002', 'vendor':str(self.vendor.id), 'rider':str(rider.id), 'status':'assigned', 'pickup_address':'A', 'delivery_address':'B', 'recipient_name':'Sam', 'recipient_phone':'+234801', 'delivery_fee':'2000.00'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_searches_orders_across_logistics_fields(self):
        Order.objects.create(reference='ORD-SEARCH-01', vendor=self.vendor, pickup_address='Marina', delivery_address='Ikeja', recipient_name='Amaka Obi', recipient_phone='+23480222', delivery_fee='2500.00')
        response = self.client.get('/api/orders/?q=Amaka')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['reference'], 'ORD-SEARCH-01')

    def test_searches_and_filters_riders(self):
        Rider.objects.create(full_name='Tola Driver', phone='+23480777', email='tola@example.com', status='available')
        Rider.objects.create(full_name='Musa Driver', phone='+23480888', email='musa@example.com', status='offline')
        response = self.client.get('/api/riders/?q=tola@example.com&status=available')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['full_name'], 'Tola Driver')

    def make_order(self, reference='ORD-ASSIGN-01', **changes):
        values = {'reference': reference, 'vendor': self.vendor, 'pickup_address': 'Marina',
                  'delivery_address': 'Ikeja', 'recipient_name': 'Sam',
                  'recipient_phone': '+234801', 'delivery_fee': '2000.00'}
        values.update(changes)
        return Order.objects.create(**values)

    def make_rider(self, status_value=Rider.Status.AVAILABLE, suffix='1'):
        return Rider.objects.create(full_name=f'Rider {suffix}', phone=f'+2348099{suffix}',
                                    email=f'rider{suffix}@example.com', status=status_value)

    def test_available_rider_can_be_assigned_and_details_are_returned(self):
        order = self.make_order()
        rider = self.make_rider()
        response = self.client.patch(f'/api/orders/{order.id}/', {'rider': str(rider.id)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db(); rider.refresh_from_db()
        self.assertEqual(order.status, Order.Status.ASSIGNED)
        self.assertEqual(order.rider, rider)
        self.assertEqual(rider.status, Rider.Status.ON_DELIVERY)
        self.assertEqual(response.data['rider_name'], rider.full_name)
        self.assertEqual(response.data['rider_phone'], rider.phone)
        self.assertEqual(response.data['rider_status'], Rider.Status.ON_DELIVERY)

    def test_unavailable_rider_cannot_be_assigned(self):
        order = self.make_order()
        rider = self.make_rider(Rider.Status.ON_DELIVERY)
        response = self.client.patch(f'/api/orders/{order.id}/', {'rider': str(rider.id)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        order.refresh_from_db()
        self.assertIsNone(order.rider)

    def test_delivered_order_releases_rider(self):
        rider = self.make_rider(Rider.Status.ON_DELIVERY)
        order = self.make_order(rider=rider, status=Order.Status.PICKED_UP)
        response = self.client.patch(f'/api/orders/{order.id}/', {'status': Order.Status.DELIVERED}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rider.refresh_from_db(); order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DELIVERED)
        self.assertEqual(rider.status, Rider.Status.AVAILABLE)

    def test_cancelled_assigned_order_releases_rider(self):
        rider = self.make_rider(Rider.Status.ON_DELIVERY)
        order = self.make_order(rider=rider, status=Order.Status.ASSIGNED)
        response = self.client.patch(f'/api/orders/{order.id}/', {'status': Order.Status.CANCELLED}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rider.refresh_from_db(); order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(rider.status, Rider.Status.AVAILABLE)

    def test_terminal_orders_cannot_be_assigned(self):
        rider = self.make_rider()
        for index, terminal_status in enumerate([Order.Status.DELIVERED, Order.Status.CANCELLED], start=1):
            order = self.make_order(reference=f'ORD-TERMINAL-{index}', status=terminal_status)
            response = self.client.patch(f'/api/orders/{order.id}/', {'rider': str(rider.id)}, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_rider_cannot_be_assigned_to_two_active_orders(self):
        rider = self.make_rider()
        first = self.make_order(reference='ORD-FIRST')
        second = self.make_order(reference='ORD-SECOND')
        self.assertEqual(self.client.patch(f'/api/orders/{first.id}/', {'rider': str(rider.id)}, format='json').status_code, status.HTTP_200_OK)
        response = self.client.patch(f'/api/orders/{second.id}/', {'rider': str(rider.id)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def pricing_payload(self, reference='ORD-PRICE-01', **changes):
        values = {'reference': reference, 'vendor': str(self.vendor.id), 'pickup_address': 'Marina',
                  'delivery_address': 'Ikeja', 'recipient_name': 'Sam',
                  'recipient_phone': '+234801', 'weight_kg': '8.00'}
        values.update(changes)
        return values

    def test_calculates_delivery_fee_from_configured_rate(self):
        response = self.client.post('/api/orders/', self.pricing_payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data['price_per_kg']), Decimal('1500.00'))
        self.assertEqual(Decimal(response.data['delivery_fee']), Decimal('12000.00'))

    def test_calculates_decimal_weight(self):
        response = self.client.post('/api/orders/', self.pricing_payload(weight_kg='2.75'), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data['delivery_fee']), Decimal('4125.00'))

    def test_rejects_zero_and_negative_weight(self):
        for index, weight in enumerate(['0', '-1'], start=1):
            response = self.client.post('/api/orders/', self.pricing_payload(reference=f'ORD-BAD-{index}', weight_kg=weight), format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('weight_kg', response.data)

    def test_changing_weight_recalculates_fee_and_rate_snapshot(self):
        created = self.client.post('/api/orders/', self.pricing_payload(weight_kg='5'), format='json')
        PricingConfiguration.objects.create(price_per_kg=Decimal('2000.00'), is_active=True)
        response = self.client.patch(f"/api/orders/{created.data['id']}/", {'weight_kg': '10'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['price_per_kg']), Decimal('2000.00'))
        self.assertEqual(Decimal(response.data['delivery_fee']), Decimal('20000.00'))

    def test_frontend_fee_cannot_override_backend_calculation(self):
        payload = self.pricing_payload(delivery_fee='1.00', price_per_kg='0.01')
        response = self.client.post('/api/orders/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data['delivery_fee']), Decimal('12000.00'))
        patch = self.client.patch(f"/api/orders/{response.data['id']}/", {'delivery_fee': '1.00'}, format='json')
        self.assertEqual(Decimal(patch.data['delivery_fee']), Decimal('12000.00'))

    def test_current_pricing_endpoint_returns_active_rate(self):
        PricingConfiguration.objects.create(price_per_kg=Decimal('1750.50'), is_active=True)
        response = self.client.get('/api/pricing/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['price_per_kg']), Decimal('1750.50'))

class DashboardAnalyticsTests(APITestCase):
    def setUp(self):
        self.vendor = Vendor.objects.create(name='Analytics Vendor', business_type='Retail', owner_name='Owner', phone='+2348001', email='analytics@example.com', address='Lagos', status=Vendor.Status.ACTIVE)

    def order(self, reference, status_value, fee):
        return Order.objects.create(reference=reference, vendor=self.vendor, pickup_address='A', delivery_address='B', recipient_name='Customer', recipient_phone='+2348002', status=status_value, weight_kg=None, delivery_fee=fee, price_per_kg=None)

    def test_revenue_status_and_average_analytics(self):
        self.order('AN-DELIVERED', Order.Status.DELIVERED, Decimal('12000.00'))
        self.order('AN-PENDING', Order.Status.PENDING, Decimal('6000.00'))
        self.order('AN-CANCELLED', Order.Status.CANCELLED, Decimal('99000.00'))
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_orders'], 3)
        self.assertEqual(response.data['delivered_orders'], 1)
        self.assertEqual(response.data['pending_orders'], 1)
        self.assertEqual(response.data['cancelled_orders'], 1)
        self.assertEqual(Decimal(response.data['delivered_revenue']), Decimal('12000.00'))
        self.assertEqual(Decimal(response.data['total_revenue']), Decimal('12000.00'))
        self.assertEqual(Decimal(response.data['pending_revenue']), Decimal('6000.00'))
        self.assertEqual(Decimal(response.data['average_order_value']), Decimal('9000.00'))

    def test_vendor_and_rider_counts(self):
        Vendor.objects.create(name='Pending Vendor', business_type='Retail', owner_name='Owner', phone='+2348003', email='pending@example.com', address='Lagos', status=Vendor.Status.PENDING)
        Vendor.objects.create(name='Inactive Vendor', business_type='Retail', owner_name='Owner', phone='+2348004', email='inactive@example.com', address='Lagos', status=Vendor.Status.INACTIVE)
        Rider.objects.create(full_name='Available Rider', phone='+2348101', email='available@example.com', status=Rider.Status.AVAILABLE)
        Rider.objects.create(full_name='Busy Rider', phone='+2348102', email='busy@example.com', status=Rider.Status.ON_DELIVERY)
        Rider.objects.create(full_name='Offline Rider', phone='+2348103', email='offline@example.com', status=Rider.Status.OFFLINE)
        response = self.client.get('/api/dashboard/')
        self.assertEqual((response.data['total_vendors'], response.data['active_vendors'], response.data['pending_vendors'], response.data['inactive_vendors']), (3, 1, 1, 1))
        self.assertEqual((response.data['total_riders'], response.data['available_riders'], response.data['riders_on_delivery'], response.data['inactive_riders']), (3, 1, 1, 1))

class EmptyDashboardAnalyticsTests(APITestCase):
    def test_empty_database_returns_zero_values_and_seven_day_trend(self):
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for field in ['total_orders', 'pending_orders', 'assigned_orders', 'picked_up_orders', 'delivered_orders', 'cancelled_orders', 'total_vendors', 'total_riders']:
            self.assertEqual(response.data[field], 0)
        for field in ['total_revenue', 'delivered_revenue', 'pending_revenue', 'average_order_value', 'total_weight_kg', 'delivered_weight_kg', 'average_order_weight_kg']:
            self.assertEqual(Decimal(response.data[field]), Decimal('0.00'))
        self.assertEqual(response.data['recent_orders'], [])
        self.assertEqual(len(response.data['revenue_trend']), 7)

@override_settings(MEDIA_ROOT='/tmp/logistics-test-media')
class PickupEvidenceTests(APITestCase):
    def setUp(self):
        self.vendor = Vendor.objects.create(name='Evidence Vendor', business_type='Retail', owner_name='Owner', phone='+2348201', email='evidence@example.com', address='Lagos', status=Vendor.Status.ACTIVE)
        self.rider = Rider.objects.create(full_name='Evidence Rider', phone='+2348202', email='evidence-rider@example.com', status=Rider.Status.ON_DELIVERY)

    def assigned_order(self, reference='PICKUP-001', **changes):
        values = dict(reference=reference, vendor=self.vendor, rider=self.rider, pickup_address='A', delivery_address='B', recipient_name='Customer', recipient_phone='+2348203', status=Order.Status.ASSIGNED, weight_kg=None, delivery_fee=Decimal('1500.00'))
        values.update(changes)
        return Order.objects.create(**values)

    def test_pickup_code_is_generated_automatically_and_unique(self):
        first = self.assigned_order()
        second = self.assigned_order(reference='PICKUP-002')
        self.assertRegex(first.pickup_code, r'^\d{6}$')
        self.assertNotEqual(first.pickup_code, second.pickup_code)

    def test_frontend_cannot_control_pickup_code(self):
        response = self.client.post('/api/orders/', {'reference':'PICKUP-POST', 'vendor':str(self.vendor.id), 'pickup_address':'A', 'delivery_address':'B', 'recipient_name':'Customer', 'recipient_phone':'+2348203', 'weight_kg':'1.00', 'pickup_code':'111111'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(pk=response.data['id'])
        self.assertNotEqual(order.pickup_code, '111111')
        self.assertNotIn('pickup_code', response.data)

    def test_correct_code_verifies_and_changes_assigned_to_picked_up(self):
        order = self.assigned_order()
        response = self.client.post(f'/api/orders/{order.id}/verify-pickup/', {'pickup_code':order.pickup_code}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PICKED_UP)

    def test_incorrect_code_does_not_change_status(self):
        order = self.assigned_order()
        response = self.client.post(f'/api/orders/{order.id}/verify-pickup/', {'pickup_code':'000000' if order.pickup_code != '000000' else '999999'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['pickup_code'], ['Invalid pickup code.'])
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.ASSIGNED)

    def test_invalid_lifecycle_states_cannot_verify(self):
        for index, state in enumerate([Order.Status.DELIVERED, Order.Status.CANCELLED, Order.Status.PENDING], start=1):
            order = self.assigned_order(reference=f'PICKUP-STATE-{index}', status=state, rider=None if state == Order.Status.PENDING else self.rider)
            response = self.client.post(f'/api/orders/{order.id}/verify-pickup/', {'pickup_code':order.pickup_code}, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verification_cannot_be_reused(self):
        order = self.assigned_order()
        self.assertEqual(self.client.post(f'/api/orders/{order.id}/verify-pickup/', {'pickup_code':order.pickup_code}, format='json').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(f'/api/orders/{order.id}/verify-pickup/', {'pickup_code':order.pickup_code}, format='json').status_code, status.HTTP_400_BAD_REQUEST)

    def test_normal_status_patch_cannot_bypass_verification(self):
        order = self.assigned_order()
        response = self.client.patch(f'/api/orders/{order.id}/', {'status':Order.Status.PICKED_UP}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.ASSIGNED)

    def test_package_image_can_be_uploaded_and_creation_without_image_still_works(self):
        gif = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        image = SimpleUploadedFile('package.gif', gif, content_type='image/gif')
        payload = {'reference':'PHOTO-001', 'vendor':str(self.vendor.id), 'pickup_address':'A', 'delivery_address':'B', 'recipient_name':'Customer', 'recipient_phone':'+2348203', 'weight_kg':'1.00', 'package_photo':image}
        response = self.client.post('/api/orders/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('/media/orders/packages/', response.data['package_photo'])
        without_photo = {**payload, 'reference':'PHOTO-002'}
        without_photo.pop('package_photo')
        response = self.client.post('/api/orders/', without_photo, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
