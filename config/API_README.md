# 📦 Backend API Reference — Frontend Developer Guide

> Base URL: `http://localhost:8000/api/` (update to your deployed URL)  
> Auth: Token-based — include `Authorization: Token <your_token>` in every protected request header.

---

## 🔐 Authentication

### Register
`POST /auth/register/`

**Body:**
```json
{
  "email": "john@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe",
  "role": "buyer",
  "phone": "6XXXXXXXX",
  "city": "Douala"
}
```

**Response `201`:**
```json
{
  "token": "abc123...",
  "user": { "id": 1, "email": "john@example.com", "first_name": "John", "last_name": "Doe", "role": "buyer" }
}
```

---

### Login
`POST /auth/login/`

**Body:**
```json
{ "email": "john@example.com", "password": "securepassword" }
```

**Response `200`:**
```json
{
  "token": "abc123...",
  "user": { "id": 1, "email": "john@example.com", "role": "buyer" }
}
```

> 💡 Save the token to localStorage/AsyncStorage and attach it to every subsequent request.

---

### Logout
`POST /auth/logout/` 🔒

No body needed. Invalidates the current token.

**Response `204`:** *(no content)*

---

### Get / Update Current User
`GET /auth/me/` 🔒  
`PATCH /auth/me/` 🔒

**PATCH Body (any fields, multipart/form-data for avatar):**
```json
{ "first_name": "John", "last_name": "Doe", "phone": "6XXXXXXXX", "city": "Douala" }
```

---

### Addresses
`GET /auth/me/addresses/` 🔒 — list addresses  
`POST /auth/me/addresses/` 🔒 — add address  
`GET /auth/me/addresses/<id>/` 🔒  
`PATCH /auth/me/addresses/<id>/` 🔒  
`DELETE /auth/me/addresses/<id>/` 🔒

**POST Body:**
```json
{
  "label": "Home",
  "line": "123 Main St",
  "city": "Buea",
  "is_primary": true
}
```

---

### Agent KYC Documents
`GET /auth/me/agent-kyc/` 🔒 — list agent KYC documents (agents only)  
`POST /auth/me/agent-kyc/` 🔒 — upload a KYC document (multipart/form-data)  
`GET /auth/me/agent-kyc/<id>/` 🔒  
`PATCH /auth/me/agent-kyc/<id>/` 🔒  
`DELETE /auth/me/agent-kyc/<id>/` 🔒

**POST Body:** `multipart/form-data` — fields: `doc_type` (`identity` / `driving_license` / `vehicle` / `address`), `label`, `file`

---

## 🏪 Shops

### List All Active Shops
`GET /shops/` — public

**Query params:** `?city=Buea` `?category=electronics`

---

### Shop Detail
`GET /shops/<handle>/` — public

---

### Shop Products
`GET /shops/<handle>/products/` — public

---

### Follow / Unfollow a Shop
`POST /shops/<handle>/follow/` 🔒

Toggles follow state. First call follows, second call unfollows.

**Response:**
```json
{ "following": true }
```

---

### My Shop (Vendor)
`GET /shops/my/` 🔒  
`PUT /shops/my/` 🔒  
`PATCH /shops/my/` 🔒 — supports `multipart/form-data` for `logo` and `banner` uploads

---

### Create My Shop (Vendor)
`POST /shops/my/create/` 🔒

---

### KYC Documents (Vendor Shop)
`GET /shops/my/kyc/` 🔒  
`POST /shops/my/kyc/` 🔒

**POST Body:** `multipart/form-data` — fields: `doc_type` (`identity` / `address` / `business`), `label`, `file`

---

### Shops I Follow
`GET /shops/followed/` 🔒

---

## 🛍️ Products

### List Products (Public)
`GET /products/` — public

**Query params:**
| Param | Example | Description |
|-------|---------|-------------|
| `search` | `?search=shoes` | Search name/description/category |
| `category` | `?category=fashion` | Filter by category |
| `city` | `?city=Buea` | Filter by shop city |
| `condition` | `?condition=new` | `new` or `used` |
| `min_price` | `?min_price=500` | Minimum price |
| `max_price` | `?max_price=5000` | Maximum price |
| `ordering` | `?ordering=price` | Sort: `price`, `-price`, `rating`, `created_at` |

---

### Product Detail
`GET /products/<id>/` — public

> ℹ️ Each call to this endpoint increments the product's view count.

---

### Vendor: My Products
`GET /products/vendor/` 🔒  
`POST /products/vendor/` 🔒

**POST Body:**
```json
{
  "name": "Air Jordan 1",
  "description": "Limited edition",
  "price": 45000,
  "category": "fashion",
  "condition": "new",
  "stock": 10
}
```

---

### Vendor: Edit / Delete Product
`GET /products/vendor/<id>/` 🔒  
`PATCH /products/vendor/<id>/` 🔒  
`DELETE /products/vendor/<id>/` 🔒

---

### Product Reviews
`GET /products/<id>/reviews/` — public  
`POST /products/<id>/reviews/` 🔒

**POST Body:**
```json
{ "rating": 4, "comment": "Great product!" }
```

---

### Wishlist
`GET /products/wishlist/` 🔒 — list wishlist items  
`POST /products/wishlist/` 🔒 — add to wishlist  
`DELETE /products/wishlist/<id>/` 🔒 — remove from wishlist

**POST Body:**
```json
{ "product": 42 }
```

---

## 📦 Orders

### List My Orders / Create Order
`GET /orders/` 🔒  
`POST /orders/` 🔒

> The response list is automatically filtered by role — vendors see their shop's orders, agents see assigned orders, buyers see their own.

**POST Body (buyer creates order):**
```json
{
  "product": 42,
  "quantity": 2,
  "delivery_address": 1
}
```

**Response `201`:** Full order object (see Order Status section below).

---

### Order Detail
`GET /orders/<order_id>/` 🔒

---

### Update Order Status
`PATCH /orders/<order_id>/status/` 🔒

Only certain roles can make certain transitions:

| Role | From | To |
|------|------|----|
| Vendor | `paid_escrow` | `preparing` |
| Vendor | `preparing` | `picked_up` |
| Agent | `picked_up` | `in_transit` |
| Agent | `in_transit` | `delivered_confirm` |
| Buyer | `delivered_confirm` | `completed` |

**Body:**
```json
{ "status": "preparing" }
```

---

### Buyer: Confirm Delivery
`POST /orders/<order_id>/confirm/` 🔒

Buyer confirms delivery → marks order `completed` and releases escrow to vendor.

**Response:**
```json
{ "detail": "Order confirmed. Escrow released to vendor." }
```

---

### Vendor: Cancel Order
`POST /orders/<order_id>/cancel/` 🔒

Vendor cancels an order before it has been picked up. Allowed from: `awaiting_payment`, `paid_escrow`, `preparing`, `agent_assigned`.

---

### Agent: Decline Assignment
`POST /orders/<order_id>/decline/` 🔒

Agent declines an `agent_assigned` order — order returns to `preparing` for reassignment.

---

### Order Status Flow

```
[created] → paid_escrow → preparing → agent_assigned → picked_up → in_transit → delivered_confirm → completed
                                    ↘ cancelled
                                                                                         ↘ disputed → refunded
                                                                                                    → partially_resolved
                                                                                                    → completed (release_vendor)
```

---

## 💬 Messages

### List & Send Messages
`GET /messages/` 🔒 — shows all messages sent to or by you  
`POST /messages/` 🔒

**POST Body:**
```json
{
  "recipient": 5,
  "content": "Hey, is this item still available?"
}
```

---

## 💳 Payments

### Initiate Payment
`POST /payments/initiate/` 🔒

**Body:**
```json
{
  "order_id": "ORD-abc123",
  "method": "momo",          // "momo" | "orange_money"
  "phone_number": "6XXXXXXXX"
}
```

**Response `201`:** Payment object with status `paid` (currently simulated — real MoMo/Orange Money SDK coming soon).

---

### My Payouts (Vendor / Agent)
`GET /payments/payouts/` 🔒

---

## 🔔 Notifications

### List Notifications
`GET /notifications/` 🔒

---

### Mark All as Read
`POST /notifications/read-all/` 🔒

**Response:**
```json
{ "detail": "All notifications marked as read." }
```

---

### Single Notification
`GET /notifications/<id>/` 🔒  
`PATCH /notifications/<id>/` 🔒 — e.g. mark one as read

---

## 📁 Disputes

### File a Dispute / List Disputes
`GET /disputes/` 🔒  
`POST /disputes/` 🔒

**POST Body:**
```json
{ "order": 1, "reason": "not_delivered", "description": "Package never arrived." }
```

---

### Dispute Detail
`GET /disputes/<dispute_id>/` 🔒

---

### Upload Evidence
`POST /disputes/<dispute_id>/evidence/` 🔒

Upload or replace evidence after a dispute has been filed. Body: `multipart/form-data` with `evidence` file field.

---

### Resolve Dispute (Admin)
`PATCH /disputes/<dispute_id>/resolve/` 🔒

**Body:**
```json
{ "resolution": "refund_buyer", "admin_note": "Item clearly not delivered." }
```

`resolution` options: `refund_buyer` (order → `refunded`) | `release_vendor` (order → `completed`) | `partial_refund` (order → `partially_resolved`)

---

## 🚴 Agent Endpoints

### Agent's Assigned Deliveries
`GET /orders/agent/assignments/` 🔒

**Query param:** `?status=in_transit` — filter by status

---

### Agent Stats
`GET /orders/agent/stats/` 🔒

**Response:**
```json
{
  "today_deliveries": 3,
  "week_deliveries": 12,
  "week_earnings": 15000,
  "active_assignments": 2
}
```

---

## 🔑 Auth Header Cheatsheet

```js
// Axios
axios.defaults.headers.common['Authorization'] = `Token ${token}`;

// Fetch
fetch(url, {
  headers: {
    'Authorization': `Token ${token}`,
    'Content-Type': 'application/json',
  }
});
```

---

## 🛡️ Admin Endpoints
All require `Authorization: Token <admin_token>`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/admin/stats/` | Platform KPIs |
| GET | `/auth/admin/users/` | All users (`?role=`, `?q=`) |
| PATCH | `/auth/admin/users/<id>/` | Toggle `is_active`, `role`, `is_kyc_verified` |
| GET | `/auth/admin/gmv/` | Daily GMV + top vendors |
| GET | `/auth/admin/shops/` | All shops (`?q=`) |
| GET | `/auth/admin/verification/` | Vendor KYC queue |
| PATCH | `/auth/admin/verification/<shop_id>/` | Approve/reject vendor shop |
| GET | `/auth/admin/agent-verification/` | Agent KYC queue |
| PATCH | `/auth/admin/agent-verification/<user_id>/` | Approve/reject agent KYC |
| GET | `/auth/admin/disputes/` | All disputes (`?status=`) |
| GET | `/auth/admin/payouts/` | All payouts |
| GET | `/auth/admin/commissions/` | Monthly commission report |
| GET | `/auth/admin/health/` | System health checks |
| GET | `/auth/admin/fraud/` | Fraud signals (users with 3+ failed payments) |

---

## ⚠️ Common Error Responses

| Status | Meaning |
|--------|---------|
| `400` | Bad request / validation error — check the response body for field errors |
| `401` | Unauthorized — missing or invalid token |
| `403` | Forbidden — you don't have permission for this action |
| `404` | Not found |

**Validation error shape:**
```json
{
  "field_name": ["This field is required."],
  "non_field_errors": ["Some general error."]
}
```

---

> 🔒 = Requires `Authorization: Token <token>` header  
> All request bodies use `Content-Type: application/json` unless noted otherwise (KYC uses `multipart/form-data`)
