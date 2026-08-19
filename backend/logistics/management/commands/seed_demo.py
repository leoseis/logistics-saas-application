from django.core.management.base import BaseCommand
from logistics.models import Vendor

VENDORS = [
    ('Harbor Goods', 'Clothing', 'Darlene Robertson', '+234 802 100 0001', 'harbor@example.test', '12 Marina Road, Lagos', 'pending'),
    ('Nova Finds', 'Electric', 'Annette Black', '+234 802 100 0002', 'nova@example.test', '24 New Market, Lagos', 'inactive'),
    ('The Local Loft', 'Clothing', 'Savannah Nguyen', '+234 802 100 0003', 'loft@example.test', '4 Admiralty Way, Lekki', 'active'),
    ('Swift & Style', 'Accessories', 'Marvin McKinney', '+234 802 100 0004', 'swift@example.test', '82 Subidbazar, Lagos', 'active'),
    ('Trend Haven', 'Electric', 'Albert Flores', '+234 802 100 0005', 'trend@example.test', '64 Khandipas, Lagos', 'pending'),
    ('Urban Cart', 'Clothing', 'Cody Fisher', '+234 802 100 0006', 'urban@example.test', '13 Kataria, Ikeja', 'active'),
    ('Maple & Main', 'Electric', 'Ronald Richards', '+234 802 100 0007', 'maple@example.test', '15 South Goli, Lagos', 'active'),
]

class Command(BaseCommand):
    help = 'Create or update local demo vendors for the dashboard.'
    def handle(self, *args, **options):
        for name, business_type, owner_name, phone, email, address, status in VENDORS:
            Vendor.objects.update_or_create(email=email, defaults={'name':name, 'business_type':business_type, 'owner_name':owner_name, 'phone':phone, 'address':address, 'status':status})
        self.stdout.write(self.style.SUCCESS(f'Demo data ready ({len(VENDORS)} vendors).'))
