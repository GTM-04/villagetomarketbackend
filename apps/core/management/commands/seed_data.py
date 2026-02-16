"""
Seed database with initial data.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.listings.models import Category, ProduceType
from apps.users.models import User
from apps.farmers.models import FarmerProfile
from apps.buyers.models import BuyerProfile


class Command(BaseCommand):
    help = 'Seed database with initial data'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        # Create categories and produce types
        self.stdout.write('Creating categories and produce types...')
        
        # Vegetables
        veg_category = Category.objects.get_or_create(
            name='Vegetables',
            defaults={'description': 'Fresh vegetables'}
        )[0]
        
        vegetables = [
            'Tomatoes', 'Onions', 'Cabbage', 'Rape', 'Carrots',
            'Potatoes', 'Sweet Potatoes', 'Butternut', 'Pumpkin'
        ]
        for veg in vegetables:
            ProduceType.objects.get_or_create(
                name=veg,
                category=veg_category,
                defaults={'description': f'Fresh {veg}'}
            )
        
        # Grains
        grain_category = Category.objects.get_or_create(
            name='Grains',
            defaults={'description': 'Cereals and grains'}
        )[0]
        
        grains = ['Maize', 'Wheat', 'Sorghum', 'Millet', 'Rice']
        for grain in grains:
            ProduceType.objects.get_or_create(
                name=grain,
                category=grain_category,
                defaults={'description': f'{grain} grain'}
            )
        
        # Fruits
        fruit_category = Category.objects.get_or_create(
            name='Fruits',
            defaults={'description': 'Fresh fruits'}
        )[0]
        
        fruits = [
            'Bananas', 'Mangoes', 'Oranges', 'Avocados', 'Papayas',
            'Guavas', 'Watermelon'
        ]
        for fruit in fruits:
            ProduceType.objects.get_or_create(
                name=fruit,
                category=fruit_category,
                defaults={'description': f'Fresh {fruit}'}
            )
        
        # Legumes
        legume_category = Category.objects.get_or_create(
            name='Legumes',
            defaults={'description': 'Beans and legumes'}
        )[0]
        
        legumes = ['Sugar Beans', 'Cowpeas', 'Groundnuts', 'Soybeans']
        for legume in legumes:
            ProduceType.objects.get_or_create(
                name=legume,
                category=legume_category,
                defaults={'description': f'{legume}'}
            )
        
        # Create demo users
        self.stdout.write('Creating demo users...')
        
        # Demo farmer
        if not User.objects.filter(phone_number='+263771234567').exists():
            farmer_user = User.objects.create(
                full_name='Tendai Moyo',
                phone_number='+263771234567',
                email='farmer@example.com',
                user_type='farmer',
                district='Mashonaland East',
                ward='Ward 5',
                is_active=True,
                is_verified=True,
            )
            farmer_user.set_password('password123')
            farmer_user.save()
            
            FarmerProfile.objects.create(
                user=farmer_user,
                farm_name='Moyo Family Farm',
                farm_size=5.5,
                verified=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Created farmer: {farmer_user.phone_number}'))
        
        # Demo buyer
        if not User.objects.filter(phone_number='+263772345678').exists():
            buyer_user = User.objects.create(
                full_name='Rudo Ncube',
                phone_number='+263772345678',
                email='buyer@example.com',
                user_type='buyer',
                district='Harare',
                ward='Ward 12',
                is_active=True,
                is_verified=True,
            )
            buyer_user.set_password('password123')
            buyer_user.save()
            
            BuyerProfile.objects.create(
                user=buyer_user,
                organization_name='Fresh Foods Ltd',
                buyer_type='retailer',
            )
            self.stdout.write(self.style.SUCCESS(f'Created buyer: {buyer_user.phone_number}'))
        
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write('\nDemo accounts:')
        self.stdout.write('Farmer: +263771234567 / password123')
        self.stdout.write('Buyer: +263772345678 / password123')
