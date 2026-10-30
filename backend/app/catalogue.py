"""Fictional in-memory catalogue and search service for Priya Shopping Assistant Phase 1.

All catalogue items, prices, and stock numbers are explicit sample data for testing.
"""

from typing import Dict, List, Optional
from backend.app.schemas import Product

# Sample catalogue representing items typically helpful for Indian senior citizens
MOCK_PRODUCTS: List[Product] = [
    Product(
        id="prod_glass_20",
        name="Senior Reading Glasses (+2.0) with Anti-Glare Lens",
        name_hi="सीनियर रीडिंग चश्मा (+2.0) एंटी-ग्लेयर लेंस",
        category="Vision Care",
        price_inr=399.0,
        description="Lightweight reading glasses with soft silicone nose pads and blue-cut lens.",
        description_hi="हल्के वजन का पढ़ने का चश्मा, आरामदायक नाक पैड और ब्लू-कट लेंस के साथ।",
        in_stock=True,
        rating=4.7,
        unit="pair",
    ),
    Product(
        id="prod_glass_15",
        name="Senior Reading Glasses (+1.5) with Flexible Frame",
        name_hi="सीनियर रीडिंग चश्मा (+1.5) लचीला फ्रेम",
        category="Vision Care",
        price_inr=349.0,
        description="Durable flexible frame reading glasses with scratch-resistant lenses.",
        description_hi="टिकाऊ और लचीला फ्रेम, स्क्रैच-रेसिस्टेंट ग्लास के साथ।",
        in_stock=True,
        rating=4.6,
        unit="pair",
    ),
    Product(
        id="prod_phone_sos",
        name="EasyCare Senior Mobile Phone with Big Buttons & SOS Alert",
        name_hi="ईज़ीकेयर सीनियर मोबाइल फोन - बड़े बटन और एसओएस सुविधा",
        category="Electronics",
        price_inr=1899.0,
        description="High volume loudspeaker, dedicated one-touch emergency SOS key, and large Hindi/English keypad.",
        description_hi="तेज़ आवाज़ वाला स्पीकर, आपातकालीन SOS बटन, और बड़े अक्षरों वाला कीपैड।",
        in_stock=True,
        rating=4.8,
        unit="piece",
    ),
    Product(
        id="prod_shoes_ortho",
        name="ComfortStep Orthopedic Memory Foam Slip-on Shoes",
        name_hi="कम्फर्टस्टेप ऑर्थोपेडिक मेमोरी फोम जूते",
        category="Footwear",
        price_inr=1250.0,
        description="Extra wide anti-skid walking shoes without laces for easy wear and pain-free walking.",
        description_hi="बिना फीते वाले चौड़े आरामदायक जूते, फिसलन रोधी ग्रिप के साथ।",
        in_stock=True,
        rating=4.5,
        unit="pair",
    ),
    Product(
        id="prod_bp_monitor",
        name="SeniorPulse Digital BP Monitor with Hindi Voice Guidance",
        name_hi="सीनियरपल्स डिजिटल बीपी मशीन (हिंदी आवाज़ के साथ)",
        category="Health Devices",
        price_inr=1499.0,
        description="One-touch automatic blood pressure monitor with large LCD screen and Hindi voice readout.",
        description_hi="एक बटन से चलने वाली बीपी मशीन, बड़ी स्क्रीन और हिंदी में बोलकर बताने की सुविधा।",
        in_stock=True,
        rating=4.9,
        unit="unit",
    ),
    Product(
        id="prod_walking_stick",
        name="Quad-Base Adjustable Aluminium Walking Stick with LED Light",
        name_hi="चार पायों वाली मजबूत छड़ी (एलईडी लाइट के साथ)",
        category="Mobility",
        price_inr=650.0,
        description="Sturdy self-standing four-footed walking cane with built-in night flashlight and ergonomic grip.",
        description_hi="स्वयं खड़ी रहने वाली 4-पैर वाली छड़ी, रात के लिए टॉर्च और आरामदायक ग्रिप।",
        in_stock=True,
        rating=4.8,
        unit="piece",
    ),
    Product(
        id="prod_chyawanprash",
        name="Organic Sugar-Free Chyawanprash Immunity Booster (500g)",
        name_hi="ऑर्गेनिक शुगर-फ्री च्यवनप्राश (500 ग्राम)",
        category="Groceries & Wellness",
        price_inr=375.0,
        description="Traditional Ayurvedic immunity formula specially prepared for diabetic seniors with amla & herbs.",
        description_hi="शुगर-फ्री आयुर्वेदिक च्यवनप्राश, आंवला और दुर्लभ जड़ी-बूटियों से निर्मित।",
        in_stock=True,
        rating=4.6,
        unit="jar",
    ),
    Product(
        id="prod_cotton_kurta",
        name="Pure Breathable Khadi Cotton Kurta for Men (Large)",
        name_hi="शुद्ध खादी कॉटन कुर्ता (लार्ज साइज)",
        category="Clothing",
        price_inr=599.0,
        description="Loose-fitting, ultra-soft pure khadi cotton kurta with side pockets.",
        description_hi="ढीला और आरामदायक शुद्ध सूती खादी कुर्ता, दो साइड जेबों के साथ।",
        in_stock=True,
        rating=4.4,
        unit="piece",
    ),
    Product(
        id="prod_pill_box",
        name="7-Day Weekly Medicine Pill Organizer Box (Morning / Night)",
        name_hi="7 दिनों की दवा बॉक्स (सुबह और रात)",
        category="Health Devices",
        price_inr=199.0,
        description="Color-coded compartments with large day labels in Hindi and English.",
        description_hi="रंग-बिरंगे बड़े खाने, दिन के नाम हिंदी और अंग्रेजी में स्पष्ट लिखे हुए।",
        in_stock=True,
        rating=4.7,
        unit="piece",
    ),
]

_PRODUCTS_MAP: Dict[str, Product] = {p.id: p for p in MOCK_PRODUCTS}


def get_all_products() -> List[Product]:
    """Return all products in mock catalogue."""
    return list(MOCK_PRODUCTS)


def get_product_by_id(product_id: str) -> Optional[Product]:
    """Retrieve single product by ID or None if not found."""
    return _PRODUCTS_MAP.get(product_id)


def search_catalogue(
    query: str,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    limit: int = 3,
) -> List[Product]:
    """
    Search mock catalogue by query keywords across name, category, description, and Hindi fields.
    Applies optional category and max_price filters.
    Returns at most `limit` items. Returns empty list if no matches found.
    Never invents or fabricates products.
    """
    normalized_q = query.strip().lower()
    if not normalized_q:
        return []

    tokens = [t for t in normalized_q.split() if len(t) > 1]
    if not tokens:
        tokens = [normalized_q]

    results: List[Product] = []

    for product in MOCK_PRODUCTS:
        # Check category filter if provided
        if category and category.strip():
            if product.category.lower() != category.strip().lower():
                continue

        # Check max price filter if provided
        if max_price is not None and product.price_inr > max_price:
            continue

        # Search matching
        searchable_text = (
            f"{product.name} {product.name_hi} {product.category} "
            f"{product.description} {product.description_hi or ''}"
        ).lower()

        # Check if full query or any significant token matches
        matches_full = normalized_q in searchable_text
        matches_token = any(token in searchable_text for token in tokens)

        if matches_full or matches_token:
            results.append(product)

    # Sort: full query match first, then by rating descending
    def match_score(p: Product) -> tuple:
        full_match = normalized_q in p.name.lower() or normalized_q in p.name_hi
        return (1 if full_match else 0, p.rating or 0.0)

    results.sort(key=match_score, reverse=True)
    return results[:limit]
