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
