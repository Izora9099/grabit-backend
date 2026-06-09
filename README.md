# GrabIT Backend

REST API for the **GrabIT** marketplace platform — a multi-role e-commerce system for Cameroon with escrow-secured payments, vendor shops, delivery agents, and an admin console.

Built with **Django 4.2** + **Django REST Framework**, deployed on **Railway**, backed by **PostgreSQL on Supabase**.

> **New to the project?** Read the [Infrastructure & Technology Reference](#infrastructure--technology-reference) section before touching any code or configuration.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Infrastructure & Technology Reference](#infrastructure--technology-reference)
   - [System Overview](#system-overview)
   - [Three-Layer Architecture](#three-layer-architecture)
   - [Layer 1 — Django on Railway](#layer-1--django-on-railway)
   - [Layer 2 — PostgreSQL on Supabase](#layer-2--postgresql-on-supabase)
   - [Layer 3 — Frontend on Cloudflare Pages](#layer-3--frontend-on-cloudflare-pages)
   - [Python Packages Explained](#python-packages-explained)
   - [Settings Architecture](#settings-architecture)
   - [Django Apps — What Each One Does](#django-apps--what-each-one-does)
   - [Authentication System Deep Dive](#authentication-system-deep-dive)
   - [How a Request Travels Through the System](#how-a-request-travels-through-the-system)
3. [Prerequisites](#prerequisites)
4. [Getting Started](#getting-started)
5. [Project Structure](#project-structure)
6. [User Roles](#user-roles)
7. [Authentication](#authentication)
8. [API Reference](#api-reference)
9. [Frontend Endpoint Reference](#frontend-endpoint-reference)
10. [Key Workflows](#key-workflows)
11. [Environment Variables](#environment-variables)
12. [Running Tests](#running-tests)
13. [Deployment](#deployment)
14. [Live URLs](#live-urls)
15. [Glossary](#glossary)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.2 (LTS) |
| API | Django REST Framework 3.15 |
| Auth | JWT (djangorestframework-simplejwt) — access token in body, refresh in HttpOnly cookie |
| Filtering | django-filter |
| API Docs | drf-spectacular (OpenAPI 3 / Swagger) |
| Images | Pillow |
| Config | python-decouple |
| Database driver | psycopg2-binary |
| Dev database | SQLite |
| Production database | PostgreSQL (Supabase) |
| Production server | Gunicorn |
| Static files | Whitenoise |
| Backend hosting | Railway |
| Frontend hosting | Cloudflare Pages |

---

## Infrastructure & Technology Reference

> **Audience:** New backend developers, frontend developers integrating with the API, QA testers, and project managers who need to understand the system. Last updated May 2026.

### System Overview

GrabIT is a Cameroonian escrow-secured marketplace. When a buyer pays for a product, the money is held in escrow until the buyer confirms they have received their order. Only then is the vendor and delivery agent paid. This escrow model is the core business logic of the platform.

The backend is responsible for all user authentication, all business logic (orders, payments, escrow, disputes), serving data to the frontend via a REST API, and enforcing who can see or change what.

The system is split into three separate services that work together:

```
┌─────────────────────┐        ┌──────────────────────┐        ┌────────────────────┐
│                     │        │                       │        │                    │
│   FRONTEND          │  HTTP  │   DJANGO API          │  SQL   │   POSTGRESQL DB    │
│   React App         │◄──────►│   Railway             │◄──────►│   Supabase         │
│   Cloudflare Pages  │        │   (Python server)     │        │   (cloud database) │
│                     │        │                       │        │                    │
└─────────────────────┘        └──────────────────────┘        └────────────────────┘
     grabit.sale                web-production-fcb36              xtshkfyzmsjlojegqyin
                                   .up.railway.app                  .supabase.co
```

**In plain English:** The frontend is the visual interface users see. Django is the brain — it receives requests, applies business rules, and returns data. Supabase hosts the actual database where all data is stored permanently.

### Three-Layer Architecture

Each service has a different job and different scaling needs:

| Service | Job | Hosted On | Technology |
|---|---|---|---|
| **Frontend** | What users see and interact with | Cloudflare Pages | React + TypeScript |
| **API Server** | Business logic, authentication, data processing | Railway | Django (Python) |
| **Database** | Permanent data storage | Supabase | PostgreSQL |

Separating them means you can update, scale, or replace any one layer without touching the others.

### Layer 1 — Django on Railway

**Django** is a web framework written in Python. A framework is a pre-built toolkit that handles common, repetitive parts of building a web server — URL routing, database connections, user sessions, and input validation — so developers can focus on business logic instead of reinventing the wheel. GrabIT uses Django 4.2, a Long-Term Support (LTS) release.

**Django REST Framework (DRF)** extends Django to serve JSON data instead of HTML pages. Every endpoint at `/api/v1/...` is built with DRF.

**Railway** is a cloud hosting platform. Think of it as a computer in the cloud that runs the Django server 24/7. When you push code to GitHub, Railway automatically detects the change, rebuilds the application, and deploys it. No manual server management required. It also generates a public HTTPS URL instantly with usage-based pricing.

**How Railway starts the server — every deploy runs:**

```bash
python manage.py migrate --noinput && gunicorn config.wsgi --log-file -
```

1. `migrate --noinput` — applies any pending database schema changes
2. `gunicorn config.wsgi` — starts the production web server

**Gunicorn** (Green Unicorn) is a production-grade WSGI server. Django's built-in dev server (`runserver`) can only handle one request at a time and is not safe for production. Gunicorn runs multiple worker processes to handle concurrent requests. WSGI (Web Server Gateway Interface) is the standard protocol that connects Python web applications to the internet.

**Whitenoise** allows Django to serve its own compressed static files efficiently, without needing a separate web server like Nginx. It is added to Django's middleware stack in `production.py`.

**SSL / HTTPS:** Railway terminates HTTPS at the proxy level and forwards plain HTTP internally. Django's `SECURE_SSL_REDIRECT` is set to `False` to prevent an infinite redirect loop. `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` is set so Django still recognises requests as secure and keeps `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` functioning correctly.

### Layer 2 — PostgreSQL on Supabase

**PostgreSQL** (often called "Postgres") is the world's most advanced open-source relational database. A relational database stores data in tables with rows and columns, and tables can be linked through relationships. GrabIT requires PostgreSQL for:

- **ACID compliance** — every financial transaction is guaranteed to complete fully or not at all. No partial writes that could corrupt escrow balances.
- **Relational data model** — orders link to buyers, vendors, agents, and payments in a web of relationships.
- **Row-Level Security (RLS)** — PostgreSQL can restrict which rows a user can see at the database level, not just the application level.

**Supabase** is a cloud platform that hosts PostgreSQL databases and wraps them with useful tools — a visual dashboard, backups, and RLS support. Django connects directly to the PostgreSQL database using standard connection strings, not Supabase's JavaScript client library.

**Two connection modes:**

| Mode | Port | Used For | Variable |
|---|---|---|---|
| Transaction Pooler | 6543 | All live app queries | `SUPABASE_TRANSACTION_URI` |
| Direct connection | 5432 | Database migrations only | `SUPABASE_DIRECT_URI` |

The transaction pooler manages a shared pool of database connections that are reused across requests — more efficient for a live application receiving many requests. The direct connection is required when running `manage.py migrate`, which needs full PostgreSQL feature support that pooled connections do not always provide.

**Row Level Security (RLS)** is currently disabled on all tables during the testing phase. Django is the only service accessing the database and enforces its own access controls through DRF permissions. RLS will be enabled with proper policies before the production launch.

### Layer 3 — Frontend on Cloudflare Pages

The frontend is a separate repository. Key facts for backend developers:

- Hosted on **Cloudflare Pages** at `grabit.sale`
- Communicates with Django via the `VITE_API_URL` environment variable
- All authenticated API requests must include `Authorization: Bearer <access-token>` — note `Bearer`, not `Token`
- The refresh token is delivered as an `HttpOnly` cookie (`grabit_refresh`) — do **not** read or store it in JavaScript
- CORS in Django (`CORS_ALLOWED_ORIGINS`) is configured to allow requests from the frontend's domain

### Python Packages Explained

All packages are listed in `requirements.txt`.

#### Core Framework

| Package | What it does |
|---|---|
| `Django >=4.2,<5.0` | The web framework. Handles URL routing, database ORM, admin panel, authentication, and the request/response cycle. |
| `djangorestframework >=3.15` | Extends Django to build REST APIs. Provides serialisers (data validation + formatting), viewsets, authentication classes, and permission classes. |

#### API Features

| Package | What it does |
|---|---|
| `django-cors-headers >=4.3` | Handles CORS — allows the browser to make requests to the API from a different domain (e.g. `grabit.sale` calling `railway.app`). Without this, browsers block all cross-origin requests. |
| `django-filter >=24.0` | Adds querystring filtering to API endpoints. Powers `GET /products/?category=electronics&city=Yaoundé`. |
| `drf-spectacular >=0.27` | Auto-generates OpenAPI 3.0 documentation from code. Powers the Swagger UI at `/api/docs/` — write the code and the docs are generated automatically. |

#### Database

| Package | What it does |
|---|---|
| `psycopg2-binary >=2.9` | Python adapter for PostgreSQL. The driver that allows Django to talk to Supabase. The `-binary` variant includes pre-compiled C extensions so no compilation is needed during deployment. |
| `dj-database-url >=2.0,<3.0` | Parses a `postgresql://user:pass@host:port/db` URI into the dictionary format Django's `DATABASES` setting requires. Makes it easy to configure the database from a single environment variable. |

#### Configuration & Server

| Package | What it does |
|---|---|
| `python-decouple >=3.8` | Reads configuration values from environment variables or a `.env` file. Every `config("VARIABLE_NAME")` call in the settings files uses this package. |
| `gunicorn >=22.0` | Production WSGI server. Runs multiple worker processes to handle concurrent requests. Railway uses this to serve the Django application. |
| `whitenoise >=6.7` | Serves Django's static files efficiently in production without a separate web server. Compresses files and adds proper HTTP caching headers. |
| `Pillow >=10.0` | Python's image processing library. Used for product photos and KYC document uploads — resizing, format conversion, and validation. |

### Settings Architecture

Settings are split across three files in `config/settings/`:

```
config/settings/
├── base.py          ← Shared settings for ALL environments
├── development.py   ← Overrides for local development
└── production.py    ← Overrides for Railway deployment
```

**`base.py`** contains everything that is the same in every environment: `INSTALLED_APPS`, `MIDDLEWARE`, `AUTH_USER_MODEL` (pointing to `accounts.User`), `REST_FRAMEWORK` configuration, and `SPECTACULAR_SETTINGS`.

**`development.py`** imports from `base.py` then overrides: `DEBUG=True`, SQLite database (no setup required), and `CORS_ALLOW_ALL_ORIGINS=True` (safe locally, dangerous in production).

**`production.py`** imports from `base.py` then overrides: `DEBUG=False`, Supabase PostgreSQL via `SUPABASE_TRANSACTION_URI`, `CORS_ALLOWED_ORIGINS` restricted to specific frontend domains, Whitenoise for static files, and security headers (`SECURE_BROWSER_XSS_FILTER`, `X_FRAME_OPTIONS`, etc.).

### Django Apps — What Each One Does

| App | Responsibility |
|---|---|
| `accounts` | Custom `User` model (with `role`, `phone`, `city`), registration/login, profiles, delivery addresses, admin-only user management and KYC review |
| `products` | Product catalogue, images, reviews (verified purchase only), wishlist |
| `shops` | Vendor shops, KYC documents, shop following, subscription plan, shop creation workflow |
| `orders` | Full order lifecycle, `EscrowEvent` audit trail (every state change logged), in-platform messaging |
| `payments` | MoMo/Orange Money payment records, vendor and agent payout tracking |
| `disputes` | Dispute filing, evidence upload, admin resolution with three outcomes |
| `notifications` | User notification feed, mark-as-read |

**Key business rules:**
- Prices are stored as integers in XAF francs — no decimal sub-unit
- A vendor must have an approved KYC before their shop goes active
- Once an order is paid, funds enter escrow — the vendor cannot be paid until the buyer confirms delivery or an admin resolves a dispute
- `OrderItem` snapshots the price at purchase time, preserving order history if the vendor later changes their price

**`orders` is the most complex app.** It tracks 8 states: `awaiting_payment → paid_escrow → preparing → agent_assigned → picked_up → in_transit → delivered_confirm → completed`. Every transition is logged to the `EscrowEvent` model.

**`payments`** is currently scaffolded. The actual MTN MoMo and Orange Money API integration is the next development phase.

### Authentication System Deep Dive

GrabIT uses **JWT (JSON Web Token) Authentication** via `djangorestframework-simplejwt`.

#### Login / Register flow

`POST /api/v1/auth/login/` and `POST /api/v1/auth/register/` return a **short-lived access token** (10 minutes) in the JSON body:

```json
{
  "access": "<access-jwt>",
  "user": { "id": 1, "email": "user@example.com", "role": "buyer" }
}
```

A **long-lived refresh token** (7 days) is simultaneously set as an `HttpOnly`, `SameSite=Strict` cookie named `grabit_refresh`. **The refresh token is never in the response body** — keeping it in `localStorage` would expose it to XSS attacks.

#### Sending authenticated requests

Include the access token as a Bearer token in every request to a protected endpoint:

```
Authorization: Bearer <access-jwt>
```

> **Frontend note:** The header prefix is `Bearer`, not `Token`.

#### Refreshing the access token

`POST /api/v1/auth/token/refresh/` — no request body needed. The browser automatically sends the `grabit_refresh` cookie. Returns a new access token:

```json
{ "access": "<new-access-jwt>" }
```

Token rotation is enabled: each refresh also issues a new refresh cookie and blacklists the old one.

#### Logout

`POST /api/v1/auth/logout/` — blacklists the refresh token and clears the cookie.

#### Google OAuth

`POST /api/v1/auth/google/` — accepts `{ "id_token": "<google-id-token>" }`. Returns the same JWT pair as regular login, plus `"profile_complete": false` for first-time sign-ins (which triggers the `GoogleCompleteForm`).

`POST /api/v1/auth/google/complete/` — for first-time users, submit `role`, `city`, and `phone` to finish the profile.

**How Django checks the token on each request:**
1. DRF reads the `Authorization: Bearer <jwt>` header
2. Validates the JWT signature and expiry — no database query needed for access tokens
3. Attaches the decoded user to `request.user`
4. The view's permission class checks whether that user has the right role

**Permission levels:**

| Endpoint type | Who can access |
|---|---|
| Public (product list, shop detail) | Anyone — no token required |
| Authenticated (place order, view cart) | Any logged-in user |
| Vendor endpoints | Users with `role = vendor` |
| Agent endpoints | Users with `role = agent` |
| Admin endpoints | Users with `role = admin` |

### How a Request Travels Through the System

Example: a buyer fetching their order list — `GET /api/v1/orders/`

```
1. Browser/App
   GET https://web-production-fcb36.up.railway.app/api/v1/orders/
   Authorization: Token abc123...

2. Railway — terminates SSL, forwards plain HTTP to Gunicorn on port 8000

3. Gunicorn — one worker process picks up the request, passes it to Django WSGI

4. Django Middleware (in order):
   CorsMiddleware          → checks if origin is in CORS_ALLOWED_ORIGINS
   SecurityMiddleware      → adds security response headers
   AuthenticationMiddleware → loads request.user from session

5. URL Router — /api/v1/orders/ → OrderViewSet

6. DRF Authentication — reads token → queries DB → attaches user to request.user

7. DRF Permission Check — is user authenticated? Role match? → granted

8. OrderViewSet.list() — runs Order.objects.filter(buyer=request.user)

9. Django ORM → psycopg2 sends SQL to Supabase (port 6543):
   SELECT * FROM orders_order WHERE buyer_id = 42

10. Supabase returns rows → ORM converts to Python Order objects

11. OrderSerializer — converts objects to dict, validates field types

12. DRF Response — serializes to JSON, sets HTTP 200 OK

13. Gunicorn → Railway → Browser receives the JSON order list
```

---

## Prerequisites

- Python 3.10+
- pip

---

## Getting Started

### 1. Clone the repository

```bash
git clone <repo-url>
cd grabit-backend
```

### 2. Create and activate a virtual environment

A virtual environment isolates this project's Python packages from your system Python. Always use one.

```bash
# Create
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — macOS / Linux
source venv/bin/activate
```

You will know it is active when you see `(venv)` at the start of your terminal prompt.

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
SECRET_KEY=any-random-string-will-do-for-local-dev
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

For local development you do not need the Supabase variables — SQLite is used by default.

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Create a superuser (admin account)

```bash
python manage.py createsuperuser
```

Use role `admin` when prompted (or update it via the Django admin panel afterwards).

### 7. Load test data

```bash
python manage.py seed_data
```

This creates sample users, shops, products, and orders so you have realistic data to work with immediately. After seeding, the following test accounts are available — all use the password `Grabit2024!`:

| Role | Email | What you can test |
|---|---|---|
| Admin | admin@grabit.sale | Full platform access, dispute resolution, KYC approval |
| Vendor | (see seed_data output) | Shop management, product listing, order fulfilment |
| Buyer | (see seed_data output) | Browsing, ordering, dispute filing |
| Agent | (see seed_data output) | Delivery assignment and status updates |

### 8. Start the development server

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

### 9. Connect the frontend

In the GrabIT React app, create `.env.local`:

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
│   │   └── production.py    # Prod overrides (Supabase, Whitenoise)
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

Environment variables are stored outside the codebase — never committed to Git. They live in a `.env` file locally and in Railway's Variables panel in production. See `.env.example` for the full template.

### Django Core

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Always | Long random string used to sign cookies, session tokens, CSRF tokens, and password reset links. Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | Always | `True` locally, must be `False` on Railway. When `True`, Django shows stack traces on error pages. |
| `ALLOWED_HOSTS` | Always | Comma-separated hostnames Django will respond to (e.g. `localhost,127.0.0.1,web-production-fcb36.up.railway.app`). |
| `DJANGO_SETTINGS_MODULE` | Production | Set to `config.settings.production` on Railway. Defaults to `development` locally. |

### CORS

| Variable | Required | Description |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` | Production | Comma-separated frontend origins allowed to make cross-origin requests (e.g. `https://grabit.sale,https://grabit.pages.dev`). |

### Supabase Database

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_TRANSACTION_URI` | Production | Main database connection string (port 6543). Used for all live queries. |
| `SUPABASE_DIRECT_URI` | Production | Session-mode connection string (port 5432). Used only when running `manage.py migrate`. |

### Supabase API

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | Optional | The Supabase project's REST API URL. Not required for database queries — those use the connection strings above. |
| `SUPABASE_ANON_KEY` | Optional | Public "anonymous" JWT key. Safe to expose in frontend code. Grants limited access per RLS policies. |
| `SUPABASE_SERVICE_KEY` | Optional | Secret service role JWT key. Bypasses all RLS. **Never expose in frontend code** — treat like a database root password. |

### Email (production SMTP)

| Variable | Default | Description |
|---|---|---|
| `EMAIL_HOST` | `smtp.sendgrid.net` | SMTP server hostname |
| `EMAIL_PORT` | `587` | SMTP port |
| `EMAIL_HOST_USER` | — | SMTP username / API key identifier |
| `EMAIL_HOST_PASSWORD` | — | SMTP password or API key |
| `DEFAULT_FROM_EMAIL` | `noreply@grabit.sale` | Sender address for all outgoing email |

---

## Running Tests

```bash
python manage.py test
```

Each app has a `tests.py` stub. Expand these with unit tests for models and integration tests for API endpoints.

---

## Deployment

### How code gets to production

```
Developer Machine
      │
      │  git push origin main
      │
      ▼
GitHub Repository
      │
      │  Railway webhook fires automatically
      │
      ▼
Railway Build Process
      │  1. Detects Python project (via requirements.txt)
      │  2. Creates virtual environment
      │  3. pip install -r requirements.txt
      │  4. python manage.py collectstatic --noinput
      │
      ▼
Railway Deploy Process
      │  5. python manage.py migrate --noinput
      │  6. gunicorn config.wsgi --log-file -
      │
      ▼
Live at: https://web-production-fcb36.up.railway.app
```

### Environment variables on Railway

All secrets are stored in Railway's Variables panel, not in the codebase. To add or change a variable:

1. Go to [railway.app](https://railway.app) and open the `grabit-backend` project
2. Click the service → **Variables** tab
3. Add or edit variables
4. Railway will automatically redeploy with the new values

### Deployment checklist

Before every production deployment, confirm:

- [ ] `DJANGO_SETTINGS_MODULE=config.settings.production` is set in Railway variables
- [ ] `DEBUG=False` is set in Railway variables
- [ ] `SECRET_KEY` is a strong, unique key (not the development placeholder)
- [ ] `ALLOWED_HOSTS` includes the Railway domain
- [ ] `CORS_ALLOWED_ORIGINS` includes the correct frontend URL
- [ ] `SUPABASE_TRANSACTION_URI` and `SUPABASE_DIRECT_URI` are valid and use the correct database user
- [ ] Configure SMTP variables for transactional email
- [ ] Integrate real MTN MoMo / Orange Money SDK in `payments/views.py`
- [ ] Set up cloud storage (S3 / Cloudinary) for media files if needed

---

## Live URLs

| Resource | URL |
|---|---|
| **Live API** | `https://web-production-fcb36.up.railway.app/api/v1/` |
| **API Documentation (Swagger)** | `https://web-production-fcb36.up.railway.app/api/docs/` |
| **API Documentation (ReDoc)** | `https://web-production-fcb36.up.railway.app/api/redoc/` |
| **Django Admin Panel** | `https://web-production-fcb36.up.railway.app/admin/` |
| **Supabase Dashboard** | `https://supabase.com/dashboard/project/xtshkfyzmsjlojegqyin` |
| **Railway Dashboard** | `https://railway.app` |
| **Frontend (Live)** | `https://grabit.sale` |

---

## Glossary

| Term | Definition |
|---|---|
| **API** | Application Programming Interface. A set of rules that allows two software systems to communicate. The Django API receives requests from the frontend and returns data. |
| **REST API** | A type of API that uses standard HTTP methods (GET, POST, PATCH, DELETE) and returns JSON. GrabIT's API is REST-based. |
| **JSON** | JavaScript Object Notation. A lightweight data format used to send structured data between the server and frontend. |
| **Endpoint** | A specific URL in the API that performs a specific action. For example, `POST /api/v1/auth/login/` is the login endpoint. |
| **HTTP Method** | The verb of an API request. `GET` fetches data, `POST` creates data, `PATCH` updates data, `DELETE` removes data. |
| **Token** | A random string that proves a user is authenticated. Sent in the `Authorization` header of every protected request. |
| **Middleware** | Code that runs on every request before it reaches the view. Used for CORS, security headers, and authentication. |
| **Migration** | A database schema change (adding a table, column, etc.) stored as a Python file. `manage.py migrate` applies pending migrations to the database. |
| **ORM** | Object Relational Mapper. Django's ORM lets you write Python like `Order.objects.filter(status='pending')` instead of raw SQL. |
| **Serialiser** | A DRF component that converts Python objects to JSON (for responses) and validates incoming JSON (for requests). |
| **CORS** | Cross-Origin Resource Sharing. A browser security mechanism that blocks requests to a different domain unless the server explicitly allows it. |
| **Escrow** | A financial arrangement where funds are held by a neutral third party until conditions are met. In GrabIT, the platform holds the buyer's payment until delivery is confirmed. |
| **WSGI** | Web Server Gateway Interface. The standard interface between Python web apps and web servers like Gunicorn. |
| **Virtual Environment** | An isolated Python installation for a specific project. Prevents package conflicts between different projects on the same machine. |
| **PostgreSQL** | An open-source relational database. The database system GrabIT uses in production. |
| **Supabase** | A cloud platform that hosts PostgreSQL databases with extra tooling (dashboard, auth, storage, realtime). GrabIT's database provider. |
| **Railway** | A cloud platform for deploying web applications. GrabIT's backend hosting provider. |
| **Gunicorn** | A Python WSGI HTTP server for production. Handles multiple concurrent requests by running multiple worker processes. |
| **Whitenoise** | A Python library that lets Django serve its own static files efficiently in production. |
| **RLS** | Row Level Security. A PostgreSQL feature that restricts which database rows a user can see, enforced at the database level. |
| **XAF** | Central African CFA franc. The currency of Cameroon. All monetary values in GrabIT are stored as integers in XAF. |
| **KYC** | Know Your Customer. The process of verifying a user's identity. GrabIT requires vendors and delivery agents to submit identity documents before being approved. |
| **`manage.py`** | Django's command-line utility. Used for running migrations, starting the dev server, creating users, and running management commands. |
| **`requirements.txt`** | A text file listing all Python packages the project depends on. `pip install -r requirements.txt` installs all of them. |

---

*GrabIT · grabit.sale · Internal Team Documentation · May 2026*
