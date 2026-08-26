from rest_framework import status
from rest_framework.test import APITestCase
from .models import Order, Rider, Vendor

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
