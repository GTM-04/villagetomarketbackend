#!/bin/bash

# Village to Market - Setup Script
# Run this script to set up the development environment

echo "================================"
echo "Village to Market - Setup Script"
echo "================================"

# Check Python version
python_version=$(python --version 2>&1 | grep -oP '\d+\.\d+')
if (( $(echo "$python_version < 3.9" | bc -l) )); then
    echo "Error: Python 3.9 or higher is required"
    exit 1
fi

echo "✓ Python version: $(python --version)"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
source venv/bin/activate || . venv/Scripts/activate

echo "✓ Virtual environment created"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✓ Dependencies installed"

# Copy environment variables
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created - Please update with your settings"
else
    echo ""
    echo "✓ .env file already exists"
fi

# Run migrations
echo ""
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

echo "✓ Migrations completed"

# Seed database
echo ""
echo "Seeding database with initial data..."
python manage.py seed_data

echo "✓ Database seeded"

# Create superuser prompt
echo ""
echo "Would you like to create a superuser? (y/n)"
read -r create_superuser

if [ "$create_superuser" = "y" ]; then
    python manage.py createsuperuser
fi

echo ""
echo "================================"
echo "Setup completed successfully!"
echo "================================"
echo ""
echo "To start the development server:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Start combined Django + FastAPI server: daphne -b 0.0.0.0 -p 8000 config.asgi:application"
echo "  3. Start Celery: celery -A config worker -l info"
echo "  4. Start Celery Beat: celery -A config beat -l info"
echo ""
echo "Demo accounts:"
echo "  Farmer: +263771234567 / password123"
echo "  Buyer: +263772345678 / password123"
echo ""
