# Truelog Logistics Platform

A logistics administration prototype with a React/Vite dashboard and a Django REST Framework API. The backend owns vendors, riders, vehicles, and delivery orders; it exposes JSON endpoints designed for the dashboard and future client applications.

## Project structure

```text
src/                 React dashboard and design system
backend/config/      Django project configuration
backend/logistics/   Logistics models, serializers, views, routes, and tests
requirements.txt     Backend dependencies
```

## Frontend

```bash
npm install
npm run dev
```

The dashboard is at `http://localhost:5173/`; the component styleguide is at `http://localhost:5173/#/styleguide`.

## Backend setup

The project expects Python 3.10+ and uses SQLite for local development. A local virtual environment keeps Python dependencies out of the system installation.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py runserver
```

The API is then available at `http://127.0.0.1:8000/api/`. CORS allows the Vite development server at `http://localhost:5173` and `http://127.0.0.1:5173`.

To create an administrator for Django Admin:

```bash
.venv/bin/python backend/manage.py createsuperuser
```

Visit `http://127.0.0.1:8000/admin/` to manage records through Django Admin.

## Data model

All primary resources use UUID identifiers and include `created_at` and `updated_at` timestamps.

| Model | Purpose | Important relationships |
| --- | --- | --- |
| `Vendor` | A business that creates deliveries. | Has many orders. An order’s vendor cannot be deleted while that order exists. |
| `Rider` | A delivery operator. | Can be assigned many orders and at most one vehicle. |
| `Vehicle` | Delivery bike, van, or truck. | May be assigned to one rider. |
| `Order` | A delivery request. | Belongs to one vendor and can be assigned to one rider. |

### Supported status values

| Resource | Values |
| --- | --- |
| Vendor | `active`, `inactive`, `pending` |
| Rider | `available`, `on_delivery`, `offline` |
| Vehicle | `available`, `in_service`, `maintenance` |
| Order | `pending`, `assigned`, `picked_up`, `delivered`, `cancelled` |

Vehicle types are `bike`, `van`, and `truck`.

## API reference

Base URL: `http://127.0.0.1:8000/api/`

| Resource | Collection endpoint | Detail endpoint |
| --- | --- | --- |
| Vendor | `GET`, `POST /vendors/` | `GET`, `PUT`, `PATCH`, `DELETE /vendors/<uuid>/` |
| Rider | `GET`, `POST /riders/` | `GET`, `PUT`, `PATCH`, `DELETE /riders/<uuid>/` |
| Vehicle | `GET`, `POST /vehicles/` | `GET`, `PUT`, `PATCH`, `DELETE /vehicles/<uuid>/` |
| Order | `GET`, `POST /orders/` | `GET`, `PUT`, `PATCH`, `DELETE /orders/<uuid>/` |
| Vendor dashboard | `GET /dashboard/vendors/` | — |

All collection responses use DRF page-number pagination:

```json
{
  "count": 42,
  "next": "http://127.0.0.1:8000/api/vendors/?page=2",
  "previous": null,
  "results": []
}
```

Pass `page` and `page_size` to collection routes; `page_size` is capped at 100. Available filters:

| Endpoint | Filters |
| --- | --- |
| `/vendors/` | `q` searches name, owner, or email; `status` filters vendor status. |
| `/riders/` | `q` searches name or phone. |
| `/vehicles/` | `status` filters vehicle status. |
| `/orders/` | `status` filters order status; `vendor` accepts a vendor UUID. |

### Dashboard endpoint

`GET /api/dashboard/vendors/` returns vendor totals by status and up to five pending vendors for the dashboard’s summary and pending-vendor panel.

```json
{
  "total_vendors": 12,
  "active_vendors": 8,
  "inactive_vendors": 2,
  "pending_vendors": 2,
  "pending": []
}
```

## Request examples

Create an active vendor:

```bash
curl -X POST http://127.0.0.1:8000/api/vendors/ \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Harbor Goods",
    "business_type": "Clothing",
    "owner_name": "Darlene Robertson",
    "phone": "+2348000000000",
    "email": "hello@harborgoods.test",
    "address": "12 Marina Road, Lagos",
    "status": "active"
  }'
```

Create a rider:

```bash
curl -X POST http://127.0.0.1:8000/api/riders/ \
  -H 'Content-Type: application/json' \
  -d '{
    "full_name": "Ada Okafor",
    "phone": "+2348012345678",
    "email": "ada@example.test",
    "status": "available",
    "rating": "4.8"
  }'
```

Create a vehicle, optionally assigning a rider UUID:

```bash
curl -X POST http://127.0.0.1:8000/api/vehicles/ \
  -H 'Content-Type: application/json' \
  -d '{
    "registration_number": "LAG-123-XY",
    "vehicle_type": "bike",
    "capacity_kg": 25,
    "status": "available",
    "assigned_rider": "<rider_uuid>"
  }'
```

Create an assigned order:

```bash
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H 'Content-Type: application/json' \
  -d '{
    "reference": "ORD-1001",
    "vendor": "<vendor_uuid>",
    "rider": "<rider_uuid>",
    "pickup_address": "12 Marina Road, Lagos",
    "delivery_address": "4 Admiralty Way, Lekki",
    "recipient_name": "Tunde Ade",
    "recipient_phone": "+2348098765432",
    "status": "assigned",
    "delivery_fee": "2500.00"
  }'
```

Partially update a resource with `PATCH`:

```bash
curl -X PATCH http://127.0.0.1:8000/api/orders/<order_uuid>/ \
  -H 'Content-Type: application/json' \
  -d '{"status": "picked_up"}'
```

## Validation and business rules

- Orders can only be created or updated for a vendor whose status is `active`.
- Riders with status `offline` cannot be assigned to an order.
- Orders in `assigned` or `picked_up` status must have a rider.
- A vehicle in `maintenance` cannot be assigned to a rider.
- Rider phone numbers and emails, vehicle registration numbers, and order references are unique.
- Invalid payloads return HTTP `400` with field-level JSON errors. Successful creates return `201`; successful deletes return `204`.

## Testing and checks

Run backend tests and Django’s configuration checks:

```bash
.venv/bin/python backend/manage.py test logistics
.venv/bin/python backend/manage.py check
```

The current tests cover vendor filtering plus order validation for inactive vendors and offline riders.

## Deployment notes

Before deploying, set a secure `SECRET_KEY`, set `DEBUG = False`, populate `ALLOWED_HOSTS`, replace the local SQLite database with the chosen production database, and restrict `CORS_ALLOWED_ORIGINS` to the deployed frontend origin. Add authentication and permissions before exposing write endpoints publicly.
