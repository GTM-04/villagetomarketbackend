# 🚀 Quick Start Guide - Village to Market

## ⚡ Get Running in 5 Minutes

### Prerequisites Check

```bash
python --version    # Need 3.9+
psql --version     # Need PostgreSQL 15+
redis-cli --version # Need Redis 6+
```

---

## Option 1: Automated Setup (Recommended)

```bash
# 1. Navigate to project
cd villagetomarketbackend

# 2. Run setup script (does everything!)
chmod +x setup.sh
./setup.sh

# 3. Start all services
# Terminal 1: Django
source venv/bin/activate
python manage.py runserver

# Terminal 2: FastAPI
source venv/bin/activate
uvicorn api.main:app --reload --port 8001

# Terminal 3: Celery Worker
source venv/bin/activate
celery -A config worker -l info

# Terminal 4: Celery Beat (optional)
source venv/bin/activate
celery -A config beat -l info

# Terminal 5: Redis (if not auto-starting)
redis-server
```

---

## Option 2: Docker (Easiest)

```bash
# One command to rule them all!
docker-compose up --build

# Access services:
# - Django Admin: http://localhost:8000/admin
# - FastAPI Docs: http://localhost:8001/api/docs
# - API Health: http://localhost:8001/health
```

---

## Option 3: Manual Setup

### Step 1: Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Database Setup

```bash
# Create PostgreSQL database
createdb villagetomarket

# Or using psql
psql -U postgres
CREATE DATABASE villagetomarket;
\q
```

### Step 3: Configuration

```bash
# Copy environment file
cp .env.example .env

# Edit with your settings
nano .env  # or use your editor
```

Minimum .env settings:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres:password@localhost:5432/villagetomarket
REDIS_URL=redis://localhost:6379/0
```

### Step 4: Initialize Database

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed with sample data
python manage.py seed_data
```

### Step 5: Start Services

```bash
# Start Django (Terminal 1)
python manage.py runserver

# Start FastAPI (Terminal 2)
uvicorn api.main:app --reload --port 8001

# Start Celery (Terminal 3)
celery -A config worker -l info

# Start Redis (Terminal 4, if needed)
redis-server
```

---

## 🎯 Verify Installation

### Check Django Admin

```bash
# Open browser: http://localhost:8000/admin
# Login with superuser credentials
```

### Check API Documentation

```bash
# Open browser: http://localhost:8001/api/docs
# Interactive API docs (Swagger UI)
```

### Test API Health

```bash
curl http://localhost:8001/health

# Should return:
# {"status":"healthy","version":"1.0.0"}
```

### Test Authentication

```bash
# Login with demo farmer account
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+263771234567",
    "password": "password123"
  }'
```

### Test Listing Creation

```bash
# First, login and get token (from previous step)
TOKEN="your-access-token-here"

# Create a listing
curl -X POST http://localhost:8001/api/v1/listings/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "produce_type_id": 1,
    "quantity_available": 100,
    "unit": "kg",
    "price_per_unit": 2.5,
    "description": "Fresh organic tomatoes",
    "is_organic": true
  }'
```

---

## 📱 Demo Accounts

After running `python manage.py seed_data`:

**Farmer Account:**

- Phone: `+263771234567`
- Password: `password123`
- Name: Tendai Moyo
- Farm: Moyo Family Farm

**Buyer Account:**

- Phone: `+263772345678`
- Password: `password123`
- Name: Rudo Ncube
- Organization: Fresh Foods Ltd

---

## 🔍 Troubleshooting

### Port Already in Use

```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
python manage.py runserver 8002
```

### Database Connection Error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U postgres -d villagetomarket -c "SELECT 1"
```

### Redis Connection Error

```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Or start Redis
redis-server
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check virtual environment is activated
which python  # Should point to venv/bin/python
```

### Migration Errors

```bash
# Reset migrations (development only!)
python manage.py migrate --run-syncdb

# Or delete database and start fresh
dropdb villagetomarket
createdb villagetomarket
python manage.py migrate
```

---

## 🎓 Next Steps

### 1. Explore Django Admin

- Visit: <http://localhost:8000/admin>
- Create users, listings, categories
- Explore all models

### 2. Test API Endpoints

- Visit: <http://localhost:8001/api/docs>
- Use "Try it out" on each endpoint
- Test with demo accounts

### 3. Read Documentation

- `README.md` - Complete overview
- `docs/API.md` - API documentation  
- `docs/DEPLOYMENT.md` - Production guide
- `PROJECT_COMPLETE.md` - Full feature list

### 4. Start Developing

- Create new endpoints in `api/v1/endpoints/`
- Add models in `apps/*/models.py`
- Add background tasks in `apps/*/tasks.py`

---

## 📊 Useful Commands

### Django

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Shell
python manage.py shell

# Collect static files
python manage.py collectstatic
```

### Celery

```bash
# Worker
celery -A config worker -l info

# Beat (scheduler)
celery -A config beat -l info

# Monitor tasks
celery -A config flower  # Install: pip install flower
```

### Database

```bash
# Backup
pg_dump villagetomarket > backup.sql

# Restore
psql villagetomarket < backup.sql

# Reset
dropdb villagetomarket && createdb villagetomarket
```

### Docker

```bash
# Build and start
docker-compose up --build

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Execute command in container
docker-compose exec web python manage.py migrate
```

---

## 🌐 Important URLs

- **Django Admin**: <http://localhost:8000/admin>
- **API Docs (Swagger)**: <http://localhost:8001/api/docs>
- **API ReDoc**: <http://localhost:8001/api/redoc>
- **API Health**: <http://localhost:8001/health>
- **Flower (Celery Monitor)**: <http://localhost:5555> (if installed)

---

## 💡 Pro Tips

1. **Use setup.sh**: Automates everything
2. **Check logs**: Look at terminal output for errors
3. **Read error messages**: They usually point to the issue
4. **Use API docs**: Interactive testing is built-in
5. **Start simple**: Test one endpoint at a time

---

## ✅ Success Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] PostgreSQL running
- [ ] Redis running
- [ ] Database migrated
- [ ] Sample data seeded
- [ ] Django server running (port 8000)
- [ ] FastAPI server running (port 8001)
- [ ] Can access admin panel
- [ ] Can access API docs
- [ ] Health check returns "healthy"
- [ ] Can login with demo account

---

## 🆘 Getting Help

If stuck:

1. Check terminal output for errors
2. Read error messages carefully
3. Verify all services are running
4. Check `.env` configuration
5. Review documentation files
6. Check PostgreSQL and Redis are running

---

## 🎉 You're All Set

If you can:

- ✅ Access Django admin
- ✅ View API docs
- ✅ Login with demo accounts
- ✅ Create a listing

**You're ready to develop!** 🚀

---

*Happy Coding! 💻*
