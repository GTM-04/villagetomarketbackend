"""
Seed script for categories and produce types.
Run: python seed_produce_types.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.listings.models import Category, ProduceType

# ---------------------------------------------------------------------------
# Category definitions: (name, icon, order)
# ---------------------------------------------------------------------------
category_defs = [
    ('Vegetables', '🥬', 1),
    ('Fruits',     '🍎', 2),
    ('Grains',     '🌾', 3),
    ('Livestock',  '🐄', 4),
    ('Poultry',    '🐔', 5),
    ('Dairy',      '🥛', 6),
]

print("Creating categories...")
categories = {}
for name, icon, order in category_defs:
    cat, created = Category.objects.get_or_create(
        name=name,
        defaults={'icon': icon, 'order': order}
    )
    # Update icon/order if category already existed
    if not created and (cat.icon != icon or cat.order != order):
        cat.icon = icon
        cat.order = order
        cat.save()
    categories[name.lower()] = cat
    status = '✓ Created' if created else '- Updated'
    print(f"  {status}: {icon} {name}")

# ---------------------------------------------------------------------------
# Produce type definitions: (name, category_key, common_units)
# ---------------------------------------------------------------------------
produce_data = [
    # Vegetables
    ('Tomatoes',   'vegetables', ['kg', 'crate', 'box']),
    ('Onions',     'vegetables', ['kg', 'bag', 'crate']),
    ('Butternut',  'vegetables', ['kg', 'unit', 'crate']),
    ('Cabbage',    'vegetables', ['head', 'kg', 'crate']),
    ('Spinach',    'vegetables', ['bunch', 'kg', 'crate']),
    ('Peppers',    'vegetables', ['kg', 'crate', 'box']),
    ('Carrots',    'vegetables', ['kg', 'bunch', 'bag']),
    ('Cucumbers',  'vegetables', ['kg', 'crate', 'box']),

    # Fruits
    ('Bananas',    'fruits', ['bunch', 'kg', 'crate']),
    ('Avocados',   'fruits', ['kg', 'crate', 'unit']),
    ('Oranges',    'fruits', ['kg', 'bag', 'crate']),
    ('Mangoes',    'fruits', ['kg', 'crate', 'unit']),
    ('Apples',     'fruits', ['kg', 'crate', 'bag']),

    # Grains
    ('White Maize',  'grains', ['kg', 'tonne', '50kg bag']),
    ('Yellow Maize', 'grains', ['kg', 'tonne', '50kg bag']),
    ('Wheat',        'grains', ['kg', 'tonne', '50kg bag']),
    ('Sorghum',      'grains', ['kg', 'tonne', '50kg bag']),
    ('Millet',       'grains', ['kg', 'tonne', '50kg bag']),

    # Livestock
    ('Cattle', 'livestock', ['head', 'kg live weight']),
    ('Goats',  'livestock', ['head', 'kg live weight']),
    ('Sheep',  'livestock', ['head', 'kg live weight']),
    ('Pigs',   'livestock', ['head', 'kg live weight']),

    # Poultry
    ('Chickens', 'poultry', ['bird', 'kg', 'dozen']),
    ('Eggs',     'poultry', ['dozen', 'tray', 'unit']),
    ('Ducks',    'poultry', ['bird', 'kg']),
    ('Turkeys',  'poultry', ['bird', 'kg']),

    # Dairy
    ('Milk',    'dairy', ['litre', '500ml', '1L']),
    ('Cheese',  'dairy', ['kg', 'unit', 'block']),
    ('Yogurt',  'dairy', ['litre', '500ml', '250ml']),
    ('Butter',  'dairy', ['kg', '250g', '500g']),
]

print("\nCreating produce types...")
created_count = 0
updated_count = 0
for name, cat_key, units in produce_data:
    pt, created = ProduceType.objects.get_or_create(
        name=name,
        defaults={
            'category': categories[cat_key],
            'common_units': units,
        }
    )
    if not created and pt.category != categories[cat_key]:
        pt.category = categories[cat_key]
        pt.common_units = units
        pt.save()
        updated_count += 1
        print(f"  ~ Updated:  {name}")
    elif created:
        created_count += 1
        print(f"  ✓ Created:  {name}")
    else:
        print(f"  - Exists:   {name}")

print(f"\n{'─'*40}")
print(f"  Categories:    {Category.objects.count()} total")
print(f"  Produce types: {ProduceType.objects.count()} total")
print(f"  Created: {created_count}  |  Updated: {updated_count}")
print(f"{'─'*40}")
