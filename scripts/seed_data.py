"""
Seed data script for Zimbabwe-specific data.
Run with: python scripts/seed_data.py
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.listings.models import Category, ProduceType
from django.db import transaction


ZIMBABWE_DISTRICTS = [
    # Harare Province
    'Harare', 'Chitungwiza', 'Epworth',
    # Bulawayo Province
    'Bulawayo',
    # Manicaland Province
    'Mutare', 'Rusape', 'Chipinge', 'Nyanga', 'Chimanimani', 'Makoni', 'Mutasa',
    # Mashonaland Central Province
    'Bindura', 'Guruve', 'Mount Darwin', 'Mazowe', 'Rushinga', 'Shamva', 'Mbire',
    # Mashonaland East Province
    'Marondera', 'Murehwa', 'Mutoko', 'Mudzi', 'Goromonzi', 'Seke', 'Uzumba-Maramba-Pfungwe',
    # Mashonaland West Province
    'Chinhoyi', 'Kariba', 'Hurungwe', 'Makonde', 'Chegutu', 'Zvimba', 'Mhondoro-Ngezi',
    # Masvingo Province
    'Masvingo', 'Chivi', 'Gutu', 'Zaka', 'Bikita', 'Mwenezi', 'Chiredzi',
    # Matabeleland North Province
    'Hwange', 'Binga', 'Victoria Falls', 'Lupane', 'Nkayi', 'Tsholotsho', 'Bubi',
    # Matabeleland South Province
    'Gwanda', 'Beitbridge', 'Plumtree', 'Insiza', 'Umzingwane', 'Mangwe', 'Matobo',
    # Midlands Province
    'Gweru', 'Kwekwe', 'Gokwe North', 'Gokwe South', 'Shurugwi', 'Zvishavane', 'Mberengwa', 'Chirumanzu'
]

CATEGORIES_DATA = {
    'Vegetables': {
        'icon': '🥬',
        'produce': [
            {'name': 'Tomatoes', 'units': ['kg', 'crates', 'boxes'], 'price_range': (20, 80)},
            {'name': 'Onions', 'units': ['kg', 'bags'], 'price_range': (30, 100)},
            {'name': 'Cabbage', 'units': ['kg', 'heads'], 'price_range': (15, 50)},
            {'name': 'Spinach', 'units': ['bundles', 'kg'], 'price_range': (10, 40)},
            {'name': 'Carrots', 'units': ['kg', 'bags'], 'price_range': (25, 70)},
            {'name': 'Peppers', 'units': ['kg', 'crates'], 'price_range': (35, 120)},
            {'name': 'Cucumbers', 'units': ['kg', 'crates'], 'price_range': (20, 65)},
            {'name': 'Butternut', 'units': ['kg', 'pieces'], 'price_range': (15, 50)},
            {'name': 'Rape (Covo)', 'units': ['bundles', 'kg'], 'price_range': (10, 35)},
            {'name': 'Lettuce', 'units': ['heads', 'kg'], 'price_range': (15, 45)},
        ]
    },
    'Grains & Cereals': {
        'icon': '🌾',
        'produce': [
            {'name': 'Maize (White)', 'units': ['kg', 'tonnes', 'bags'], 'price_range': (300, 600)},
            {'name': 'Maize (Yellow)', 'units': ['kg', 'tonnes', 'bags'], 'price_range': (280, 580)},
            {'name': 'Sorghum', 'units': ['kg', 'tonnes', 'bags'], 'price_range': (250, 500)},
            {'name': 'Pearl Millet', 'units': ['kg', 'bags'], 'price_range': (200, 450)},
            {'name': 'Wheat', 'units': ['kg', 'tonnes', 'bags'], 'price_range': (400, 800)},
            {'name': 'Rice', 'units': ['kg', 'bags'], 'price_range': (500, 1200)},
        ]
    },
    'Fruits': {
        'icon': '🍎',
        'produce': [
            {'name': 'Bananas', 'units': ['kg', 'bunches'], 'price_range': (30, 80)},
            {'name': 'Avocados', 'units': ['kg', 'pieces'], 'price_range': (40, 120)},
            {'name': 'Oranges', 'units': ['kg', 'crates'], 'price_range': (25, 70)},
            {'name': 'Mangoes', 'units': ['kg', 'crates'], 'price_range': (20, 60)},
            {'name': 'Apples', 'units': ['kg', 'boxes'], 'price_range': (50, 150)},
            {'name': 'Guavas', 'units': ['kg', 'buckets'], 'price_range': (15, 45)},
            {'name': 'Papaya', 'units': ['kg', 'pieces'], 'price_range': (20, 55)},
        ]
    },
    'Legumes': {
        'icon': '🫘',
        'produce': [
            {'name': 'Groundnuts', 'units': ['kg', 'bags'], 'price_range': (300, 700)},
            {'name': 'Sugar Beans', 'units': ['kg', 'bags'], 'price_range': (400, 900)},
            {'name': 'Cowpeas', 'units': ['kg', 'bags'], 'price_range': (350, 750)},
            {'name': 'Soybeans', 'units': ['kg', 'tonnes', 'bags'], 'price_range': (450, 950)},
            {'name': 'Bambara Nuts', 'units': ['kg', 'bags'], 'price_range': (300, 650)},
        ]
    },
    'Tubers & Roots': {
        'icon': '🥔',
        'produce': [
            {'name': 'Sweet Potatoes', 'units': ['kg', 'bags'], 'price_range': (25, 70)},
            {'name': 'Potatoes', 'units': ['kg', 'bags', 'pockets'], 'price_range': (35, 90)},
            {'name': 'Cassava', 'units': ['kg', 'bags'], 'price_range': (20, 60)},
            {'name': 'Yams', 'units': ['kg', 'bags'], 'price_range': (30, 80)},
        ]
    },
    'Livestock': {
        'icon': '🐄',
        'produce': [
            {'name': 'Cattle', 'units': ['head'], 'price_range': (300000, 800000)},
            {'name': 'Goats', 'units': ['head'], 'price_range': (50000, 150000)},
            {'name': 'Sheep', 'units': ['head'], 'price_range': (40000, 120000)},
            {'name': 'Pigs', 'units': ['head', 'kg'], 'price_range': (80000, 200000)},
            {'name': 'Rabbits', 'units': ['head'], 'price_range': (10000, 30000)},
        ]
    },
    'Poultry & Eggs': {
        'icon': '🐓',
        'produce': [
            {'name': 'Broiler Chickens', 'units': ['kg', 'birds'], 'price_range': (500, 1200)},
            {'name': 'Layer Chickens', 'units': ['birds'], 'price_range': (800, 1500)},
            {'name': 'Eggs', 'units': ['trays', 'crates'], 'price_range': (250, 450)},
            {'name': 'Ducks', 'units': ['birds'], 'price_range': (1000, 2500)},
            {'name': 'Guinea Fowl', 'units': ['birds'], 'price_range': (800, 1800)},
        ]
    },
    'Cash Crops': {
        'icon': '🍃',
        'produce': [
            {'name': 'Tobacco', 'units': ['kg', 'bales'], 'price_range': (800, 2000)},
            {'name': 'Cotton', 'units': ['kg', 'bales'], 'price_range': (600, 1500)},
            {'name': 'Sugarcane', 'units': ['tonnes'], 'price_range': (400, 800)},
            {'name': 'Coffee', 'units': ['kg'], 'price_range': (1500, 3500)},
            {'name': 'Tea', 'units': ['kg'], 'price_range': (800, 2000)},
        ]
    },
}


@transaction.atomic
def seed_categories():
    """Seed categories and produce types."""
    print("🌱 Seeding categories and produce types...")
    
    categories_created = 0
    produce_created = 0
    
    for cat_name, cat_data in CATEGORIES_DATA.items():
        # Create category
        category, created = Category.objects.get_or_create(
            name=cat_name,
            defaults={
                'icon': cat_data['icon'],
                'order': list(CATEGORIES_DATA.keys()).index(cat_name),
                'is_active': True
            }
        )
        
        if created:
            categories_created += 1
            print(f"  ✓ Created category: {cat_name}")
        
        # Create produce types
        for produce in cat_data['produce']:
            produce_type, created = ProduceType.objects.get_or_create(
                category=category,
                name=produce['name'],
                defaults={
                    'common_units': produce['units'],
                    'typical_price_min': produce['price_range'][0],
                    'typical_price_max': produce['price_range'][1],
                    'is_active': True
                }
            )
            
            if created:
                produce_created += 1
    
    print(f"\n✅ Created {categories_created} categories")
    print(f"✅ Created {produce_created} produce types")
    return categories_created, produce_created


def display_districts():
    """Display Zimbabwe districts."""
    print("\n📍 Zimbabwe Districts:")
    print(f"Total: {len(ZIMBABWE_DISTRICTS)} districts")
    print("\nList of districts:")
    for i, district in enumerate(sorted(ZIMBABWE_DISTRICTS), 1):
        print(f"  {i}. {district}")


def main():
    print("=" * 60)
    print("FROM VILLAGE TO MARKET - DATABASE SEEDING")
    print("=" * 60)
    print()
    
    # Seed categories
    cat_count, produce_count = seed_categories()
    
    # Display districts
    display_districts()
    
    print("\n" + "=" * 60)
    print("✨ SEEDING COMPLETE!")
    print("=" * 60)
    print(f"\nDatabase seeded with:")
    print(f"  • {cat_count} Categories")
    print(f"  • {produce_count} Produce Types")
    print(f"  • {len(ZIMBABWE_DISTRICTS)} Districts (reference)")
    print("\nNext steps:")
    print("  1. Run migrations: python manage.py migrate")
    print("  2. Create superuser: python manage.py createsuperuser")
    print("  3. Start server: python manage.py runserver")
    print()


if __name__ == '__main__':
    main()
