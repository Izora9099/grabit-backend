# GrabIT Backend

REST API for the **GrabIT** marketplace platform — a multi-role e-commerce system for Cameroon with escrow-secured payments, vendor shops, delivery agents, and an admin console.

Built with **Django 4.2** + **Django REST Framework**.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Prerequisites](#prerequisites)
3. [Getting Started](#getting-started)
4. [Project Structure](#project-structure)
5. [User Roles](#user-roles)
6. [Authentication](#authentication)
7. [API Reference](#api-reference)
8. [Frontend Endpoint Reference](#frontend-endpoint-reference)
9. [Key Workflows](#key-workflows)
10. [Environment Variables](#environment-variables)
11. [Running Tests](#running-tests)
12. [Deployment](#deployment)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.2 |
| API | Django REST Framework 3.15 |
| Auth | DRF Token Authentication |
| Filtering | django-filter |
| API Docs | drf-spectacular (OpenAPI 3 / Swagger) |
| Images | Pillow |
| Config | python-decouple |
| Dev server | Django `runserver` |
| Production server | Gunicorn + Whitenoise |
| Database (dev) | SQLite |
| Database (prod) | PostgreSQL |

---

## Prerequisites

- Python 3.8+
- pip

---

## Getting Started

### 1. Clone the repository

```bash
git clone <repo-url>
cd grabit-backend
```

### 2. Create and activate a virtual environment

```bash
# Create
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set at minimum:

```env
SECRET_KEY=<generate a new key — see .env.example for the command>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Create a superuser (admin account)

```bash
python manage.py createsuperuser
```

Use role `admin` when prompted (or update it via the Django admin panel afterwards).

### 7. Start the development server

```bash
python manage.py runserver
```

The API is now available at **http://localhost:8000**

| URL | Purpose |
|---|---|
| http://localhost:8000/api/v1/ | API root |
| http://localhost:8000/api/docs/ | Swagger UI (interactive docs) |
| http://localhost:8000/api/redoc/ | ReDoc (alternative docs) |
| http://localhost:8000/admin/ | Django admin panel |

### 8. Connect the frontend

In the GrabIT React app (`grabit/`), create `.env.local`:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Project Structure

```
grabit-backend/
├── config/                  # Project configuration
│   ├── settings/
│   │   ├── base.py          # Shared settings (all environments)
│   │   ├── development.py   # Dev overrides (SQLite, permissive CORS)
│   │   └── production.py    # Prod overrides (PostgreSQL, Whitenoise)
│   ├── urls.py              # Root URL routing + API docs
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/                # User auth, profiles, addresses, admin views
├── products/                # Product catalog, reviews, wishlist
├── shops/                   # Vendor shops, follow system, KYC documents
├── orders/                  # Orders, escrow events, in-app messaging
├── payments/                # Payment initiation, vendor/agent payouts
├── notifications/           # User notification feed
├── disputes/                # Dispute filing and admin resolution
│
├── media/                   # User-uploaded files (gitignored)
├── venv/                    # Virtual environment (gitignored)
├── db.sqlite3               # SQLite database (gitignored, dev only)
├── manage.py
├── requirements.txt
├── .env                     # Local secrets (gitignored)
└── .env.example             # Template for .env
```

---

## User Roles

| Role | Description |
|---|---|
| `buyer` | Browses products, places orders, files disputes |
| `vendor` | Owns a shop, manages products and orders, receives payouts |
| `agent` | Assigned to deliver orders, updates delivery status |
| `admin` | Full platform access — approves KYC, resolves disputes, views analytics |

Role is set at registration and cannot be changed by the user.

---

## Authentication

The API uses **DRF Token Authentication**.

### Register

```http
POST /api/v1/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secret123",
  "first_name": "Lemuel",
  "last_name": "Ndifonl",
  "role": "buyer",
  "phone": "6XXXXXXXX",
  "city": "Douala"
}
```

Response:
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user": { "id": 1, "email": "user@example.com", "role": "buyer", ... }
}
```

### Login

```http
POST /api/v1/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secret123"
}
```

### Using the token

Include this header on every authenticated request:

```http
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

> **Frontend note:** The token header uses `Token`, not `Bearer`. Update `src/lib/api.ts` to use `Authorization: Token ${token}`.

### Logout

```http
POST /api/v1/auth/logout/
Authorization: Token <token>
```

---

## API Reference

Interactive docs with try-it-out buttons are at **http://localhost:8000/api/docs/**

### Endpoints summary

#### Auth (`/api/v1/auth/`)
| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `register/` | Create account | Public |
| POST | `login/` | Get token | Public |
| POST | `logout/` | Invalidate token | Required |
| GET/PATCH | `me/` | Current user profile | Required |
| POST | `me/change-password/` | Change password | Required |
| GET/POST | `me/addresses/` | Delivery addresses | Required |
| GET/PATCH/DELETE | `me/addresses/<id>/` | Address detail | Required |

#### Products (`/api/v1/products/`)
| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `` | List live products | Public |
| GET | `<id>/` | Product detail | Public |
| GET/POST | `<id>/reviews/` | Reviews (POST requires auth) | Mixed |
| GET/POST | `wishlist/` | Wishlist | Required |
| DELETE | `wishlist/<id>/` | Remove from wishlist | Required |
| GET/POST | `vendor/` | Vendor's products | Vendor |
| GET/PATCH/DELETE | `vendor/<id>/` | Vendor product detail | Vendor |

Query params for product list: `search`, `category`, `city`, `condition`, `min_price`, `max_price`, `ordering`

#### Shops (`/api/v1/shops/`)
| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `` | List active shops | Public |
| GET | `<handle>/` | Shop detail | Public |
| GET | `<handle>/products/` | Shop's live products | Public |
| POST | `<handle>/follow/` | Follow / unfollow (toggle) | Required |
| GET/PATCH | `my/` | Vendor's own shop | Vendor |
| POST | `my/create/` | Create a new shop | Vendor |
| GET/POST | `my/kyc/` | KYC documents | Vendor |
| GET | `followed/` | Shops the user follows | Required |

#### Orders (`/api/v1/orders/`)
| Method | Path | Description | Auth |
|---|---|---|---|
| GET/POST | `` | List / create orders | Required |
| GET | `<order_id>/` | Order detail | Required |
| PATCH | `<order_id>/status/` | Advance order status | Vendor / Agent |
| POST | `<order_id>/confirm/` | Buyer confirms delivery | Buyer |
| POST | `<order_id>/cancel/` | Vendor cancels order (before pickup) | Vendor |
| POST | `<order_id>/decline/` | Agent declines assignment | Agent |
| GET/POST | `messages/` | In-app messages | Required |
| GET | `agent/assignments/` | Agent's deliveries | Agent |
| GET | `agent/stats/` | Agent earnings & stats | Agent |

#### Payments (`/api/v1/payments/`)
| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `initiate/` | Initiate MoMo / Orange payment | Required |
| GET | `payouts/` | Vendor / agent payout history | Required |

#### Notifications (`/api/v1/notifications/`)
| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `` | List notifications | Required |
| POST | `read-all/` | Mark all as read | Required |
| GET/PATCH | `<id>/` | Notification detail | Required |

#### Disputes (`/api/v1/disputes/`)
| Method | Path | Description | Auth |
|---|---|---|---|
| GET/POST | `` | List / file a dispute | Required |
| GET | `<dispute_id>/` | Dispute detail | Required |
| POST | `<dispute_id>/evidence/` | Upload / replace evidence file | Buyer |
| PATCH | `<dispute_id>/resolve/` | Resolve dispute | Admin |

#### Admin (`/api/v1/auth/admin/`)
| Method | Path | Description |
|---|---|---|
| GET | `stats/` | Platform KPIs |
| GET | `users/` | All users (filterable) |
| PATCH | `users/<id>/` | Edit user role / status |
| GET | `gmv/` | Daily revenue + top vendors |
| GET | `shops/` | All shops |
| GET | `verification/` | Vendor KYC queue |
| PATCH | `verification/<shop_id>/` | Approve / reject vendor shop |
| GET | `agent-verification/` | Agent KYC queue |
| PATCH | `agent-verification/<user_id>/` | Approve / reject agent KYC |
| GET | `disputes/` | All disputes |
| GET | `payouts/` | All payouts |
| GET | `commissions/` | Monthly commission report |
| GET | `health/` | System health checks |
| GET | `fraud/` | Fraud signal detection |

---

## Frontend Endpoint Reference

All endpoints are prefixed with `/api/v1`. Base URL in development: `http://localhost:8000`.

Every authenticated request must include:
```
Authorization: Token <token>
```

The token is returned by both `/auth/register/` and `/auth/login/`.

---

### Public — no auth required

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/auth/register/` | Body: `email`, `password`, `first_name`, `last_name`, `role`, `phone`, `city`. Returns `{token, user}` |
| POST | `/auth/login/` | Body: `email`, `password`. Returns `{token, user}` |
| GET | `/products/` | Query params: `search`, `category`, `city`, `condition`, `min_price`, `max_price`, `ordering` |
| GET | `/products/<id>/` | Full product detail |
| GET | `/products/<id>/reviews/` | All reviews for a product |
| GET | `/shops/` | Query params: `city`, `category` |
| GET | `/shops/<handle>/` | Shop detail by URL handle |
| GET | `/shops/<handle>/products/` | Live products from a specific shop |

---

### All authenticated users

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/auth/logout/` | Deletes the current token |
| GET | `/auth/me/` | Current user profile |
| PATCH | `/auth/me/` | Update profile fields (`first_name`, `last_name`, `phone`, `city`, `avatar`) |
| GET | `/auth/me/addresses/` | Saved delivery addresses |
| POST | `/auth/me/addresses/` | Add address. Body: `label`, `line`, `city`, `is_primary` |
| PATCH / DELETE | `/auth/me/addresses/<id>/` | Edit or remove a single address |
| POST | `/auth/me/change-password/` | Change password. Body: `current_password`, `new_password` (min 6 chars) |
| GET | `/notifications/` | Notification feed for the current user |
| POST | `/notifications/read-all/` | Mark every notification as read |
| PATCH | `/notifications/<id>/` | Mark a single notification read |

---

### Buyer

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/orders/` | Buyer's own orders |
| POST | `/orders/` | Place an order. Body: `shop` (id), `items` (array of `{product, quantity}`), `delivery_address`, `city` |
| GET | `/orders/<order_id>/` | Order detail (e.g. `GR-10001`) |
| POST | `/orders/<order_id>/confirm/` | Confirm delivery received — completes order and releases escrow |
| GET / POST | `/orders/messages/` | In-app messages with vendors. POST body: `recipient`, `order`, `body` |
| POST | `/payments/initiate/` | Trigger payment. Body: `order_id`, `method` (`mtn_momo` / `orange_money` / `bank_transfer`), `phone_number` |
| GET | `/products/wishlist/` | Wishlist items |
| POST | `/products/wishlist/` | Add to wishlist. Body: `product` (id) |
| DELETE | `/products/wishlist/<id>/` | Remove a wishlist item |
| POST | `/products/<id>/reviews/` | Post a review. Body: `rating` (1–5), `text` |
| POST | `/shops/<handle>/follow/` | Toggle follow/unfollow (returns `{following: true/false}`) |
| GET | `/shops/followed/` | All shops the buyer follows |
| GET | `/disputes/` | Buyer's disputes |
| POST | `/disputes/` | Open a dispute. Body: `order` (id), `reason`, `description` |
| GET | `/disputes/<dispute_id>/` | Dispute detail (e.g. `DSP-300`) |

---

### Vendor

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/shops/my/create/` | Create a new shop (first-time only). Body: `name`, `handle`, `category`, `city`, `tagline`, `description`, etc. |
| GET | `/shops/my/` | Vendor's own shop data |
| PATCH | `/shops/my/` | Update shop details |
| GET | `/shops/my/kyc/` | KYC documents uploaded for the shop |
| POST | `/shops/my/kyc/` | Upload a KYC document. Body: `doc_type`, `label` |
| GET | `/products/vendor/` | All of the vendor's products (all statuses) |
| POST | `/products/vendor/` | Create a product. Body: `name`, `description`, `price`, `category`, `condition`, `stock`, `status` |
| GET | `/products/vendor/<id>/` | Single vendor product |
| PATCH | `/products/vendor/<id>/` | Edit product fields |
| DELETE | `/products/vendor/<id>/` | Delete a product |
| GET | `/orders/` | Incoming orders for the vendor's shop |
| GET | `/orders/<order_id>/` | Order detail |
| PATCH | `/orders/<order_id>/status/` | Advance order status. Allowed transitions: `paid_escrow → preparing`, `preparing → agent_assigned` |
| POST | `/orders/<order_id>/cancel/` | Cancel order (only before pickup) |
| GET / POST | `/orders/messages/` | In-app messages with buyers |
| GET | `/payments/payouts/` | Payout history |

---

### Agent

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/orders/agent/assignments/` | Assigned deliveries. Optional query param: `status` |
| GET | `/orders/agent/stats/` | Returns `today_deliveries`, `week_deliveries`, `week_earnings`, `active_assignments` |
| GET | `/orders/<order_id>/` | Order detail |
| PATCH | `/orders/<order_id>/status/` | Advance delivery status. Allowed transitions: `agent_assigned → picked_up`, `picked_up → in_transit`, `in_transit → delivered_confirm` |
| POST | `/orders/<order_id>/decline/` | Decline assignment — order returns to `preparing` |
| GET / POST | `/orders/messages/` | In-app messages |
| GET | `/payments/payouts/` | Earnings / payout history |
| GET / POST | `/auth/me/agent-kyc/` | Agent KYC documents |
| GET / PATCH / DELETE | `/auth/me/agent-kyc/<id>/` | Single agent KYC document |

---

### Admin — `/auth/admin/` prefix, all require `role: admin`

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/auth/admin/stats/` | Platform KPIs: user counts, active shops, pending KYC, orders today, GMV |
| GET | `/auth/admin/gmv/` | Daily GMV for last 30 days + top 10 vendors by revenue |
| GET | `/auth/admin/commissions/` | Monthly commission report (last 12 months) |
| GET | `/auth/admin/users/` | All users. Query params: `role`, `q` (search by email/username) |
| PATCH | `/auth/admin/users/<id>/` | Toggle `is_active`, `role`, or `is_kyc_verified` |
| GET | `/auth/admin/shops/` | All shops. Query param: `q` |
| GET | `/auth/admin/verification/` | KYC queue — shops under review with their uploaded documents |
| PATCH | `/auth/admin/verification/<shop_id>/` | Approve or reject a shop. Body: `{"action": "approve"}` or `{"action": "reject"}` |
| GET | `/auth/admin/disputes/` | All disputes. Query param: `status` |
| PATCH | `/disputes/<dispute_id>/resolve/` | Resolve a dispute. Body: `resolution` (`refund_buyer` / `release_vendor` / `partial_refund`), `admin_note` |
| GET | `/auth/admin/payouts/` | All vendor/agent payouts |
| GET | `/auth/admin/health/` | System health checks (DB connectivity, recent order pipeline) |
| GET | `/auth/admin/fraud/` | Users flagged for ≥ 3 failed payment attempts |

---

## Key Workflows

### Placing an order

1. Buyer creates order → `POST /orders/` — status: `awaiting_payment`
2. Buyer initiates payment → `POST /payments/initiate/` — status: `paid_escrow`
3. Vendor prepares → `PATCH /orders/<id>/status/` `{"status": "preparing"}`
4. Vendor assigns agent → `PATCH /orders/<id>/status/` `{"status": "agent_assigned"}`
5. Agent accepts and picks up → `PATCH /orders/<id>/status/` `{"status": "picked_up"}`
6. Agent in transit → `PATCH /orders/<id>/status/` `{"status": "in_transit"}`
7. Agent delivers → `PATCH /orders/<id>/status/` `{"status": "delivered_confirm"}`
8. Buyer confirms → `POST /orders/<id>/confirm/` — status: `completed`, escrow released

> **Auto-release:** If the buyer does not confirm within **72 hours** of `delivered_confirm`, escrow is auto-released to the vendor and the order is marked `completed`.

**Terminal states:** `completed`, `cancelled`, `refunded`, `partially_resolved`

**Dispute path:** any order not yet `completed` can be escalated → status `disputed`. Admin resolves to:
- `release_vendor` → order `completed`, escrow released
- `refund_buyer` → order `refunded`, escrow returned
- `partial_refund` → order `partially_resolved`, escrow released with a note

### Filing a dispute

At any point before `completed`, the buyer can file a dispute:

```http
POST /api/v1/disputes/
Authorization: Token <token>

{
  "order": 1,
  "reason": "not_delivered",
  "description": "Package never arrived."
}
```

An admin then resolves it via `PATCH /disputes/<id>/resolve/` with `resolution: refund_buyer | release_vendor | partial_refund`.

### Vendor KYC / Shop verification

1. Vendor creates shop → `POST /shops/my/create/`
2. Vendor uploads KYC documents → `POST /shops/my/kyc/` (multipart/form-data)
3. Admin reviews queue → `GET /auth/admin/verification/`
4. Admin approves → `PATCH /auth/admin/verification/<shop_id>/` `{"action": "approve"}`
5. Shop status changes to `active`, `is_verified` set to `true`

### Agent KYC / Onboarding

1. Agent uploads KYC documents → `POST /auth/me/agent-kyc/` (multipart/form-data)
2. Admin reviews queue → `GET /auth/admin/agent-verification/`
3. Admin approves → `PATCH /auth/admin/agent-verification/<user_id>/` `{"action": "approve"}`
4. Agent `is_kyc_verified` set to `true`

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes | — | Django secret key |
| `DEBUG` | No | `False` | Enable debug mode |
| `ALLOWED_HOSTS` | Yes | — | Comma-separated hostnames |
| `CORS_ALLOWED_ORIGINS` | Prod | — | Comma-separated frontend origins |
| `DB_NAME` | Prod | — | PostgreSQL database name |
| `DB_USER` | Prod | — | PostgreSQL user |
| `DB_PASSWORD` | Prod | — | PostgreSQL password |
| `DB_HOST` | Prod | `localhost` | PostgreSQL host |
| `DB_PORT` | Prod | `5432` | PostgreSQL port |
| `EMAIL_HOST` | Prod | `smtp.sendgrid.net` | SMTP host |
| `EMAIL_HOST_USER` | Prod | — | SMTP username |
| `EMAIL_HOST_PASSWORD` | Prod | — | SMTP password |
| `SECURE_SSL_REDIRECT` | Prod | `True` | Force HTTPS |

Set production settings by exporting:
```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
```

---

## Running Tests

```bash
python manage.py test
```

Each app has a `tests.py` stub. Expand these with unit tests for models and integration tests for API endpoints.

---

## Deployment

### Checklist before going live

- [ ] Set `DJANGO_SETTINGS_MODULE=config.settings.production`
- [ ] Generate a strong `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Restrict `ALLOWED_HOSTS` to your domain
- [ ] Switch database to PostgreSQL
- [ ] Run `python manage.py collectstatic`
- [ ] Configure SMTP for transactional email
- [ ] Set up cloud storage (S3 / Cloudinary) for media files
- [ ] Integrate real MTN MoMo / Orange Money SDK in `payments/views.py`
- [ ] Put gunicorn behind nginx or a PaaS (Railway, Render, etc.)

### Running with Gunicorn

```bash
DJANGO_SETTINGS_MODULE=config.settings.production \
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```
