"""
Pricing Recommendation Inference Module
========================================
Standalone module used by the FastAPI /pricing/recommend endpoint.

Load order
----------
1. Try joblib artefacts trained by the notebook
   (notebooks/saved_models/pricing_model.joblib + feature_scaler.joblib).
2. If artefacts are missing, fall back to a rule-based heuristic so the
   endpoint always responds — even before the notebook has been run.

Feature engineering here mirrors the notebook exactly so that inference
vectors are identical to what the model was trained on.
"""

from __future__ import annotations

import logging
import pathlib
from datetime import date, timedelta
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
_BASE_DIR   = pathlib.Path(__file__).resolve().parents[3]          # project root
_MODELS_DIR = _BASE_DIR / "notebooks" / "saved_models"
_MODEL_PATH  = _MODELS_DIR / "pricing_model.joblib"
_SCALER_PATH = _MODELS_DIR / "feature_scaler.joblib"

# ── Vocabularies (must match notebook Section 5) ──────────────────────────────
PRODUCE_TYPES = [
    "Tomatoes", "Maize", "Cabbage", "Onions",
    "Potatoes", "Beans", "Groundnuts", "Spinach",
]
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
    "fresh", "pesticide-free", "locally-grown",
    "non-gmo", "sun-dried", "hand-picked", "certified-organic",
]

# Build lookup dicts {value: index}
_CAT_FIELDS: dict[str, list[str]] = {
    "produce_type": PRODUCE_TYPES,
    "variety":      [v for vals in VARIETIES.values() for v in vals] + ["Other"],
    "grade":        GRADES,
    "unit":         UNITS,
    "district":     DISTRICTS,
}
_LE: dict[str, dict[str, int]] = {
    field: {val: idx for idx, val in enumerate(vocab)} | {"__unk__": len(vocab)}
    for field, vocab in _CAT_FIELDS.items()
}

# Image dimensions expected by the CNN extractor
IMG_SIZE   = (224, 224)
HIST_DIM   = 48    # colour-histogram fallback (16 bins × 3 channels)
CNN_DIM    = 1280  # MobileNetV2 global-avg-pool

# ── Lazy-loaded singletons ────────────────────────────────────────────────────
_model  = None
_scaler = None
_cnn    = None
_tf_ok  = False


def _try_load_tf() -> bool:
    """Attempt to import TensorFlow and build the MobileNetV2 extractor."""
    global _cnn, _tf_ok
    try:
        import tensorflow as tf
        from tensorflow.keras.applications import MobileNetV2
        _cnn  = MobileNetV2(weights="imagenet", include_top=False,
                            input_shape=(224, 224, 3), pooling="avg")
        _cnn.trainable = False
        _tf_ok = True
        logger.info("MobileNetV2 loaded for image feature extraction.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("TensorFlow unavailable — colour-histogram fallback (%s)", exc)
        _tf_ok = False
    return _tf_ok


def load_artefacts() -> bool:
    """
    Load the trained model + scaler from disk.
    Returns True if both artefacts were loaded successfully.
    """
    global _model, _scaler
    try:
        import joblib
        _model  = joblib.load(_MODEL_PATH)
        _scaler = joblib.load(_SCALER_PATH)
        logger.info("Pricing model loaded from %s", _MODEL_PATH)
        return True
    except FileNotFoundError:
        logger.warning(
            "Pricing model artefacts not found at %s. "
            "Run the notebook to train and save the model. "
            "Falling back to heuristic pricing.",
            _MODELS_DIR,
        )
        return False
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load pricing model: %s", exc)
        return False


# ── Feature engineering helpers ───────────────────────────────────────────────

def _tabular_dim() -> int:
    """Return the fixed length of a tabular feature vector."""
    return (
        sum(len(v) + 1 for v in _CAT_FIELDS.values())  # one-hot cats + unk
        + 3    # qty, min_order, days_since_harvest
        + 1    # is_organic
        + len(QUALITY_TAG_LIST)                         # multi-hot tags
    )


def encode_tabular(row: dict) -> np.ndarray:
    """Convert a listing dict → fixed-length float32 tabular feature vector."""
    parts: list[np.ndarray] = []

    for field, vocab in _CAT_FIELDS.items():
        vec = np.zeros(len(vocab) + 1, dtype=np.float32)
        val = row.get(field, "__unk__")
        idx = _LE[field].get(str(val), _LE[field]["__unk__"])
        vec[idx] = 1.0
        parts.append(vec)

    qty     = float(row.get("quantity_available", 100))
    min_ord = float(row.get("minimum_order") or qty * 0.1)

    harvest = row.get("harvest_date")
    if harvest is None:
        harvest_d = date.today() - timedelta(days=3)
    elif isinstance(harvest, date):
        harvest_d = harvest
    else:
        harvest_d = date.fromisoformat(str(harvest))
    days = max(0, (date.today() - harvest_d).days)

    parts.append(np.array([qty, min_ord, float(days)], dtype=np.float32))
    parts.append(np.array([float(bool(row.get("is_organic", False)))], dtype=np.float32))

    tags    = row.get("quality_tags") or []
    tag_vec = np.array([1.0 if t in tags else 0.0 for t in QUALITY_TAG_LIST],
                       dtype=np.float32)
    parts.append(tag_vec)

    return np.concatenate(parts)


def extract_image_features(img_array: np.ndarray) -> np.ndarray:
    """
    img_array : RGB uint8 (224, 224, 3)
    Returns a 1-D float32 feature vector.
    """
    if _tf_ok and _cnn is not None:
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
        from tensorflow.keras.preprocessing.image import img_to_array
        x = img_to_array(img_array)
        x = preprocess_input(x)
        x = np.expand_dims(x, 0)
        return _cnn.predict(x, verbose=0)[0]   # (1280,)

    # Colour-histogram fallback
    h_r = np.histogram(img_array[:, :, 0], bins=16, range=(0, 256))[0]
    h_g = np.histogram(img_array[:, :, 1], bins=16, range=(0, 256))[0]
    h_b = np.histogram(img_array[:, :, 2], bins=16, range=(0, 256))[0]
    feat = np.concatenate([h_r, h_g, h_b]).astype(np.float32)
    return feat / (feat.sum() + 1e-9)


def build_feature_vector(row: dict, img_array: np.ndarray) -> np.ndarray:
    """Concatenate tabular + image features → unified vector."""
    return np.concatenate([encode_tabular(row), extract_image_features(img_array)])


def _neutral_image(crop: str) -> np.ndarray:
    """Return a synthetic 224×224 image for when no photo is uploaded."""
    CROP_COLORS = {
        "Tomatoes": (200, 60, 50),   "Maize": (240, 210, 60),
        "Cabbage": (80, 160, 80),    "Onions": (200, 160, 80),
        "Potatoes": (180, 140, 80),  "Beans": (160, 100, 60),
        "Groundnuts": (200, 170, 100), "Spinach": (50, 130, 60),
    }
    rgb = CROP_COLORS.get(crop, (150, 150, 150))
    return np.full((224, 224, 3), rgb, dtype=np.uint8)


# ── Heuristic fallback ────────────────────────────────────────────────────────

_BASE_PRICES_ZWL = {
    "Tomatoes": 450, "Maize": 320, "Cabbage": 280,
    "Onions": 390,   "Potatoes": 350, "Beans": 580,
    "Groundnuts": 900, "Spinach": 200,
}
_GRADE_MULT = {
    "Export Quality": 1.35, "Premium": 1.25, "Grade A": 1.10,
    "Grade B": 0.95, "Grade C": 0.80, "Standard": 0.90,
}


def heuristic_recommend(row: dict, margin: float = 0.12) -> dict:
    """Rule-based price estimate used when the ML model is not yet available."""
    crop      = row.get("produce_type", "Tomatoes")
    grade     = row.get("grade", "Grade B")
    is_org    = bool(row.get("is_organic", False))
    tags      = row.get("quality_tags") or []

    harvest   = row.get("harvest_date")
    if isinstance(harvest, date):
        days = max(0, (date.today() - harvest).days)
    else:
        days = 3

    base    = _BASE_PRICES_ZWL.get(crop, 400)
    mult    = _GRADE_MULT.get(grade, 0.95)
    org     = 1.15 if is_org else 1.0
    fresh   = 1.0 + max(0, (7 - days) / 7) * 0.10
    tag_bon = 1.0 + 0.02 * min(len(tags), 3)
    price   = round(base * mult * org * fresh * tag_bon, 2)

    return {
        "recommended_price": price,
        "price_min":  round(price * (1 - margin), 2),
        "price_max":  round(price * (1 + margin), 2),
        "currency":   "ZWL",
        "unit":       row.get("unit", "kg"),
        "model_used": "heuristic",
        "confidence_margin": f"±{int(margin * 100)}%",
        "note": (
            "This is a rule-based estimate. "
            "Run notebooks/pricing_recommendation_model.ipynb to train "
            "the ML model for higher accuracy."
        ),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def recommend_price(
    listing_fields: dict,
    image: Optional[np.ndarray] = None,
    confidence_margin: float = 0.10,
) -> dict:
    """
    Return a price recommendation for a crop listing.

    Parameters
    ----------
    listing_fields    : dict with produce_type, variety, grade, unit, district,
                        is_organic, quality_tags, quantity_available,
                        minimum_order, harvest_date
    image             : RGB (224,224,3) uint8 numpy array or None
    confidence_margin : fractional half-width of the price band

    Returns
    -------
    dict: recommended_price, price_min, price_max, currency, unit,
          model_used, confidence_margin[, note]
    """
    if _model is None or _scaler is None:
        return heuristic_recommend(listing_fields, margin=confidence_margin)

    crop     = listing_fields.get("produce_type", "Tomatoes")
    img_arr  = image if image is not None else _neutral_image(crop)

    feat = build_feature_vector(listing_fields, img_arr).reshape(1, -1)
    try:
        feat_scaled = _scaler.transform(feat)
        raw_price   = float(_model.predict(feat_scaled)[0])
    except Exception as exc:  # noqa: BLE001
        logger.error("Model inference failed: %s — falling back to heuristic.", exc)
        return heuristic_recommend(listing_fields, margin=confidence_margin)

    margin = raw_price * confidence_margin
    return {
        "recommended_price": round(raw_price, 2),
        "price_min":         round(raw_price - margin, 2),
        "price_max":         round(raw_price + margin, 2),
        "currency":          "ZWL",
        "unit":              listing_fields.get("unit", "kg"),
        "model_used":        type(_model).__name__,
        "confidence_margin": f"±{int(confidence_margin * 100)}%",
    }


# ── Initialise on import ──────────────────────────────────────────────────────
_try_load_tf()
load_artefacts()
