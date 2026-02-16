# 📋 API Quick Reference - Village to Market

**Base URL**: `http://localhost:8001/api/v1`  
**Authentication**: Bearer Token in Authorization header

---

## 🔐 Authentication Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/auth/register` | ❌ | Register new user |
| POST | `/auth/login` | ❌ | User login |
| POST | `/auth/refresh` | ❌ | Refresh access token |

---

## 👤 User Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/users/me` | ✅ | Get current user profile |
| PATCH | `/users/me` | ✅ | Update user profile |

---

## 📦 Listing Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/listings/` | ❌ | List all listings |
| POST | `/listings/` | ✅ (Farmer) | Create new listing |
| GET | `/listings/{id}` | ❌ | Get listing details |
| DELETE | `/listings/{id}` | ✅ (Owner) | Delete listing |

**Query Parameters for GET /listings/**:

- `district` - Filter by district
- `produce_type` - Filter by produce type ID
- `status` - Filter by status (default: active)
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)

---

## 💬 Messaging Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/messaging/conversations` | ✅ | List user's conversations |
| GET | `/messaging/conversations/{id}/messages` | ✅ | Get messages in conversation |

**WebSocket**: `ws://localhost:8001/ws/messaging/{conversation_id}/`

---

## 💰 Pricing Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/pricing/market-prices` | ❌ | Get current market prices |

**Query Parameters**:

- `district` - Filter by district
- `produce_type` - Filter by produce name

---

## 🔔 Notification Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/notifications/` | ✅ | List user's notifications |
| POST | `/notifications/{id}/read` | ✅ | Mark notification as read |

---

## 🛒 Marketplace Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/marketplace/orders` | ✅ | List user's orders |

---

## 🔄 Offline Sync Endpoint

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/sync/` | ✅ | Sync offline changes |

---

## 📝 Request/Response Examples

### Login

```bash
# Request
POST /auth/login
{
  "phone_number": "+263771234567",
  "password": "password123"
}

# Response
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "full_name": "John Doe",
    "phone_number": "+263771234567",
    "user_type": "farmer"
  }
}
```

### Get Listings

```bash
# Request
GET /listings/?district=Harare&page=1&page_size=20

# Response
[
  {
    "id": "uuid",
    "title": "Fresh Organic Tomatoes",
    "produce_type": {"id": 1, "name": "Tomatoes"},
    "quantity_available": 500.0,
    "unit": "kg",
    "price_per_unit": 2.50,
    "currency": "ZWL",
    "district": "Harare",
    "status": "active",
    "is_organic": true,
    "harvest_date": "2026-02-15",
    "images": ["url1", "url2"]
  }
]
```

### Create Listing

```bash
# Request
POST /listings/
Authorization: Bearer {token}
{
  "produce_type_id": 1,
  "quantity_available": 500,
  "unit": "kg",
  "price_per_unit": 2.50,
  "description": "Fresh organic tomatoes",
  "is_organic": true,
  "harvest_date": "2026-02-15"
}

# Response
{
  "id": "uuid",
  "title": "Tomatoes - Harare",
  ...
}
```

---

## 🔌 WebSocket Messages

### Send Message

```json
{
  "type": "chat_message",
  "message": "Hello!",
  "client_id": "unique-id-123"
}
```

### Receive Message

```json
{
  "type": "chat_message",
  "message": {
    "id": "uuid",
    "text": "Hello!",
    "sender_id": "uuid",
    "sender_name": "John Doe",
    "created_at": "2026-02-16T10:30:00Z",
    "client_id": "unique-id-123"
  }
}
```

### Send Typing Indicator

```json
{
  "type": "typing",
  "is_typing": true
}
```

### Send Read Receipt

```json
{
  "type": "read_receipt",
  "message_id": "uuid"
}
```

---

## ⚠️ Error Responses

All errors follow this format:

```json
{
  "error": "Error message description",
  "status_code": 400,
  "details": {}
}
```

### Common Status Codes

- **200 OK** - Success
- **201 Created** - Resource created
- **204 No Content** - Success with no response body
- **400 Bad Request** - Invalid request data
- **401 Unauthorized** - Missing or invalid token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **422 Unprocessable Entity** - Validation error
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Server error

---

## 🔒 Authentication Header

Include in all authenticated requests:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## 🧪 Demo Accounts

**Farmer:**

- Phone: `+263771234567`
- Password: `password123`

**Buyer:**

- Phone: `+263772345678`
- Password: `password123`

---

## 📱 Rate Limits

- **Authenticated**: 100 requests/minute
- **Unauthenticated**: 20 requests/minute

---

## 🎯 Quick Start Code (JavaScript)

```javascript
// 1. Login
const loginResponse = await fetch('http://localhost:8001/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    phone_number: '+263771234567',
    password: 'password123'
  })
});
const { access_token } = await loginResponse.json();

// 2. Get Listings
const listingsResponse = await fetch('http://localhost:8001/api/v1/listings/', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const listings = await listingsResponse.json();

// 3. WebSocket Chat
const ws = new WebSocket('ws://localhost:8001/ws/messaging/{conversation_id}/');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
ws.send(JSON.stringify({
  type: 'chat_message',
  message: 'Hello!'
}));
```

---

## 📚 Additional Resources

- **Full Documentation**: `FRONTEND_INTEGRATION.md`
- **API Interactive Docs**: <http://localhost:8001/api/docs>
- **Project README**: `README.md`
- **Deployment Guide**: `docs/DEPLOYMENT.md`

---

**Last Updated**: February 16, 2026
