"""Automated API and unit tests for Priya Shopping Assistant Phase 1 MVP."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.orders import order_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_in_memory_state():
    """Ensure a clean in-memory state before and after each test."""
    order_service.reset_state()
    yield
    order_service.reset_state()


# ---------------------------------------------------------------------------
# 1. Health Endpoint Tests
# ---------------------------------------------------------------------------

def test_health_check():
    """Verify health endpoint reports demo mode and non-persistent storage."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["mode"] == "demo"
    assert data["catalogue_source"] == "in_memory"
    assert isinstance(data["orders_persistent"], bool)
    assert data["live_commerce_enabled"] is False



# ---------------------------------------------------------------------------
# 2. Product Search Tests
# ---------------------------------------------------------------------------

def test_product_search_success_default_limit():
    """Verify searching for 'glasses' returns matching products bounded by default limit 3."""
    response = client.post("/api/v1/products/search", json={"query": "glasses"})
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "glasses"
    assert data["demo_data"] is True
    assert data["currency"] == "INR"
    assert isinstance(data["matches"], list)
    assert len(data["matches"]) <= 3
    assert any("Glasses" in p["name"] for p in data["matches"])


def test_product_search_case_insensitive():
    """Verify product search matches irrespective of casing."""
    res_upper = client.post("/api/v1/products/search", json={"query": "PHONE"})
    res_lower = client.post("/api/v1/products/search", json={"query": "phone"})
    assert res_upper.status_code == 200
    assert res_lower.status_code == 200
    assert len(res_upper.json()["matches"]) == len(res_lower.json()["matches"])


def test_product_search_with_category_and_max_price():
    """Verify category and max price filters are properly applied."""
    response = client.post(
        "/api/v1/products/search",
        json={"query": "reading", "category": "Vision Care", "max_price": 360.0},
    )
    assert response.status_code == 200
    matches = response.json()["matches"]
    for product in matches:
        assert product["category"] == "Vision Care"
        assert product["price_inr"] <= 360.0


def test_product_search_empty_matches_no_fabrication():
    """Verify searching for an nonexistent product returns empty matches, never fabricated data."""
    response = client.post(
        "/api/v1/products/search",
        json={"query": "nonexistent_space_rocket_xyz"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["matches"] == []
    assert data["count"] == 0


def test_product_search_validation_empty_query():
    """Verify whitespace-only or empty query fails Pydantic validation."""
    response = client.post("/api/v1/products/search", json={"query": "   "})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 3. Product Detail Tests
# ---------------------------------------------------------------------------

def test_get_product_detail_success():
    """Verify retrieving a known product by ID."""
    response = client.get("/api/v1/products/prod_glass_20")
    assert response.status_code == 200
    product = response.json()
    assert product["id"] == "prod_glass_20"
    assert product["price_inr"] == 399.0
    assert product["category"] == "Vision Care"


def test_get_product_detail_not_found():
    """Verify 404 is returned for an unknown product ID."""
    response = client.get("/api/v1/products/unknown_product_999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


# ---------------------------------------------------------------------------
# 4. Order Preview Tests
# ---------------------------------------------------------------------------

def test_create_order_preview_success():
    """Verify backend calculates exact item line totals and grand total."""
    # prod_glass_20 is 399.0, prod_pill_box is 199.0
    # 2 * 399 + 1 * 199 = 798 + 199 = 997.0
    payload = {
        "items": [
            {"product_id": "prod_glass_20", "quantity": 2},
            {"product_id": "prod_pill_box", "quantity": 1},
        ]
    }
    response = client.post("/api/v1/orders/preview", json=payload)
    assert response.status_code == 200
    preview = response.json()
    assert preview["preview_id"].startswith("prev_")
    assert preview["status"] == "awaiting_confirmation"
    assert preview["demo_order"] is True
    assert preview["subtotal_inr"] == 997.0
    assert preview["total_inr"] == 997.0
    assert len(preview["items"]) == 2
    assert preview["items"][0]["line_total_inr"] == 798.0
    assert preview["items"][1]["line_total_inr"] == 199.0


def test_create_order_preview_unknown_product():
    """Verify 404 when preview includes an invalid product ID."""
    payload = {
        "items": [
            {"product_id": "invalid_prod_id", "quantity": 1},
        ]
    }
    response = client.post("/api/v1/orders/preview", json=payload)
    assert response.status_code == 404


def test_create_order_preview_invalid_quantity():
    """Verify 422 when item quantity is 0 or negative."""
    payload = {
        "items": [
            {"product_id": "prod_glass_20", "quantity": 0},
        ]
    }
    response = client.post("/api/v1/orders/preview", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 5. Order Confirmation & Duplicate Prevention Tests
# ---------------------------------------------------------------------------

def test_confirm_order_requires_explicit_confirmation():
    """Verify confirmed must be True to confirm an order."""
    # First create a valid preview
    prev_res = client.post(
        "/api/v1/orders/preview",
        json={"items": [{"product_id": "prod_glass_15", "quantity": 1}]},
    )
    preview_id = prev_res.json()["preview_id"]

    # Attempt to confirm with confirmed=False
    conf_res = client.post(
        "/api/v1/orders/confirm",
        json={"preview_id": preview_id, "confirmed": False},
    )
    assert conf_res.status_code == 400


def test_confirm_order_success_and_duplicate_prevention():
    """Verify confirming an order succeeds once, and a second confirmation triggers 409 Conflict."""
    prev_res = client.post(
        "/api/v1/orders/preview",
        json={"items": [{"product_id": "prod_phone_sos", "quantity": 1}]},
    )
    preview_id = prev_res.json()["preview_id"]

    # First confirmation -> Success
    confirm_res = client.post(
        "/api/v1/orders/confirm",
        json={"preview_id": preview_id, "confirmed": True},
    )
    assert confirm_res.status_code == 200
    order_data = confirm_res.json()
    assert order_data["order_id"].startswith("ord_")
    assert order_data["status"] == "confirmed_demo"
    assert order_data["demo_order"] is True
    assert order_data["total_inr"] == 1899.0

    # Second confirmation with same preview_id -> 409 Conflict
    duplicate_res = client.post(
        "/api/v1/orders/confirm",
        json={"preview_id": preview_id, "confirmed": True},
    )
    assert duplicate_res.status_code == 409


def test_confirm_order_unknown_preview():
    """Verify 404 for unknown preview_id."""
    response = client.post(
        "/api/v1/orders/confirm",
        json={"preview_id": "nonexistent_preview_id", "confirmed": True},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 6. Order Retrieval Tests
# ---------------------------------------------------------------------------

def test_get_order_by_id_success():
    """Verify fetching an existing confirmed demo order by ID."""
    prev_res = client.post(
        "/api/v1/orders/preview",
        json={"items": [{"product_id": "prod_walking_stick", "quantity": 1}]},
    )
    preview_id = prev_res.json()["preview_id"]

    confirm_res = client.post(
        "/api/v1/orders/confirm",
        json={"preview_id": preview_id, "confirmed": True},
    )
    order_id = confirm_res.json()["order_id"]

    # Fetch order
    fetch_res = client.get(f"/api/v1/orders/{order_id}")
    assert fetch_res.status_code == 200
    fetched_order = fetch_res.json()
    assert fetched_order["order_id"] == order_id
    assert fetched_order["total_inr"] == 650.0
    assert fetched_order["status"] == "confirmed_demo"


def test_get_order_by_id_not_found():
    """Verify 404 for non-existent order ID."""
    response = client.get("/api/v1/orders/unknown_order_12345")
    assert response.status_code == 404
