# GrabIT Backend

REST API for the **GrabIT** marketplace platform — a multi-role e-commerce system for Cameroon with escrow-secured payments, vendor shops, delivery agents, and an admin console.

Built with **Django 4.2** + **Django REST Framework**, deployed on **Railway**, backed by **Railway-hosted PostgreSQL** and **Cloudflare R2** for file storage.

> **New to the project?** Read the [Infrastructure & Technology Reference](#infrastructure--technology-reference) section before touching any code or configuration.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Infrastructure & Technology Reference](#infrastructure--technology-reference)
   - [System Overview](#system-overview)
   - [Three-Layer Architecture](#three-layer-architecture)
   - [Layer 1 — Django on Railway](#layer-1--django-on-railway)
   - [Layer 2 — PostgreSQL on Railway](#layer-2--postgresql-on-railway)
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
| Auth — JWT | djangorestframework-simplejwt — access token in body, refresh in HttpOnly cookie |
| Auth — Google OAuth | django-allauth + google-auth |
| Admin 2FA | django-two-factor-auth + django-axes (brute-force protection) |
| Password hashing | argon2-cffi |
| Rate limiting | django-ratelimit |
| Filtering | django-filter |
| API Docs | drf-spectacular (OpenAPI 3 / Swagger) |
| Images | Pillow |
| File storage | django-storages + boto3 (S3-compatible; Cloudflare R2 in production) |
| Payment gateway | Fapshi (direct-pay collection; sandbox + live) |
| Task queue | Celery 5 + Redis |
| HTTP client | requests (Fapshi API calls) |
| Config | python-decouple |
| Database driver | psycopg2-binary |
| Dev database | SQLite |
| Production database | PostgreSQL (Railway plugin) |
| Production server | Gunicorn |
| Static files | Whitenoise |
| Backend hosting | Railway |
| Frontend hosting | Cloudflare Pages |
| Payment proxy | Cloudflare Worker (proxies Railway → Fapshi) |

---

## Infrastructure & Technology Reference

> **Audience:** New backend developers, frontend developers integrating with the API, QA testers, and project managers who need to understand the system. Last updated June 2026.

### System Overview

GrabIT is a Cameroonian escrow-secured marketplace. When a buyer pays for a product, the money is held in escrow until the buyer confirms they have received their order. Only then is the vendor and delivery agent paid. This escrow model is the core business logic of the platform.

The backend is responsible for all user authentication, all business logic (orders, payments, escrow, disputes), serving data to the frontend via a REST API, and enforcing who can see or change what.

The system is split into three separate services that work together:

```
┌─────────────────────┐        ┌──────────────────────┐        ┌────────────────────┐
│                     │        │                       │        │                    │
│   FRONTEND          │  HTTP  │   DJANGO API          │  SQL   │   POSTGRESQL DB    │
│   React App         │◄──────►│   Railway             │◄──────►│   Railway Postgres │
│   Cloudflare Pages  │        │   (Python server)     │        │   (plugin)         │
│                     │        │                       │        │                    │
└─────────────────────┘        └──────────────────────┘        └────────────────────┘
     grabit.sale                web-production-fcb36                 DATABASE_URL
                                   .up.railway.app               (set in Railway vars)
                                          │
                                          │ X-Proxy-Secret
                                          ▼
                               ┌──────────────────────┐        ┌────────────────────┐
                               │                      │        │                    │
                               │  CLOUDFLARE WORKER   │◄──────►│   FAPSHI API       │
                               │  (payment proxy)     │        │   live.fapshi.com  │
                               │                      │        │                    │
                               └──────────────────────┘        └────────────────────┘
                               helloworld.ndifonlemuel            apiuser + apikey
                                 .workers.dev                    stored in the Worker
```

**In plain English:** The frontend is the visual interface users see. Django is the brain — it receives requests, applies business rules, and returns data. Railway hosts the Django application and PostgreSQL database. For payments, Django calls a Cloudflare Worker instead of Fapshi directly; the Worker holds the Fapshi API credentials and forwards requests, working around Railway's outbound connectivity constraints with Fapshi.

### Three-Layer Architecture

Each service has a different job and different scaling needs:

| Service | Job | Hosted On | Technology |
|---|---|---|---|
| **Frontend** | What users see and interact with | Cloudflare Pages | React + TypeScript |
| **API Server** | Business logic, authentication, data processing | Railway | Django (Python) |
| **Database** | Permanent data storage | Railway (PostgreSQL plugin) | PostgreSQL |
| **File Storage** | Product images and KYC documents | Cloudflare R2 | S3-compatible object storage |

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

### Layer 2 — PostgreSQL on Railway

**PostgreSQL** (often called "Postgres") is the world's most advanced open-source relational database. A relational database stores data in tables with rows and columns, and tables can be linked through relationships. GrabIT requires PostgreSQL for:

- **ACID compliance** — every financial transaction is guaranteed to complete fully or not at all. No partial writes that could corrupt escrow balances.
- **Relational data model** — orders link to buyers, vendors, agents, and payments in a web of relationships.

**Railway's PostgreSQL plugin** provisions a managed PostgreSQL database alongside the Django service inside the same Railway project. Railway automatically injects a `DATABASE_URL` environment variable that Django reads via `dj-database-url`. This keeps all infrastructure — web server, task worker, and database — in a single project with shared networking and one billing dashboard.

**`conn_max_age=600`** is set in production so Django reuses database connections for up to 10 minutes instead of opening a new one per request, reducing connection overhead under load.

**File storage** uses **Cloudflare R2** (S3-compatible object storage). Product images and KYC documents are uploaded directly to R2 via `django-storages` + `boto3`. Files are served from a custom domain (`R2_PUBLIC_URL`). R2 is configured with `AWS_QUERYSTRING_AUTH=False` so URLs are permanent public links, not time-limited presigned URLs.

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
| `psycopg2-binary >=2.9` | Python adapter for PostgreSQL. The driver that allows Django to talk to the Railway PostgreSQL database. The `-binary` variant includes pre-compiled C extensions so no compilation is needed during deployment. |
| `dj-database-url >=2.0,<3.0` | Parses a `postgresql://user:pass@host:port/db` URI into the dictionary format Django's `DATABASES` setting requires. Railway injects `DATABASE_URL` automatically; this package converts it. |

#### Authentication & Security

| Package | What it does |
|---|---|
| `djangorestframework-simplejwt` | Issues and validates JWT access tokens (10 min) and refresh tokens (7 days). Access token in response body; refresh token in `HttpOnly` cookie. |
| `django-allauth` | Handles Google OAuth flow. Validates the Google ID token, creates or looks up the user account, and integrates with DRF's JWT flow. |
| `google-auth` | Verifies Google ID tokens against Google's public keys with audience validation. Used inside the custom Google OAuth view. |
| `django-axes` | Brute-force protection for the admin login. Locks out an IP+username pair after 5 failed attempts for 1 hour. |
| `django-two-factor-auth` | Enforces TOTP-based two-factor authentication for all Django admin logins. |
| `argon2-cffi` | Provides the Argon2 password hasher — more resistant to GPU cracking than Django's default PBKDF2. Existing PBKDF2 hashes are upgraded transparently on next login. |
| `django-ratelimit` | Per-view rate limiting to protect public endpoints from abuse. |
| `cryptography` | Cryptographic primitives required by allauth's Google OIDC support. |

#### Payments

| Package | What it does |
|---|---|
| `requests` | HTTP client used to call the Fapshi API (initiate payment, verify payment status). |
| `celery` | Distributed task queue. Runs `reconcile_pending_payments` every 5 minutes to self-heal any payments stuck in `processing` state if a webhook was missed. |
| `redis` | Python client for Redis. Used as both the Celery broker (task queue) and result backend. Railway provides Redis as an add-on plugin. |

#### File Storage

| Package | What it does |
|---|---|
| `django-storages` | Pluggable storage backend for Django. In production, it routes all file saves to Cloudflare R2 via the S3-compatible API. |
| `boto3` | AWS SDK for Python. `django-storages` uses it under the hood to communicate with R2's S3-compatible endpoint. |

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

**`production.py`** imports from `base.py` then overrides: `DEBUG=False`, PostgreSQL via `DATABASE_URL` (injected by Railway), `CORS_ALLOWED_ORIGINS` restricted to specific frontend domains, Cloudflare R2 for file storage, Whitenoise for static files, and security headers (`SECURE_BROWSER_XSS_FILTER`, `SECURE_HSTS_SECONDS`, `X_FRAME_OPTIONS`, etc.).

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

**`payments`** integrates with **Fapshi** for direct-pay collection (buyer pays via MTN MoMo or Orange Money). All Fapshi API calls are routed through a **Cloudflare Worker proxy** (`FAPSHI_BASE_URL` points to the Worker; `FAPSHI_PROXY_SECRET` authenticates Railway to the Worker; the Worker holds the actual Fapshi credentials). The webhook endpoint at `/api/v1/payments/webhook/fapshi/` verifies each payment against `GET /payment-status/:transId` before transitioning an order to `paid_escrow`. A Celery task (`reconcile_pending_payments`, runs every 5 minutes) self-heals stuck `processing` payments. Vendor/agent payouts are a separate future phase.

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
   Authorization: Bearer <access-jwt>...

2. Railway — terminates SSL, forwards plain HTTP to Gunicorn on port 8000

3. Gunicorn — one worker process picks up the request, passes it to Django WSGI

4. Django Middleware (in order):
   CorsMiddleware          → checks if origin is in CORS_ALLOWED_ORIGINS
   SecurityMiddleware      → adds security response headers
   AxesMiddleware          → checks if IP/username is locked out
   AuthenticationMiddleware → loads request.user from session

5. URL Router — /api/v1/orders/ → OrderViewSet

6. DRF Authentication — validates JWT signature + expiry (no DB query for access tokens) → attaches user to request.user

7. DRF Permission Check — is user authenticated? Role match? → granted

8. OrderViewSet.list() — runs Order.objects.filter(buyer=request.user)

9. Django ORM → psycopg2 sends SQL to Railway PostgreSQL:
   SELECT * FROM orders_order WHERE buyer_id = 42

10. Railway PostgreSQL returns rows → ORM converts to Python Order objects

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

For local development you do not need `DATABASE_URL` — SQLite is used by default.

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
│   │   └── production.py    # Prod overrides (Railway PostgreSQL, R2, Whitenoise)
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

The API uses **JWT authentication** via `djangorestframework-simplejwt`. For a full breakdown see [Authentication System Deep Dive](#authentication-system-deep-dive).

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

Response — access token in body, refresh token set as `HttpOnly` cookie:
```json
{
  "access": "<access-jwt>",
  "user": { "id": 1, "email": "user@example.com", "role": "buyer" }
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

### Using the access token

Include this header on every authenticated request:

```http
Authorization: Bearer <access-jwt>
```

> **Frontend note:** The header prefix is `Bearer`, not `Token`.

### Refreshing the token

```http
POST /api/v1/auth/token/refresh/
```

No body needed — the browser sends the `grabit_refresh` HttpOnly cookie automatically. Returns a new `{ "access": "..." }`.

### Logout

```http
POST /api/v1/auth/logout/
Authorization: Bearer <access-jwt>
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
| POST | `initiate/` | Initiate Fapshi MoMo / Orange payment | Required |
| GET | `payouts/` | Vendor / agent payout history | Required |
| POST | `webhook/fapshi/` | Fapshi payment webhook (called by Fapshi, not the frontend) | `x-wh-secret` header |

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
Authorization: Bearer <access-jwt>
```

The access token is returned in the body by both `/auth/register/` and `/auth/login/`. The refresh token is set as an `HttpOnly` cookie named `grabit_refresh`.

---

### Public — no auth required

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/auth/register/` | Body: `email`, `password`, `first_name`, `last_name`, `role`, `phone`, `city`. Returns `{access, user}`; refresh token set as `HttpOnly` cookie |
| POST | `/auth/login/` | Body: `email`, `password`. Returns `{access, user}`; refresh token set as `HttpOnly` cookie |
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
| POST | `/auth/logout/` | Blacklists refresh token and clears the cookie |
| POST | `/auth/token/refresh/` | Returns new access token using the `grabit_refresh` cookie |
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
| POST | `/payments/initiate/` | Trigger Fapshi payment. Body: `order_id`, `method` (`mtn_momo` / `orange_money`), `phone_number` (required, 9-digit Cameroonian number e.g. `670000000`) |
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
Authorization: Bearer <access-jwt>

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
| `SECRET_KEY` | Always | Long random string used to sign cookies, CSRF tokens, and password reset links. Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | Always | `True` locally, must be `False` on Railway. |
| `ALLOWED_HOSTS` | Always | Comma-separated hostnames Django will respond to (e.g. `localhost,127.0.0.1,web-production-fcb36.up.railway.app`). |
| `DJANGO_SETTINGS_MODULE` | Production | Set to `config.settings.production` on Railway. Defaults to `development` locally. |
| `ADMIN_URL_PATH` | Optional | Custom path for the Django admin panel (default: `internal-mgmt`). Obfuscates the admin URL from bots. |

### CORS

| Variable | Required | Description |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` | Production | Comma-separated frontend origins (hardcoded in `production.py` to `https://grabit.sale` and `https://grab-it.ndifonlemuel.workers.dev`). Update this file to add new domains. |

### Database (Railway PostgreSQL)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Production | Full PostgreSQL connection string. Railway injects this automatically when you add the PostgreSQL plugin to your project. Format: `postgresql://user:pass@host:port/db`. |

### Cloudflare R2 (media storage)

| Variable | Required | Description |
|---|---|---|
| `R2_BUCKET_NAME` | Production | R2 bucket name (e.g. `grabit-media`) |
| `R2_ENDPOINT_URL` | Production | `https://<account-id>.r2.cloudflarestorage.com` |
| `R2_ACCESS_KEY_ID` | Production | R2 API token Access Key ID |
| `R2_SECRET_ACCESS_KEY` | Production | R2 API token Secret Access Key |
| `R2_PUBLIC_URL` | Production | Public base URL for uploaded files (e.g. `https://media.grabit.sale`) |

### Google OAuth

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_OAUTH2_CLIENT_ID` | Optional | OAuth 2.0 client ID from Google Cloud Console. Required for Google login to work. |
| `GOOGLE_OAUTH2_CLIENT_SECRET` | Optional | OAuth 2.0 client secret. |

### Fapshi (payment gateway)

All Fapshi API calls go through a Cloudflare Worker proxy. There are two operating modes depending on which env vars are set:

**Proxy mode (production)** — `FAPSHI_PROXY_SECRET` is set; `FAPSHI_BASE_URL` points to the Worker. Railway authenticates to the Worker with `X-Proxy-Secret`; the Worker holds the actual Fapshi credentials and forwards the call.

**Direct mode (local dev / sandbox)** — `FAPSHI_PROXY_SECRET` is absent; `FAPSHI_BASE_URL` points directly to Fapshi; `FAPSHI_API_USER` + `FAPSHI_API_KEY` are used.

| Variable | Required | Description |
|---|---|---|
| `FAPSHI_BASE_URL` | Always | Proxy mode: Cloudflare Worker URL. Direct mode: `https://sandbox.fapshi.com` locally or `https://live.fapshi.com` for production without proxy. |
| `FAPSHI_PROXY_SECRET` | Proxy mode | Shared secret that Railway sends as `X-Proxy-Secret` to the Cloudflare Worker. Must match the secret configured in the Worker. When set, `FAPSHI_API_USER`/`FAPSHI_API_KEY` are not needed on Railway (they live in the Worker). |
| `FAPSHI_API_USER` | Direct mode | "API User" from your Fapshi collection service credentials tab. Not needed when `FAPSHI_PROXY_SECRET` is set. |
| `FAPSHI_API_KEY` | Direct mode | "API Key" from your Fapshi collection service credentials tab. Not needed when `FAPSHI_PROXY_SECRET` is set. |
| `FAPSHI_WEBHOOK_SECRET` | Production | Shared secret between Fapshi and your server. Set the same value in the Fapshi dashboard → Webhook → Secret field. Max 50 chars. |

### Redis (Celery)

| Variable | Required | Description |
|---|---|---|
| `REDIS_URL` | Production | Redis connection string. Railway provides this automatically when you add the Redis plugin. Used as Celery broker and result backend. |

### Email (production SMTP)

| Variable | Default | Description |
|---|---|---|
| `EMAIL_HOST` | `smtp.sendgrid.net` | SMTP server hostname |
| `EMAIL_PORT` | `587` | SMTP port |
| `EMAIL_HOST_USER` | — | SMTP username / API key identifier |
| `EMAIL_HOST_PASSWORD` | — | SMTP password or API key |
| `DEFAULT_FROM_EMAIL` | `noreply@grabit.cm` | Sender address for all outgoing email |

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

### Cloudflare Worker (payment proxy)

The Worker lives at `https://helloworld.ndifonlemuel.workers.dev` and is managed separately from the Django codebase. It is **not** deployed via Railway or Git — it is deployed directly through the Cloudflare Workers dashboard.

**Why it exists:** Railway uses dynamic outbound IPs that Fapshi rejects. The Worker runs on Cloudflare's edge network and proxies all Fapshi API calls from Django, keeping the real Fapshi credentials off Railway entirely.

**How it works:**

```
Django (Railway)
  │  POST /direct-pay
  │  X-Proxy-Secret: <FAPSHI_PROXY_SECRET>
  ▼
Cloudflare Worker
  │  validates X-Proxy-Secret == env.PROXY_SECRET
  │  injects env.FAPSHI_API_USER + env.FAPSHI_API_KEY
  │  forwards to https://live.fapshi.com/direct-pay
  ▼
Fapshi Live API
```

**Worker source code:**

```javascript
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Diagnostic: GET /ip-check → returns Cloudflare's outbound IP
    if (request.method === "GET" && url.pathname === "/ip-check") {
      const ip = await fetch("https://api.ipify.org?format=json").then(r => r.json());
      return new Response(JSON.stringify(ip), {
        headers: { "Content-Type": "application/json" },
      });
    }

    // All other routes require the shared secret from Django
    if (request.headers.get("X-Proxy-Secret") !== env.PROXY_SECRET) {
      return new Response(JSON.stringify({ message: "Forbidden" }), {
        status: 403,
        headers: { "Content-Type": "application/json" },
      });
    }

    const base = env.FAPSHI_BASE ?? "https://live.fapshi.com";
    const target = base + url.pathname + url.search;

    const headers = new Headers({
      "Content-Type": "application/json",
      "apiuser": env.FAPSHI_API_USER,
      "apikey": env.FAPSHI_API_KEY,
    });

    const init = { method: request.method, headers };
    if (!["GET", "HEAD"].includes(request.method)) {
      init.body = await request.arrayBuffer();
    }

    const resp = await fetch(target, init);
    const body = await resp.text();
    return new Response(body, {
      status: resp.status,
      headers: { "Content-Type": "application/json" },
    });
  },
};
```

**Worker secrets** (set in Cloudflare dashboard → Workers & Pages → helloworld → Settings → Variables and Secrets):

| Name | Type | Value |
|---|---|---|
| `FAPSHI_BASE` | Plain text | `https://live.fapshi.com` |
| `FAPSHI_API_USER` | Secret | Live API User from Fapshi dashboard |
| `FAPSHI_API_KEY` | Secret | Live API Key from Fapshi dashboard |
| `PROXY_SECRET` | Secret | Must match `FAPSHI_PROXY_SECRET` in Railway |

**To update the Worker:** Cloudflare Workers dashboard → helloworld → Edit code → paste updated source → Deploy.

**Logs:** Workers dashboard → helloworld → Logs → Begin log stream, then trigger a request. Useful for debugging Fapshi errors without touching Railway.

---

### Deployment checklist

Before every production deployment, confirm:

- [ ] `DJANGO_SETTINGS_MODULE=config.settings.production` is set in Railway variables
- [ ] `DEBUG=False` is set in Railway variables
- [ ] `SECRET_KEY` is a strong, unique key (not the development placeholder)
- [ ] `ALLOWED_HOSTS` includes the Railway domain
- [ ] Railway **PostgreSQL plugin** is attached — `DATABASE_URL` injected automatically
- [ ] Railway **Redis plugin** is attached — `REDIS_URL` injected automatically
- [ ] `R2_BUCKET_NAME`, `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_PUBLIC_URL` set in Railway variables
- [ ] `FAPSHI_BASE_URL` set to the Cloudflare Worker URL (proxy mode) or `https://live.fapshi.com` (direct mode)
- [ ] `FAPSHI_PROXY_SECRET` set in Railway **and** matching the secret in the Cloudflare Worker (proxy mode)
- [ ] `FAPSHI_WEBHOOK_SECRET` set in Railway variables; same value pasted into Fapshi dashboard → Webhook → Secret
- [ ] Fapshi dashboard webhook URL set to `https://<your-railway-domain>/api/v1/payments/webhook/fapshi/`
- [ ] Celery worker service running: `celery -A config worker -l info --concurrency=2`
- [ ] Celery beat service running: `celery -A config beat -l info`
- [ ] `GOOGLE_OAUTH2_CLIENT_ID` and `GOOGLE_OAUTH2_CLIENT_SECRET` set (if Google login is active)
- [ ] SMTP variables configured for transactional email

---

## Live URLs

| Resource | URL |
|---|---|
| **Live API** | `https://web-production-fcb36.up.railway.app/api/v1/` |
| **API Documentation (Swagger)** | `https://web-production-fcb36.up.railway.app/api/docs/` |
| **API Documentation (ReDoc)** | `https://web-production-fcb36.up.railway.app/api/redoc/` |
| **Django Admin Panel** | `https://web-production-fcb36.up.railway.app/internal-mgmt/` |
| **Railway Dashboard** | `https://railway.app` |
| **Frontend (Live)** | `https://grabit.sale` |
| **Payment Proxy (Cloudflare Worker)** | `https://helloworld.ndifonlemuel.workers.dev` |

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
| **Railway** | A cloud platform for deploying web applications. GrabIT's backend hosting provider. Also provides the PostgreSQL database and Redis as managed plugins within the same project. |
| **Cloudflare R2** | S3-compatible object storage from Cloudflare. Stores all product images and KYC documents. Served from a custom domain via `R2_PUBLIC_URL`. |
| **Cloudflare Worker** | A serverless function deployed on Cloudflare's edge network. GrabIT uses one as a payment proxy: it accepts requests from Railway (authenticated with `X-Proxy-Secret`), injects the real Fapshi credentials, and forwards the call to Fapshi. This was introduced because Railway has outbound connectivity constraints when calling Fapshi directly. |
| **Fapshi** | A Cameroonian payment gateway for MTN MoMo and Orange Money. GrabIT uses the Fapshi collection API for buyer payments, routed through the Cloudflare Worker proxy. |
| **Celery** | A distributed task queue for Python. Used to run background jobs — currently the `reconcile_pending_payments` task that self-heals stuck payments every 5 minutes. |
| **Gunicorn** | A Python WSGI HTTP server for production. Handles multiple concurrent requests by running multiple worker processes. |
| **Whitenoise** | A Python library that lets Django serve its own static files efficiently in production. |
| **JWT** | JSON Web Token. A self-contained token that encodes user identity and expiry. GrabIT uses short-lived access JWTs (10 min) and long-lived refresh JWTs (7 days). |
| **XAF** | Central African CFA franc. The currency of Cameroon. All monetary values in GrabIT are stored as integers in XAF. |
| **KYC** | Know Your Customer. The process of verifying a user's identity. GrabIT requires vendors and delivery agents to submit identity documents before being approved. |
| **`manage.py`** | Django's command-line utility. Used for running migrations, starting the dev server, creating users, and running management commands. |
| **`requirements.txt`** | A text file listing all Python packages the project depends on. `pip install -r requirements.txt` installs all of them. |

---

*GrabIT · grabit.sale · Internal Team Documentation · June 2026*
