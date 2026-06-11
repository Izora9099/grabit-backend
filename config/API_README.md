# GrabIT Backend API Reference

> **Base URL:** `https://web-production-fcb36.up.railway.app/api/v1`  
> **Auth:** JWT — include `Authorization: Bearer <access_token>` on every protected request.  
> **Refresh token** is stored in an HttpOnly cookie (`grabit_refresh`) — the browser/app sends it automatically on `/auth/token/refresh/`.

---

## Authentication

### Register
`POST /auth/register/`

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
  "access": "<jwt_access_token>",
  "user": { "id": 1, "email": "john@example.com", "first_name": "John", "last_name": "Doe", "role": "buyer", "city": "Douala" }
}
```
Refresh token set as HttpOnly cookie.

---

### Login
`POST /auth/login/`

```json
{ "email": "john@example.com", "password": "securepassword" }
```

**Response `200`:**
```json
{
  "access": "<jwt_access_token>",
  "user": { "id": 1, "email": "john@example.com", "role": "buyer" }
}
```
Refresh token set as HttpOnly cookie.

---

### Refresh Access Token
`POST /auth/token/refresh/`

No body needed. Reads the refresh token from the `grabit_refresh` cookie.

**Response `200`:**
```json
{ "access": "<new_jwt_access_token>" }
```

---

### Logout
`POST /auth/logout/` 🔒

No body. Blacklists the refresh token and clears the cookie.

**Response `204`:** *(no content)*

---

### Google OAuth — Sign In
`POST /auth/google/`

```json
{ "id_token": "<google_id_token>" }
```

**Response `200`:**
```json
{
  "access": "<jwt_access_token>",
  "user": { ... },
  "profile_complete": false
}
```
`profile_complete: false` on first sign-in — show the profile completion form.

---

### Google OAuth — Complete Profile (first-time only)
`POST /auth/google/complete/` 🔒

```json
{ "role": "buyer", "city": "Douala", "phone": "6XXXXXXXX" }
```

**Response `200`:** Full user object.

---

### Get / Update Current User
`GET /auth/me/` 🔒  
`PATCH /auth/me/` 🔒

PATCH accepts `multipart/form-data` (for avatar upload) or JSON.

```json
{ "first_name": "John", "city": "Buea", "phone": "6XXXXXXXX" }
```

---

### Change Password
`POST /auth/me/change-password/` 🔒

```json
{ "old_password": "current", "new_password": "newpassword" }
```

**Response `200`:**
```json
{ "detail": "Password updated successfully." }
```

---

### Addresses
`GET /auth/me/addresses/` 🔒  
`POST /auth/me/addresses/` 🔒  
`GET /auth/me/addresses/<id>/` 🔒  
`PATCH /auth/me/addresses/<id>/` 🔒  
`DELETE /auth/me/addresses/<id>/` 🔒

**POST Body:**
```json
{ "label": "Home", "line": "123 Main St", "city": "Buea", "is_primary": true }
```

---

### Agent KYC Documents
`GET /auth/me/agent-kyc/` 🔒  
`POST /auth/me/agent-kyc/` 🔒 — `multipart/form-data`  
`GET /auth/me/agent-kyc/<id>/` 🔒  
`PATCH /auth/me/agent-kyc/<id>/` 🔒  
`DELETE /auth/me/agent-kyc/<id>/` 🔒

Fields: `doc_type` (`identity` / `driving_license` / `vehicle` / `address`), `label`, `file`

---

## Shops

### List Active Shops
`GET /shops/` — public

Query params: `?city=Buea` `?category=electronics`

---

### Shop Detail
`GET /shops/<handle>/` — public

---

### Shop Products
`GET /shops/<handle>/products/` — public

---

### Shop Reviews
`GET /shops/<handle>/reviews/` — public  
`POST /shops/<handle>/reviews/` 🔒

```json
{ "rating": 4, "text": "Great service!" }
```

---

### Follow / Unfollow a Shop
`POST /shops/<handle>/follow/` 🔒

Toggles. First call follows, second call unfollows.

**Response:** `{ "following": true }`

---

### My Shop (Vendor)
`GET /shops/my/` 🔒  
`PATCH /shops/my/` 🔒 — `multipart/form-data` for `logo` / `banner` uploads

---

### Create My Shop (Vendor)
`POST /shops/my/create/` 🔒

---

### Shop KYC Documents (Vendor)
`GET /shops/my/kyc/` 🔒  
`POST /shops/my/kyc/` 🔒 — `multipart/form-data`

Fields: `doc_type` (`identity` / `address` / `business`), `label`, `file`

---

### Shops I Follow
`GET /shops/followed/` 🔒

---

## Products

### List Products
`GET /products/` — public

| Param | Example | Description |
|-------|---------|-------------|
| `search` | `?search=shoes` | Search name / description / category |
| `category` | `?category=fashion` | Filter by category |
| `city` | `?city=Buea` | Filter by shop city |
| `condition` | `?condition=new` | `new` or `used` |
| `min_price` | `?min_price=500` | Minimum price |
| `max_price` | `?max_price=5000` | Maximum price |
| `ordering` | `?ordering=-price` | `price`, `-price`, `rating`, `created_at` |

---

### Product Detail
`GET /products/<id>/` — public

Each call increments the product's view count.

---

### Product Reviews
`GET /products/<id>/reviews/` — public  
`POST /products/<id>/reviews/` 🔒

```json
{ "rating": 4, "text": "Great product!" }
```

---

### Wishlist
`GET /products/wishlist/` 🔒  
`POST /products/wishlist/` 🔒  
`DELETE /products/wishlist/<id>/` 🔒

**POST Body:**
```json
{ "product_id": 42 }
```

---

### Vendor: My Products
`GET /products/vendor/` 🔒  
`POST /products/vendor/` 🔒

```json
{
  "name": "Air Jordan 1",
  "description": "Limited edition",
  "price": 45000,
  "category": "fashion",
  "condition": "new",
  "stock": 10,
  "status": "active"
}
```

---

### Vendor: Edit / Delete Product
`GET /products/vendor/<id>/` 🔒  
`PATCH /products/vendor/<id>/` 🔒  
`DELETE /products/vendor/<id>/` 🔒

---

### Vendor: Product Images
`GET /products/vendor/<id>/images/` 🔒  
`POST /products/vendor/<id>/images/` 🔒 — `multipart/form-data`

Fields: `image` (file), `is_primary` (bool), `order` (int)

`GET /products/vendor/<id>/images/<img_id>/` 🔒  
`PATCH /products/vendor/<id>/images/<img_id>/` 🔒  
`DELETE /products/vendor/<id>/images/<img_id>/` 🔒

---

## Orders

### List / Create Orders
`GET /orders/` 🔒  
`POST /orders/` 🔒

Response list is filtered by role: vendors see shop orders, agents see assigned orders, buyers see their own.

**POST Body (buyer):**
```json
{ "product": 42, "quantity": 2, "delivery_address": 1 }
```

---

### Order Detail
`GET /orders/<order_id>/` 🔒

---

### Update Order Status
`PATCH /orders/<order_id>/status/` 🔒

| Role | Allowed transition |
|------|--------------------|
| Vendor | `paid_escrow` → `preparing` |
| Vendor | `preparing` → `picked_up` |
| Agent | `picked_up` → `in_transit` |
| Agent | `in_transit` → `delivered_confirm` |

```json
{ "status": "preparing" }
```

---

### Buyer: Confirm Delivery
`POST /orders/<order_id>/confirm/` 🔒

Marks order `completed` and releases escrow to vendor.

---

### Vendor: Cancel Order
`POST /orders/<order_id>/cancel/` 🔒

Allowed from: `awaiting_payment`, `paid_escrow`, `preparing`, `agent_assigned`.

---

### Agent: Decline Assignment
`POST /orders/<order_id>/decline/` 🔒

Agent declines an `agent_assigned` order — reverts to `preparing` for reassignment.

---

### Order Status Flow

```
[created] → paid_escrow → preparing → agent_assigned → picked_up → in_transit → delivered_confirm → completed
                                     ↘ cancelled
                                                                                         ↘ disputed → refunded
                                                                                                    → partially_resolved
                                                                                                    → completed
```

---

## Messages

### List & Send Messages
`GET /orders/messages/` 🔒  
`POST /orders/messages/` 🔒

```json
{ "recipient": 5, "content": "Is this item still available?" }
```

---

## Agent

### Assigned Deliveries
`GET /orders/agent/assignments/` 🔒

Query param: `?status=in_transit`

---

### Agent Stats
`GET /orders/agent/stats/` 🔒

```json
{
  "today_deliveries": 3,
  "week_deliveries": 12,
  "week_earnings": 15000,
  "active_assignments": 2
}
```

---

## Payments

### Initiate Payment
`POST /payments/initiate/` 🔒

```json
{
  "order_id": "ORD-abc123",
  "method": "momo",
  "phone_number": "6XXXXXXXX"
}
```

`method`: `"momo"` | `"orange_money"`

---

### My Payouts
`GET /payments/payouts/` 🔒

---

## Notifications

`GET /notifications/` 🔒  
`GET /notifications/<id>/` 🔒  
`PATCH /notifications/<id>/` 🔒 — e.g. mark as read  
`POST /notifications/read-all/` 🔒

---

## Disputes

### File / List
`GET /disputes/` 🔒  
`POST /disputes/` 🔒

```json
{ "order": "ORD-abc123", "reason": "not_delivered", "description": "Package never arrived." }
```

---

### Dispute Detail
`GET /disputes/<dispute_id>/` 🔒

---

### Upload Evidence
`POST /disputes/<dispute_id>/evidence/` 🔒 — `multipart/form-data`

Field: `evidence` (file)

---

### Resolve Dispute (Admin)
`PATCH /disputes/<dispute_id>/resolve/` 🔒

```json
{ "resolution": "refund_buyer", "admin_note": "Item clearly not delivered." }
```

`resolution`: `refund_buyer` | `release_vendor` | `partial_refund`

---

## Admin Endpoints
All require `Authorization: Bearer <access_token>` for a staff/admin user.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/admin/stats/` | Platform KPIs |
| GET | `/auth/admin/users/` | All users (`?role=`, `?q=`) |
| PATCH | `/auth/admin/users/<id>/` | Toggle `is_active`, `role`, `is_kyc_verified` |
| GET | `/auth/admin/gmv/` | Daily GMV + top vendors |
| GET | `/auth/admin/shops/` | All shops (`?q=`) |
| GET | `/auth/admin/verification/` | Vendor KYC queue |
| PATCH | `/auth/admin/verification/<shop_id>/` | Approve / reject vendor |
| GET | `/auth/admin/agent-verification/` | Agent KYC queue |
| PATCH | `/auth/admin/agent-verification/<user_id>/` | Approve / reject agent |
| GET | `/auth/admin/disputes/` | All disputes (`?status=`) |
| GET | `/auth/admin/payouts/` | All payouts |
| GET | `/auth/admin/commissions/` | Monthly commission report |
| GET | `/auth/admin/health/` | System health checks |
| GET | `/auth/admin/fraud/` | Users with 3+ failed payments |

---

## Auth Header

```js
// Axios
axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;

// Fetch
fetch(url, {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  }
});
```

> The refresh token is in an HttpOnly cookie — never store it manually. Call `/auth/token/refresh/` to get a new access token when the current one expires (access tokens last 15 min, refresh tokens 7 days).

---

## Common Error Responses

| Status | Meaning |
|--------|---------|
| `400` | Validation error — check response body for field errors |
| `401` | Missing or expired token |
| `403` | Insufficient permissions |
| `404` | Resource not found |
| `429` | Rate limit exceeded |

```json
{ "field_name": ["This field is required."] }
```

---

> 🔒 = requires `Authorization: Bearer <access_token>`  
> Multipart endpoints are noted where applicable; everything else uses `Content-Type: application/json`.
