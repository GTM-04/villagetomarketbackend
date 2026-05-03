# From Village to Market - Backend

Progressive Web Application backend for connecting rural Zimbabwean farmers directly with urban buyers.

## Features

- 🔐 Phone-based authentication (Zimbabwe format)
- 👨‍🌾 Farmer and Buyer profiles with role-based access
- 📝 Product listings with categories and filtering
- 💬 Real-time messaging with WebSocket support
- 📊 Market pricing and trends
- 🔄 Offline-first sync capability
- 📱 Push notifications and SMS alerts
- 🔍 Full-text search with Elasticsearch
- 🗺️ Geospatial queries for nearby listings

## Tech Stack

- **Framework**: Django 5.0 + FastAPI 0.110
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **Search**: Elasticsearch
- **WebSocket**: Django Channels
- **Python**: 3.11+

## Quick Start

### 1. Setup Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Seed Data

```bash
python scripts/seed_data.py
```

### 6. Run Development Servers

```bash
# Django development server

daphne -b 0.0.0.0 -p 8000 config.asgi:application


python manage.py runserver

# FastAPI server (in another terminal)
uvicorn api.main:app --reload --port 8001

# Celery worker (in another terminal)
celery -A config worker -l info

# Celery beat (in another terminal)
celery -A config beat -l info
```

## Docker Setup

```bash
# Build and start all services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f web
```

## API Documentation

- Django Admin: http://localhost:8000/admin/
- FastAPI Docs: http://localhost:8001/docs
- FastAPI ReDoc: http://localhost:8001/redoc
- Flower (Celery): http://localhost:5555

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test file
pytest apps/users/tests/test_models.py
```

## Project Structure

```
from-village-to-market-backend/
├── config/              # Django configuration
├── apps/                # Django applications
│   ├── users/          # User management
│   ├── farmers/        # Farmer profiles
│   ├── buyers/         # Buyer profiles
│   ├── listings/       # Product listings
│   ├── marketplace/    # Orders & transactions
│   ├── messaging/      # Chat & messaging
│   ├── pricing/        # Market intelligence
│   ├── notifications/  # Push & SMS notifications
│   ├── search/         # Elasticsearch integration
│   ├── analytics/      # Analytics & reporting
│   └── core/           # Shared utilities
├── api/                # FastAPI application
│   ├── v1/            # API v1 routes
│   ├── schemas/       # Pydantic schemas
│   └── crud/          # CRUD operations
├── scripts/           # Utility scripts
├── tests/             # Integration tests
└── media/             # User uploads
```

## Development Commands

```bash
# Code formatting
black .

# Linting
flake8

# Type checking
mypy .

# Create new Django app
python manage.py startapp app_name apps/app_name

# Make migrations
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user

### Listings
- `GET /api/v1/listings` - List all listings
- `POST /api/v1/listings` - Create listing
- `GET /api/v1/listings/{id}` - Get listing detail
- `PUT /api/v1/listings/{id}` - Update listing
- `DELETE /api/v1/listings/{id}` - Delete listing

### Messaging
- `GET /api/v1/messaging/conversations` - Get conversations
- `POST /api/v1/messaging/conversations` - Start conversation
- `WS /api/v1/messaging/ws/{conversation_id}` - WebSocket connection

### Pricing
- `GET /api/v1/pricing/market-prices` - Get market prices
- `GET /api/v1/pricing/trends/{produce_type_id}` - Get price trends

### Sync
- `POST /api/v1/sync/batch` - Batch sync operations
- `GET /api/v1/sync/status` - Get sync status

## Environment Variables

See `.env.example` for all available configuration options.

## License

Proprietary - All rights reserved

## Support

For support, email support@villagetomarket.zw
