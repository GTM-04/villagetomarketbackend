"""
Standalone script to train the pricing recommendation model and save artifacts.
Run from the project root:
    python scripts/train_pricing_model.py
Outputs:
    notebooks/saved_models/pricing_model.joblib
    notebooks/saved_models/feature_scaler.joblib
"""
import warnings
warnings.filterwarnings("ignore")

import os
import sys
import random
import json
import pathlib
from datetime import date, timedelta

import numpy as np

# ── TensorFlow (optional) ──────────────────────────────────────────────────────
TF_AVAILABLE = False
base_model = None
try:
    import tensorflow as tf
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
    from tensorflow.keras.preprocessing.image import img_to_array
    base_model = MobileNetV2(weights="imagenet", include_top=False,
                             input_shape=(224, 224, 3), pooling="avg")
    base_model.trainable = False
    TF_AVAILABLE = True
    print(f"TensorFlow {tf.__version__} — MobileNetV2 feature extractor ready")
except Exception as exc:
    print(f"TensorFlow unavailable ({exc}) — using colour-histogram fallback (48-dim)")

EMBED_DIM = 1280 if TF_AVAILABLE else 48

# ── scikit-learn / xgboost ────────────────────────────────────────────────────
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
    print("XGBoost available")
except ImportError:
    XGB_AVAILABLE = False
    print("XGBoost not found — using GradientBoostingRegressor")

import joblib
from PIL import Image, ImageDraw, ImageFilter

# ── Vocabularies ───────────────────────────────────────────────────────────────
IMG_SIZE = (224, 224)
CROP_COLORS = {
    "Tomatoes":   (200, 60,  50),
    "Maize":      (240, 210, 60),
    "Cabbage":    (80,  160, 80),
    "Onions":     (200, 160, 80),
    "Potatoes":   (180, 140, 80),
    "Beans":      (160, 100, 60),
    "Groundnuts": (200, 170, 100),
    "Spinach":    (50,  130, 60),
}
PRODUCE_TYPES = list(CROP_COLORS.keys())
VARIETIES = {
    "Tomatoes":   ["Roma", "Cherry", "Beefsteak", "Plum"],
    "Maize":      ["Yellow", "White", "Hybrid", "Open-Pollinated"],
    "Cabbage":    ["Green", "Red", "Savoy", "Napa"],
    "Onions":     ["Red", "White", "Brown", "Spring"],
    "Potatoes":   ["Irish", "Sweet", "Red", "Yellow"],
    "Beans":      ["Sugar", "Kidney", "Black-eyed", "Soya"],
    "Groundnuts": ["Virginia", "Valencia", "Spanish"],
    "Spinach":    ["English", "Baby", "Creole"],
}
GRADES    = ["Grade A", "Grade B", "Grade C", "Export Quality", "Premium", "Standard"]
UNITS     = ["kg", "g", "tonnes", "bags", "crates", "trays", "bundles", "pieces"]
DISTRICTS = [
    "Harare", "Bulawayo", "Manicaland", "Masvingo",
    "Midlands", "Mashonaland East", "Mashonaland West",
    "Mashonaland Central", "Matabeleland North", "Matabeleland South",
]
QUALITY_TAG_LIST = [
    "fresh", "pesticide-free", "locally-grown", "non-gmo",
    "sun-dried", "hand-picked", "certified-organic",
]
_CAT_FIELDS = {
    "produce_type": PRODUCE_TYPES,
    "variety":      [v for vals in VARIETIES.values() for v in vals] + ["Other"],
    "grade":        GRADES,
    "unit":         UNITS,
    "district":     DISTRICTS,
}
le_encoders = {
    field: {val: idx for idx, val in enumerate(vocab)} | {"__unk__": len(vocab)}
    for field, vocab in _CAT_FIELDS.items()
}

BASE_PRICES = {
    "Tomatoes": 450, "Maize": 320, "Cabbage": 280,
    "Onions": 390,   "Potatoes": 350, "Beans": 580,
    "Groundnuts": 900, "Spinach": 200,
}
GRADE_MULT = {
    "Export Quality": 1.35, "Premium": 1.25, "Grade A": 1.10,
    "Grade B": 0.95,        "Grade C": 0.80, "Standard": 0.90,
}


# ── Image helpers ──────────────────────────────────────────────────────────────
def generate_synthetic_crop_image(crop_type: str, quality_score: float) -> np.ndarray:
    base_rgb = CROP_COLORS.get(crop_type, (150, 150, 150))
    brightness = int(quality_score * 60)
    r = min(255, base_rgb[0] + brightness)
    g = min(255, base_rgb[1] + brightness)
    b = min(255, base_rgb[2] + 20)
    img = Image.new("RGB", IMG_SIZE, color=(r, g, b))
    draw = ImageDraw.Draw(img)
    rng = random.Random(hash(crop_type))
    for _ in range(12):
        x = rng.randint(20, 200); y = rng.randint(20, 200)
        radius = rng.randint(15, 40)
        shade = (max(0, r - 30), max(0, g - 30), max(0, b - 20))
        draw.ellipse([x, y, x + radius, y + radius], fill=shade)
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    return np.array(img)


def extract_image_features(img_array: np.ndarray) -> np.ndarray:
    """Single-image fallback (histogram only).  Batch path used during training."""
    h_r = np.histogram(img_array[:, :, 0], bins=16, range=(0, 256))[0]
    h_g = np.histogram(img_array[:, :, 1], bins=16, range=(0, 256))[0]
    h_b = np.histogram(img_array[:, :, 2], bins=16, range=(0, 256))[0]
    feat = np.concatenate([h_r, h_g, h_b]).astype(np.float32)
    return feat / (feat.sum() + 1e-9)


def extract_image_features_batch(images: list) -> np.ndarray:
    """
    Extract features for a list of (224,224,3) uint8 arrays.
    Uses MobileNetV2 in a single batched predict() call when available,
    otherwise uses the colour-histogram fallback.
    """
    if TF_AVAILABLE and base_model is not None:
        batch = np.array([img_to_array(img) for img in images], dtype=np.float32)
        batch = preprocess_input(batch)  # in-place normalisation
        return base_model.predict(batch, batch_size=64, verbose=1)
    # histogram fallback for all images
    return np.array([extract_image_features(img) for img in images])


# ── Tabular encoding ───────────────────────────────────────────────────────────
def encode_tabular_features(row: dict) -> np.ndarray:
    parts = []
    for field, vocab in _CAT_FIELDS.items():
        vec = np.zeros(len(vocab) + 1, dtype=np.float32)
        val = row.get(field, "__unk__")
        idx = le_encoders[field].get(val, le_encoders[field]["__unk__"])
        vec[idx] = 1.0
        parts.append(vec)
    qty = float(row.get("quantity_available", 0))
    min_ord = float(row.get("minimum_order", qty * 0.1) or qty * 0.1)
    harvest = row.get("harvest_date", date.today())
    if isinstance(harvest, str):
        harvest = date.fromisoformat(harvest)
    days = max(0, (date.today() - harvest).days)
    parts.append(np.array([qty, min_ord, float(days)], dtype=np.float32))
    parts.append(np.array([float(bool(row.get("is_organic", False)))], dtype=np.float32))
    tags = row.get("quality_tags", [])
    tag_vec = np.array([1.0 if t in tags else 0.0 for t in QUALITY_TAG_LIST], dtype=np.float32)
    parts.append(tag_vec)
    return np.concatenate(parts)


def build_full_feature_vector(row: dict, img_array: np.ndarray) -> np.ndarray:
    return np.concatenate([encode_tabular_features(row), extract_image_features(img_array)])


# ── Generate synthetic dataset ─────────────────────────────────────────────────
def generate_dataset(n: int = 800):
    random.seed(42)
    np.random.seed(42)
    records, images, prices = [], [], []
    for _ in range(n):
        crop      = random.choice(PRODUCE_TYPES)
        variety   = random.choice(VARIETIES.get(crop, ["Standard"]))
        grade     = random.choice(GRADES)
        unit      = random.choice(["kg", "bags", "crates"])
        district  = random.choice(DISTRICTS)
        is_org    = random.random() < 0.25
        qty       = round(random.uniform(20, 2000), 1)
        min_ord   = round(qty * random.uniform(0.05, 0.3), 1)
        days_harv = random.randint(0, 14)
        harvest_d = date.today() - timedelta(days=days_harv)
        tags      = random.sample(QUALITY_TAG_LIST, k=random.randint(0, 3))
        quality_s = random.uniform(0.4, 1.0)

        base  = BASE_PRICES[crop]
        mult  = GRADE_MULT[grade]
        org   = 1.15 if is_org else 1.0
        fresh = 1.0 + max(0, (7 - days_harv) / 7) * 0.10
        vis   = 0.90 + quality_s * 0.20
        noise = np.random.normal(1.0, 0.08)
        price = round(base * mult * org * fresh * vis * noise, 2)

        records.append({
            "produce_type": crop, "variety": variety, "grade": grade,
            "unit": unit, "district": district, "is_organic": is_org,
            "quality_tags": tags, "quantity_available": qty,
            "minimum_order": min_ord, "harvest_date": harvest_d,
        })
        images.append(generate_synthetic_crop_image(crop, quality_s))
        prices.append(price)
    return records, images, prices


# ── Main training routine ──────────────────────────────────────────────────────
def main():
    print("\n" + "=" * 60)
    print("  Village-to-Market — Pricing Model Training")
    print("=" * 60)

    print("\n[1/5] Generating synthetic dataset (800 samples) …")
    records, images, prices = generate_dataset(800)
    print(f"      Price range: ZWL {min(prices):.0f} - {max(prices):.0f}")

    print("\n[2/5] Extracting feature vectors …")
    tab_features = np.array([encode_tabular_features(row) for row in records])
    img_features = extract_image_features_batch(images)
    X_all = np.concatenate([tab_features, img_features], axis=1)
    y_all = np.array(prices)
    print(f"      Feature matrix: {X_all.shape}  (tabular {tab_features.shape[1]} + image {img_features.shape[1]})")

    print("\n[3/5] Scaling features …")
    scaler = MinMaxScaler()
    X_all  = scaler.fit_transform(X_all)

    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y_all, test_size=0.20, random_state=42
    )
    print(f"      Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")

    print("\n[4/5] Training models …")
    models = {}
    if XGB_AVAILABLE:
        # XGBoost is fast on high-dim data with n_jobs=-1
        models["XGBoost"] = xgb.XGBRegressor(
            n_estimators=300, max_depth=6, learning_rate=0.07,
            subsample=0.85, colsample_bytree=0.8,
            random_state=42, verbosity=0, n_jobs=-1,
        )
    else:
        # GradientBoosting only when XGBoost is absent; fewer trees on high-dim data
        models["GradientBoosting"] = GradientBoostingRegressor(
            n_estimators=80, max_depth=4, learning_rate=0.10,
            subsample=0.85, random_state=42,
        )
    # RandomForest is always included as baseline (parallelised)
    models["RandomForest"] = RandomForestRegressor(
        n_estimators=200, max_depth=12, random_state=42, n_jobs=-1,
    )

    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        mae  = mean_absolute_error(y_test, y_pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        r2   = r2_score(y_test, y_pred)
        results[name] = {"model": model, "MAE": mae, "RMSE": rmse, "R2": r2}
        print(f"      {name:<22}  MAE={mae:6.1f}  RMSE={rmse:6.1f}  R2={r2:.4f}")

    best_name  = max(results, key=lambda k: results[k]["R2"])
    best_model = results[best_name]["model"]
    print(f"\n      >> Best model: {best_name}  (R2 = {results[best_name]['R2']:.4f})")

    print("\n[5/5] Saving artifacts …")
    models_dir = pathlib.Path(__file__).resolve().parents[1] / "notebooks" / "saved_models"
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path  = models_dir / "pricing_model.joblib"
    scaler_path = models_dir / "feature_scaler.joblib"
    joblib.dump(best_model, model_path)
    joblib.dump(scaler,     scaler_path)
    print(f"      Model  -> {model_path}")
    print(f"      Scaler -> {scaler_path}")
    print("\nDone. Restart daphne to load the trained model.\n")


if __name__ == "__main__":
    main()
