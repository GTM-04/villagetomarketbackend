"""
Reference data for categories and produce types.

Used to bootstrap the database in a predictable, idempotent way so the
frontend can always resolve produce names like "Cattle" to an existing
ProduceType row.
"""

from django.db import transaction

from apps.listings.models import Category, ProduceType


CATEGORIES_DATA = {
    "Vegetables": {
        "icon": "🥬",
        "order": 1,
        "produce": [
            {"name": "Tomatoes", "units": ["kg", "crates", "boxes"], "price_range": (20, 80)},
            {"name": "Onions", "units": ["kg", "bags"], "price_range": (30, 100)},
            {"name": "Cabbage", "units": ["kg", "heads"], "price_range": (15, 50)},
            {"name": "Spinach", "units": ["bundles", "kg"], "price_range": (10, 40)},
            {"name": "Carrots", "units": ["kg", "bags"], "price_range": (25, 70)},
            {"name": "Peppers", "units": ["kg", "crates"], "price_range": (35, 120)},
            {"name": "Cucumbers", "units": ["kg", "crates"], "price_range": (20, 65)},
            {"name": "Butternut", "units": ["kg", "pieces"], "price_range": (15, 50)},
            {"name": "Rape (Covo)", "units": ["bundles", "kg"], "price_range": (10, 35)},
            {"name": "Lettuce", "units": ["heads", "kg"], "price_range": (15, 45)},
        ],
    },
    "Grains & Cereals": {
        "icon": "🌾",
        "order": 2,
        "produce": [
            {"name": "Maize (White)", "units": ["kg", "tonnes", "bags"], "price_range": (300, 600)},
            {"name": "Maize (Yellow)", "units": ["kg", "tonnes", "bags"], "price_range": (280, 580)},
            {"name": "Sorghum", "units": ["kg", "tonnes", "bags"], "price_range": (250, 500)},
            {"name": "Pearl Millet", "units": ["kg", "bags"], "price_range": (200, 450)},
            {"name": "Wheat", "units": ["kg", "tonnes", "bags"], "price_range": (400, 800)},
            {"name": "Rice", "units": ["kg", "bags"], "price_range": (500, 1200)},
        ],
    },
    "Fruits": {
        "icon": "🍎",
        "order": 3,
        "produce": [
            {"name": "Bananas", "units": ["kg", "bunches"], "price_range": (30, 80)},
            {"name": "Avocados", "units": ["kg", "pieces"], "price_range": (40, 120)},
            {"name": "Oranges", "units": ["kg", "crates"], "price_range": (25, 70)},
            {"name": "Mangoes", "units": ["kg", "crates"], "price_range": (20, 60)},
            {"name": "Apples", "units": ["kg", "boxes"], "price_range": (50, 150)},
            {"name": "Guavas", "units": ["kg", "buckets"], "price_range": (15, 45)},
            {"name": "Papaya", "units": ["kg", "pieces"], "price_range": (20, 55)},
        ],
    },
    "Legumes": {
        "icon": "🫘",
        "order": 4,
        "produce": [
            {"name": "Groundnuts", "units": ["kg", "bags"], "price_range": (300, 700)},
            {"name": "Sugar Beans", "units": ["kg", "bags"], "price_range": (400, 900)},
            {"name": "Cowpeas", "units": ["kg", "bags"], "price_range": (350, 750)},
            {"name": "Soybeans", "units": ["kg", "tonnes", "bags"], "price_range": (450, 950)},
            {"name": "Bambara Nuts", "units": ["kg", "bags"], "price_range": (300, 650)},
        ],
    },
    "Tubers & Roots": {
        "icon": "🥔",
        "order": 5,
        "produce": [
            {"name": "Sweet Potatoes", "units": ["kg", "bags"], "price_range": (25, 70)},
            {"name": "Potatoes", "units": ["kg", "bags", "pockets"], "price_range": (35, 90)},
            {"name": "Cassava", "units": ["kg", "bags"], "price_range": (20, 60)},
            {"name": "Yams", "units": ["kg", "bags"], "price_range": (30, 80)},
        ],
    },
    "Livestock": {
        "icon": "🐄",
        "order": 6,
        "produce": [
            {"name": "Cattle", "units": ["head"], "price_range": (300000, 800000)},
            {"name": "Goats", "units": ["head"], "price_range": (50000, 150000)},
            {"name": "Sheep", "units": ["head"], "price_range": (40000, 120000)},
            {"name": "Pigs", "units": ["head", "kg"], "price_range": (80000, 200000)},
            {"name": "Rabbits", "units": ["head"], "price_range": (10000, 30000)},
        ],
    },
    "Poultry & Eggs": {
        "icon": "🐓",
        "order": 7,
        "produce": [
            {"name": "Broiler Chickens", "units": ["kg", "birds"], "price_range": (500, 1200)},
            {"name": "Layer Chickens", "units": ["birds"], "price_range": (800, 1500)},
            {"name": "Eggs", "units": ["trays", "crates"], "price_range": (250, 450)},
            {"name": "Ducks", "units": ["birds"], "price_range": (1000, 2500)},
            {"name": "Guinea Fowl", "units": ["birds"], "price_range": (800, 1800)},
        ],
    },
    "Cash Crops": {
        "icon": "🍃",
        "order": 8,
        "produce": [
            {"name": "Tobacco", "units": ["kg", "bales"], "price_range": (800, 2000)},
            {"name": "Cotton", "units": ["kg", "bales"], "price_range": (600, 1500)},
            {"name": "Sugarcane", "units": ["tonnes"], "price_range": (400, 800)},
            {"name": "Coffee", "units": ["kg"], "price_range": (1500, 3500)},
            {"name": "Tea", "units": ["kg"], "price_range": (800, 2000)},
        ],
    },
}


@transaction.atomic
def ensure_reference_data() -> tuple[int, int]:
    """Create missing categories and produce types without duplicating rows."""
    categories_created = 0
    produce_created = 0

    for category_name, category_data in CATEGORIES_DATA.items():
        category, created = Category.objects.get_or_create(
            name=category_name,
            defaults={
                "icon": category_data["icon"],
                "order": category_data["order"],
                "is_active": True,
            },
        )
        if created:
            categories_created += 1
        else:
            changed = False
            if category.icon != category_data["icon"]:
                category.icon = category_data["icon"]
                changed = True
            if category.order != category_data["order"]:
                category.order = category_data["order"]
                changed = True
            if not category.is_active:
                category.is_active = True
                changed = True
            if changed:
                category.save()

        for produce in category_data["produce"]:
            produce_type, created = ProduceType.objects.get_or_create(
                category=category,
                name=produce["name"],
                defaults={
                    "common_units": produce["units"],
                    "typical_price_min": produce["price_range"][0],
                    "typical_price_max": produce["price_range"][1],
                    "is_active": True,
                },
            )
            if created:
                produce_created += 1
            else:
                changed = False
                if list(produce_type.common_units or []) != produce["units"]:
                    produce_type.common_units = produce["units"]
                    changed = True
                min_price, max_price = produce["price_range"]
                if produce_type.typical_price_min != min_price:
                    produce_type.typical_price_min = min_price
                    changed = True
                if produce_type.typical_price_max != max_price:
                    produce_type.typical_price_max = max_price
                    changed = True
                if not produce_type.is_active:
                    produce_type.is_active = True
                    changed = True
                if changed:
                    produce_type.save()

    return categories_created, produce_created
