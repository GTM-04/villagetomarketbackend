"""
API Documentation.
"""

# Village to Market API Documentation

## Overview

The Village to Market API provides programmatic access to the agricultural marketplace platform. The API is built with FastAPI and follows REST principles.

## Base URL

```
Development: http://localhost:8001
Production: https://api.villagetomarket.zw
```

## Authentication

All protected endpoints require JWT authentication via Bearer token.

### Getting a Token

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "phone_number": "+263771234567",
  "password": "password123"
}
```

Response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "full_name": "John Doe",
    "phone_number": "+263771234567",
    "user_type": "farmer"
  }
}
```

### Using the Token

Include the access token in the Authorization header:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## Rate Limiting

API requests are rate-limited to:

- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message",
  "status_code": 400,
  "details": {}
}
```

## Endpoints

### Authentication

#### Register User

```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "full_name": "John Doe",
  "phone_number": "+263771234567",
  "password": "securepassword",
  "user_type": "farmer",
  "district": "Mashonaland East",
  "ward": "Ward 5"
}
```

#### Login

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "phone_number": "+263771234567",
  "password": "password123"
}
```

#### Refresh Token

```bash
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Users

#### Get Current User Profile

```bash
GET /api/v1/users/me
Authorization: Bearer {token}
```

#### Update Profile

```bash
PATCH /api/v1/users/me
Authorization: Bearer {token}
Content-Type: application/json

{
  "full_name": "Updated Name",
  "email": "email@example.com"
}
```

### Listings

#### List All Listings

```bash
GET /api/v1/listings/?district=Harare&page=1&page_size=20
```

#### Create Listing (Farmers Only)

```bash
POST /api/v1/listings/
Authorization: Bearer {token}
Content-Type: application/json

{
  "produce_type_id": 1,
  "quantity_available": 500,
  "unit": "kg",
  "price_per_unit": 2.50,
  "description": "Fresh organic tomatoes",
  "is_organic": true,
  "harvest_date": "2026-02-15"
}
```

#### Get Listing Details

```bash
GET /api/v1/listings/{listing_id}
```

#### Delete Listing

```bash
DELETE /api/v1/listings/{listing_id}
Authorization: Bearer {token}
```

### Messaging

#### List Conversations

```bash
GET /api/v1/messaging/conversations
Authorization: Bearer {token}
```

#### Get Messages

```bash
GET /api/v1/messaging/conversations/{conversation_id}/messages
Authorization: Bearer {token}
```

### Pricing

#### Get Market Prices

```bash
GET /api/v1/pricing/market-prices?district=Harare
```

### Notifications

#### List Notifications

```bash
GET /api/v1/notifications/
Authorization: Bearer {token}
```

#### Mark Notification as Read

```bash
POST /api/v1/notifications/{notification_id}/read
Authorization: Bearer {token}
```

### WebSocket

#### Connect to Chat

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/messaging/{conversation_id}/');

ws.onopen = () => {
  // Send message
  ws.send(JSON.stringify({
    type: 'chat_message',
    message: 'Hello!',
    client_id: 'unique-id'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

## SDKs and Libraries

### Python

```python
import requests

# Login
response = requests.post(
    'http://localhost:8001/api/v1/auth/login',
    json={
        'phone_number': '+263771234567',
        'password': 'password123'
    }
)
token = response.json()['access_token']

# Get listings
headers = {'Authorization': f'Bearer {token}'}
listings = requests.get(
    'http://localhost:8001/api/v1/listings/',
    headers=headers
)
```

### JavaScript

```javascript
const API_BASE = 'http://localhost:8001/api/v1';

// Login
const login = async (phone, password) => {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({phone_number: phone, password})
  });
  return await response.json();
};

// Get listings
const getListings = async (token) => {
  const response = await fetch(`${API_BASE}/listings/`, {
    headers: {'Authorization': `Bearer ${token}`}
  });
  return await response.json();
};
```

## Best Practices

1. **Cache tokens**: Don't request a new token for every API call
2. **Handle token expiry**: Implement automatic token refresh
3. **Use pagination**: Don't fetch all records at once
4. **Compress requests**: Use gzip compression for large payloads
5. **Handle errors gracefully**: Implement retry logic with exponential backoff

## Support

For API support, contact: <api-support@villagetomarket.zw>
