"""
Quick script to seed produce types
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.listings.models import Category, ProduceType

# Create categories
categories = {
    'vegetables': Category.objects.get_or_create(name='Vegetables')[0],
    'fruits': Category.objects.get_or_create(name='Fruits')[0],
    'grains': Category.objects.get_or_create(name='Grains')[0],
    'legumes': Category.objects.get_or_create(name='Legumes')[0],
}

# Common Zimbabwean produce
produce_data = [
    # Vegetables
    ('Cabbage', 'vegetables'),
    ('Tomatoes', 'vegetables'),
    ('Onions', 'vegetables'),
    ('Rape (Leaf Vegetable)', 'vegetables'),
    ('Choumoellier', 'vegetables'),
    ('Butternut', 'vegetables'),
    ('Carrots', 'vegetables'),
    ('Potatoes', 'vegetables'),
    
    # Fruits
    ('Oranges', 'fruits'),
    ('Bananas', 'fruits'),
    ('Avocados', 'fruits'),
    ('Mangoes', 'fruits'),
    ('Guavas', 'fruits'),
    
    # Grains
    ('Maize', 'grains'),
    ('Wheat', 'grains'),
    ('Sorghum', 'grains'),
    
    # Legumes
    ('Groundnuts', 'legumes'),
    ('Sugar Beans', 'legumes'),
    ('Cowpeas', 'legumes'),
]

print("Creating produce types...")
for name, category_key in produce_data:
    produce_type, created = ProduceType.objects.get_or_create(
        name=name,
        defaults={'category': categories[category_key]}
    )
    if created:
        print(f"  ✓ Created: {name}")
    else:
        print(f"  - Already exists: {name}")

print(f"\nTotal produce types: {ProduceType.objects.count()}")
