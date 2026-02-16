# 🚀 Frontend Integration Guide - Village to Market API

**Version**: 1.0.0  
**Last Updated**: February 16, 2026  
**Base URL**: `http://localhost:8001/api/v1` (Development)  
**Production URL**: `https://api.villagetomarket.zw/api/v1`

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [WebSocket (Real-time Chat)](#websocket-real-time-chat)
5. [Data Models](#data-models)
6. [Error Handling](#error-handling)
7. [Code Examples](#code-examples)
8. [File Upload](#file-upload)
9. [Pagination](#pagination)
10. [Best Practices](#best-practices)

---

## 🚀 Quick Start

### Base Configuration
```javascript
const API_CONFIG = {
  baseURL: 'http://localhost:8001/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
};
```

### Demo Accounts
```javascript
// Farmer Account
const DEMO_FARMER = {
  phone: '+263771234567',
  password: 'password123'
};

// Buyer Account
const DEMO_BUYER = {
  phone: '+263772345678',
  password: 'password123'
};
```

---

## 🔐 Authentication

### Flow Overview
1. User registers or logs in
2. Backend returns `access_token` and `refresh_token`
3. Store tokens securely (localStorage for web, SecureStore for mobile)
4. Include `access_token` in Authorization header for all requests
5. Refresh token when it expires

### Endpoints

#### 1. Register User
```http
POST /auth/register
Content-Type: application/json

{
  "full_name": "John Doe",
  "phone_number": "+263771234567",
  "password": "securePassword123",
  "user_type": "farmer",  // "farmer" or "buyer"
  "district": "Mashonaland East",
  "ward": "Ward 5"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "full_name": "John Doe",
    "phone_number": "+263771234567",
    "user_type": "farmer"
  }
}
```

#### 2. Login
```http
POST /auth/login
Content-Type: application/json

{
  "phone_number": "+263771234567",
  "password": "password123"
}
```

**Response (200 OK):** Same as register

#### 3. Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200 OK):** Returns new tokens

### Using Tokens
```javascript
// Add to all authenticated requests
headers: {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
}
```

---

## 📡 API Endpoints

### **Users**

#### Get Current User Profile
```http
GET /users/me
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "John Doe",
  "phone_number": "+263771234567",
  "email": "john@example.com",
  "user_type": "farmer",
  "district": "Mashonaland East",
  "ward": "Ward 5",
  "is_verified": true,
  "profile": {
    "farm_name": "Doe Family Farm",
    "farm_size": "5.5",
    "verified": true
  }
}
```

#### Update User Profile
```http
PATCH /users/me
Authorization: Bearer {token}
Content-Type: application/json

{
  "full_name": "John Updated Doe",
  "email": "newemail@example.com",
  "district": "Harare",
  "ward": "Ward 12"
}
```

**Response (200 OK):** Returns updated user profile

---

### **Listings**

#### List All Listings
```http
GET /listings/?district=Harare&produce_type=1&status=active&page=1&page_size=20
```

**Query Parameters:**
- `district` (optional): Filter by district
- `produce_type` (optional): Filter by produce type ID
- `status` (optional): Default "active"
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Fresh Organic Tomatoes - Harare",
    "produce_type": {
      "id": 1,
      "name": "Tomatoes"
    },
    "quantity_available": 500.0,
    "unit": "kg",
    "price_per_unit": 2.50,
    "currency": "ZWL",
    "district": "Harare",
    "status": "active",
    "is_organic": true,
    "harvest_date": "2026-02-10",
    "images": [
      "http://localhost:8001/media/listings/tomatoes1.jpg",
      "http://localhost:8001/media/listings/tomatoes2.jpg"
    ]
  }
]
```

#### Create Listing (Farmers Only)
```http
POST /listings/
Authorization: Bearer {token}
Content-Type: application/json

{
  "produce_type_id": 1,
  "quantity_available": 500,
  "unit": "kg",
  "price_per_unit": 2.50,
  "description": "Fresh organic tomatoes, just harvested",
  "is_organic": true,
  "harvest_date": "2026-02-15"
}
```

**Response (201 Created):** Returns created listing

#### Get Listing Details
```http
GET /listings/{listing_id}
```

**Response (200 OK):** Returns single listing object

#### Delete Listing (Owner Only)
```http
DELETE /listings/{listing_id}
Authorization: Bearer {token}
```

**Response (204 No Content)**

---

### **Messaging**

#### List Conversations
```http
GET /messaging/conversations
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "other_user": {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "name": "Jane Smith"
    },
    "last_message": "Hello, is this still available?",
    "last_message_at": "2026-02-16T10:30:00Z",
    "unread_count": 2
  }
]
```

#### Get Messages in Conversation
```http
GET /messaging/conversations/{conversation_id}/messages
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440000",
    "sender_id": "770e8400-e29b-41d4-a716-446655440000",
    "text": "Hello, is this still available?",
    "created_at": "2026-02-16T10:30:00Z",
    "is_read": true
  },
  {
    "id": "990e8400-e29b-41d4-a716-446655440000",
    "sender_id": "550e8400-e29b-41d4-a716-446655440000",
    "text": "Yes, 500kg still available!",
    "created_at": "2026-02-16T10:35:00Z",
    "is_read": false
  }
]
```

---

### **Pricing**

#### Get Market Prices
```http
GET /pricing/market-prices?district=Harare&produce_type=Tomatoes
```

**Query Parameters:**
- `district` (optional): Filter by district
- `produce_type` (optional): Filter by produce name

**Response (200 OK):**
```json
[
  {
    "produce_type": "Tomatoes",
    "district": "Harare",
    "price_min": 2.00,
    "price_avg": 2.50,
    "price_max": 3.00,
    "unit": "kg",
    "recorded_date": "2026-02-16"
  }
]
```

---

### **Notifications**

#### List Notifications
```http
GET /notifications/
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
[
  {
    "id": "aa0e8400-e29b-41d4-a716-446655440000",
    "title": "New Message",
    "message": "You have a new message from Jane Smith",
    "notification_type": "new_message",
    "is_read": false,
    "created_at": "2026-02-16T10:30:00Z"
  }
]
```

#### Mark Notification as Read
```http
POST /notifications/{notification_id}/read
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "message": "Notification marked as read"
}
```

---

### **Marketplace**

#### List Orders
```http
GET /marketplace/orders
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
[
  {
    "id": "bb0e8400-e29b-41d4-a716-446655440000",
    "order_number": "ORD12345678",
    "listing_title": "Fresh Organic Tomatoes - Harare",
    "quantity": 50.0,
    "total_amount": 125.00,
    "status": "pending",
    "created_at": "2026-02-16T09:00:00Z"
  }
]
```

---

### **Offline Sync**

#### Sync Offline Changes
```http
POST /sync/
Authorization: Bearer {token}
Content-Type: application/json

{
  "last_sync": "2026-02-16T08:00:00Z",
  "changes": [
    {
      "entity_type": "message",
      "entity_id": "temp-123",
      "action": "create",
      "data": {
        "conversation_id": "660e8400-e29b-41d4-a716-446655440000",
        "text": "Message sent while offline"
      },
      "timestamp": "2026-02-16T10:00:00Z",
      "client_id": "client-msg-123"
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "conflicts": [],
  "server_changes": [
    {
      "entity_type": "listing",
      "entity_id": "550e8400-e29b-41d4-a716-446655440000",
      "action": "update",
      "data": {
        "quantity_available": 450.0
      },
      "timestamp": "2026-02-16T09:30:00Z"
    }
  ]
}
```

---

## 💬 WebSocket (Real-time Chat)

### Connection
```javascript
const conversationId = '660e8400-e29b-41d4-a716-446655440000';
const ws = new WebSocket(`ws://localhost:8001/ws/messaging/${conversationId}/`);

// For production with SSL
// const ws = new WebSocket(`wss://api.villagetomarket.zw/ws/messaging/${conversationId}/`);
```

### Message Types

#### Send Chat Message
```javascript
ws.send(JSON.stringify({
  type: 'chat_message',
  message: 'Hello from frontend!',
  client_id: 'unique-client-msg-id-123'
}));
```

#### Send Typing Indicator
```javascript
ws.send(JSON.stringify({
  type: 'typing',
  is_typing: true
}));
```

#### Send Read Receipt
```javascript
ws.send(JSON.stringify({
  type: 'read_receipt',
  message_id: '880e8400-e29b-41d4-a716-446655440000'
}));
```

### Receiving Messages

#### Chat Message
```json
{
  "type": "chat_message",
  "message": {
    "id": "990e8400-e29b-41d4-a716-446655440000",
    "text": "Hello!",
    "sender_id": "770e8400-e29b-41d4-a716-446655440000",
    "sender_name": "Jane Smith",
    "created_at": "2026-02-16T10:30:00Z",
    "client_id": "unique-client-msg-id-123"
  }
}
```

#### Typing Indicator
```json
{
  "type": "typing",
  "user_id": "770e8400-e29b-41d4-a716-446655440000",
  "user_name": "Jane Smith",
  "is_typing": true
}
```

#### Read Receipt
```json
{
  "type": "read_receipt",
  "message_id": "880e8400-e29b-41d4-a716-446655440000",
  "user_id": "770e8400-e29b-41d4-a716-446655440000"
}
```

---

## 📊 Data Models

### User Types
```typescript
type UserType = 'farmer' | 'buyer';

interface User {
  id: string;
  full_name: string;
  phone_number: string;
  email?: string;
  user_type: UserType;
  district: string;
  ward: string;
  is_verified: boolean;
  profile?: FarmerProfile | BuyerProfile;
}

interface FarmerProfile {
  farm_name: string;
  farm_size: string;
  verified: boolean;
}

interface BuyerProfile {
  organization_name: string;
  buyer_type: string;
}
```

### Listing
```typescript
interface Listing {
  id: string;
  title: string;
  produce_type: ProduceType;
  quantity_available: number;
  unit: string;
  price_per_unit: number;
  currency: string;
  district: string;
  status: 'active' | 'sold' | 'expired';
  is_organic: boolean;
  harvest_date?: string;
  images: string[];
}

interface ProduceType {
  id: number;
  name: string;
}
```

### Message
```typescript
interface Conversation {
  id: string;
  other_user: {
    id: string;
    name: string;
  };
  last_message?: string;
  last_message_at?: string;
  unread_count: number;
}

interface Message {
  id: string;
  sender_id: string;
  text: string;
  created_at: string;
  is_read: boolean;
}
```

### Notification
```typescript
type NotificationType = 
  | 'new_message' 
  | 'new_listing' 
  | 'price_alert' 
  | 'inquiry' 
  | 'order_status' 
  | 'system';

interface Notification {
  id: string;
  title: string;
  message: string;
  notification_type: NotificationType;
  is_read: boolean;
  created_at: string;
}
```

---

## ⚠️ Error Handling

### Error Response Format
```json
{
  "error": "Error message",
  "status_code": 400,
  "details": {}
}
```

### Common Error Codes

| Code | Meaning | Handling |
|------|---------|----------|
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Token expired, refresh or login |
| 403 | Forbidden | User lacks permission |
| 404 | Not Found | Resource doesn't exist |
| 422 | Validation Error | Check field requirements |
| 429 | Too Many Requests | Implement rate limiting |
| 500 | Server Error | Retry with exponential backoff |

---

## 💻 Code Examples

### React/JavaScript Example

```javascript
// api.js - API Service
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8001/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor - Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - Handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and hasn't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(
          `${API_BASE_URL}/auth/refresh`,
          { refresh_token: refreshToken }
        );

        const { access_token, refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth methods
export const auth = {
  register: (data) => api.post('/auth/register', data),
  login: (phone_number, password) => 
    api.post('/auth/login', { phone_number, password }),
  refresh: (refresh_token) => 
    api.post('/auth/refresh', { refresh_token }),
};

// User methods
export const users = {
  getProfile: () => api.get('/users/me'),
  updateProfile: (data) => api.patch('/users/me', data),
};

// Listings methods
export const listings = {
  list: (params) => api.get('/listings/', { params }),
  create: (data) => api.post('/listings/', data),
  get: (id) => api.get(`/listings/${id}`),
  delete: (id) => api.delete(`/listings/${id}`),
};

// Messaging methods
export const messaging = {
  listConversations: () => api.get('/messaging/conversations'),
  getMessages: (conversationId) => 
    api.get(`/messaging/conversations/${conversationId}/messages`),
};

// Pricing methods
export const pricing = {
  getMarketPrices: (params) => 
    api.get('/pricing/market-prices', { params }),
};

// Notifications methods
export const notifications = {
  list: () => api.get('/notifications/'),
  markRead: (id) => api.post(`/notifications/${id}/read`),
};

export default api;
```

### React Hook Examples

```javascript
// useAuth.js
import { useState, useEffect } from 'react';
import { auth } from './api';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      // Verify token and get user
      users.getProfile()
        .then(response => setUser(response.data))
        .catch(() => setUser(null))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (phone, password) => {
    const response = await auth.login(phone, password);
    const { access_token, refresh_token, user } = response.data;
    
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    setUser(user);
    
    return user;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  return { user, loading, login, logout };
};
```

```javascript
// useWebSocket.js
import { useEffect, useRef, useState } from 'react';

export const useWebSocket = (conversationId) => {
  const ws = useRef(null);
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!conversationId) return;

    // Connect to WebSocket
    ws.current = new WebSocket(
      `ws://localhost:8001/ws/messaging/${conversationId}/`
    );

    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'chat_message') {
        setMessages(prev => [...prev, data.message]);
      }
    };

    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    };

    // Cleanup
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [conversationId]);

  const sendMessage = (text) => {
    if (ws.current && connected) {
      ws.current.send(JSON.stringify({
        type: 'chat_message',
        message: text,
        client_id: `msg-${Date.now()}`
      }));
    }
  };

  const sendTypingIndicator = (isTyping) => {
    if (ws.current && connected) {
      ws.current.send(JSON.stringify({
        type: 'typing',
        is_typing: isTyping
      }));
    }
  };

  return { messages, sendMessage, sendTypingIndicator, connected };
};
```

### React Component Example

```jsx
// LoginScreen.jsx
import React, { useState } from 'react';
import { useAuth } from './useAuth';

const LoginScreen = () => {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      await login(phone, password);
      // Navigate to home
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Login</h2>
      {error && <div className="error">{error}</div>}
      
      <input
        type="tel"
        placeholder="Phone Number (+263...)"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        required
      />
      
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      
      <button type="submit">Login</button>
    </form>
  );
};
```

```jsx
// ChatComponent.jsx
import React, { useState, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import { messaging } from './api';

const ChatComponent = ({ conversationId }) => {
  const [messageText, setMessageText] = useState('');
  const [messages, setMessages] = useState([]);
  const { messages: wsMessages, sendMessage, connected } = useWebSocket(conversationId);

  // Load initial messages
  useEffect(() => {
    messaging.getMessages(conversationId)
      .then(response => setMessages(response.data));
  }, [conversationId]);

  // Add WebSocket messages to list
  useEffect(() => {
    if (wsMessages.length > 0) {
      setMessages(prev => [...prev, ...wsMessages]);
    }
  }, [wsMessages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (messageText.trim()) {
      sendMessage(messageText);
      setMessageText('');
    }
  };

  return (
    <div className="chat">
      <div className="messages">
        {messages.map(msg => (
          <div key={msg.id} className="message">
            <p>{msg.text}</p>
            <span>{new Date(msg.created_at).toLocaleTimeString()}</span>
          </div>
        ))}
      </div>

      <form onSubmit={handleSend}>
        <input
          type="text"
          value={messageText}
          onChange={(e) => setMessageText(e.target.value)}
          placeholder="Type a message..."
          disabled={!connected}
        />
        <button type="submit" disabled={!connected}>Send</button>
      </form>
    </div>
  );
};
```

---

## 📤 File Upload

### Upload Listing Images
```javascript
const uploadListingImage = async (listingId, file) => {
  const formData = new FormData();
  formData.append('image', file);

  const response = await api.post(
    `/listings/${listingId}/images/`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  );

  return response.data;
};
```

---

## 📄 Pagination

### Handling Paginated Responses

```javascript
const fetchListings = async (page = 1, pageSize = 20) => {
  const response = await listings.list({
    page,
    page_size: pageSize
  });

  return {
    items: response.data,
    hasMore: response.data.length === pageSize
  };
};

// Infinite scroll example
const [items, setItems] = useState([]);
const [page, setPage] = useState(1);
const [hasMore, setHasMore] = useState(true);

const loadMore = async () => {
  const result = await fetchListings(page + 1);
  setItems(prev => [...prev, ...result.items]);
  setHasMore(result.hasMore);
  setPage(prev => prev + 1);
};
```

---

## ✅ Best Practices

### 1. Token Management
```javascript
// Store tokens securely
localStorage.setItem('access_token', token);  // Web
// Or use SecureStore for React Native

// Always handle token expiration
// Implement auto-refresh (see interceptor example above)
```

### 2. Error Handling
```javascript
try {
  const response = await api.get('/listings/');
  // Handle success
} catch (error) {
  if (error.response) {
    // Server responded with error
    console.error(error.response.data.error);
  } else if (error.request) {
    // No response received
    console.error('Network error');
  } else {
    // Request setup error
    console.error(error.message);
  }
}
```

### 3. Loading States
```javascript
const [loading, setLoading] = useState(false);

const fetchData = async () => {
  setLoading(true);
  try {
    const response = await api.get('/listings/');
    // Update state
  } catch (error) {
    // Handle error
  } finally {
    setLoading(false);
  }
};
```

### 4. Debouncing Search
```javascript
import { debounce } from 'lodash';

const debouncedSearch = debounce(async (query) => {
  const response = await listings.list({ search: query });
  setResults(response.data);
}, 300);
```

### 5. WebSocket Reconnection
```javascript
const connectWebSocket = (conversationId, retries = 3) => {
  const ws = new WebSocket(`ws://localhost:8001/ws/messaging/${conversationId}/`);

  ws.onclose = () => {
    if (retries > 0) {
      setTimeout(() => {
        connectWebSocket(conversationId, retries - 1);
      }, 1000);
    }
  };

  return ws;
};
```

---

## 🔍 Testing Endpoints

### Using cURL
```bash
# Login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+263771234567", "password": "password123"}'

# Get listings
curl http://localhost:8001/api/v1/listings/

# Get profile (with token)
curl http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Using Postman
1. Import API collection from API docs
2. Set environment variable: `baseUrl = http://localhost:8001/api/v1`
3. Create `{{token}}` variable
4. Test all endpoints interactively

---

## 📱 Mobile App Considerations

### React Native
```javascript
// Use AsyncStorage for tokens
import AsyncStorage from '@react-native-async-storage/async-storage';

await AsyncStorage.setItem('access_token', token);
const token = await AsyncStorage.getItem('access_token');

// Use react-native-websocket for WebSocket
// Use react-native-image-picker for file uploads
```

### Flutter
```dart
// Use flutter_secure_storage for tokens
// Use dio package for HTTP requests
// Use web_socket_channel for WebSocket
```

---

## 🎯 Quick Reference

### Important URLs
- **API Docs**: http://localhost:8001/api/docs
- **Health Check**: http://localhost:8001/health
- **WebSocket**: ws://localhost:8001/ws/messaging/{id}/

### Rate Limits
- Authenticated: 100 requests/minute
- Unauthenticated: 20 requests/minute

### File Size Limits
- Images: 10MB max
- Other files: 10MB max

### Supported Image Formats
- JPEG, PNG, WebP

---

## 🆘 Support

### For Issues
- Check API docs: http://localhost:8001/api/docs
- Review error messages carefully
- Check network tab in browser DevTools
- Verify token is being sent correctly

### Contact
- Email: api-support@villagetomarket.zw
- Slack: #frontend-support

---

## 📝 Changelog

### Version 1.0.0 (Feb 16, 2026)
- Initial API release
- All core endpoints implemented
- WebSocket chat support
- Offline sync capability

---

**Happy Coding! 🚀**

*Last Updated: February 16, 2026*
