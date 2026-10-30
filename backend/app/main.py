"""FastAPI application for Priya Shopping Assistant Phase 1.

Provides local REST API endpoints for mock catalogue search, product detail,
order preview, and explicit demo order confirmation, plus serving the static demo UI.
"""

from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.schemas import (
    HealthResponse,
    Product,
    ProductSearchRequest,
    ProductSearchResponse,
    OrderPreviewRequest,
    OrderPreviewResponse,
    OrderConfirmRequest,
    OrderConfirmResponse,
    OrderResponse,
    ErrorDetail,
)
from backend.app.catalogue import search_catalogue, get_product_by_id
from backend.app.services.orders import (
    order_service,
    OrderError,
    ProductNotFoundError,
    PreviewNotFoundError,
    PreviewAlreadyConfirmedError,
    ConfirmationRequiredError,
)

from backend.app.db.init_db import init_db
from contextlib import asynccontextmanager
from backend.app.db.session import get_database_mode
from backend.app.routers import voice_tools, family_dashboard

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure database tables and initial fixtures are initialized on startup."""
    init_db()
    yield


app = FastAPI(
    title="Priya Shopping Assistant API",
    version="2.0.0",
    description=(
        "Priya — Voice-first shopping assistant for Indian seniors. "
        "Includes mock catalogue, persistent orders & governance, "
        "authenticated Bolna voice tools, and authenticated family dashboard."
    ),
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# Custom exception handler for OrderError hierarchy
@app.exception_handler(OrderError)
async def order_error_handler(request: Request, exc: OrderError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )

# Include Phase 2 Routers
app.include_router(voice_tools.router)
app.include_router(family_dashboard.router)


# ---------------------------------------------------------------------------
# API v1 Endpoints
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Lightweight system health check",
)
def get_health() -> HealthResponse:
    """Return system status, reporting persistent storage and enabled subsystems."""
    db_mode = get_database_mode()
    return HealthResponse(
        status="ok",
        mode="demo",
        catalogue_source="in_memory",
        orders_persistent=db_mode.get("persistent", True),
        live_commerce_enabled=False,
        database_mode=db_mode,
        voice_tools_enabled=True,
        family_dashboard_enabled=True,
    )



@app.post(
    "/api/v1/products/search",
    response_model=ProductSearchResponse,
    tags=["Catalogue"],
    summary="Search mock catalogue products",
)
def search_products(body: ProductSearchRequest) -> ProductSearchResponse:
    """
    Search mock products matching query keywords, optional category, and max_price filters.
    Returns at most limit items (default 3). Never fabricates items.
    """
    matches = search_catalogue(
        query=body.query,
        category=body.category,
        max_price=body.max_price,
        limit=body.limit or 3,
    )
    return ProductSearchResponse(
        query=body.query,
        matches=matches,
        count=len(matches),
        currency="INR",
        demo_data=True,
    )


@app.get(
    "/api/v1/products/{product_id}",
    response_model=Product,
    responses={404: {"model": ErrorDetail, "description": "Product not found"}},
    tags=["Catalogue"],
    summary="Retrieve product detail by ID",
)
def get_product(product_id: str) -> Product:
    """Retrieve details for a single product ID. Returns 404 if not found."""
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' was not found in mock catalogue.",
        )
    return product


@app.post(
    "/api/v1/orders/preview",
    response_model=OrderPreviewResponse,
    responses={
        400: {"model": ErrorDetail, "description": "Invalid item or quantity"},
        404: {"model": ErrorDetail, "description": "Product not found"},
    },
    tags=["Orders"],
    summary="Create backend-calculated order preview",
)
def create_order_preview(body: OrderPreviewRequest) -> OrderPreviewResponse:
    """
    Accept one or more product IDs and quantities, calculate authoritative totals
    on the backend, and return an awaiting-confirmation demo preview.
    """
    return order_service.create_preview(body.items)


@app.post(
    "/api/v1/orders/confirm",
    response_model=OrderConfirmResponse,
    responses={
        400: {"model": ErrorDetail, "description": "Confirmation missing or false"},
        404: {"model": ErrorDetail, "description": "Preview not found"},
        409: {"model": ErrorDetail, "description": "Preview already confirmed"},
    },
    tags=["Orders"],
    summary="Explicitly confirm a pending demo order preview",
)
def confirm_order(body: OrderConfirmRequest) -> OrderConfirmResponse:
    """
    Explicitly confirm a demo preview. Requires confirmed=true.
    Prevents duplicate confirmations on the same preview.
    """
    return order_service.confirm_order(
        preview_id=body.preview_id,
        confirmed=body.confirmed,
    )


@app.get(
    "/api/v1/orders/{order_id}",
    response_model=OrderResponse,
    responses={404: {"model": ErrorDetail, "description": "Order not found"}},
    tags=["Orders"],
    summary="Retrieve a confirmed in-memory demo order",
)
def get_order(order_id: str) -> OrderResponse:
    """Retrieve demo order details. In-memory only; not persisted across restarts."""
    order = order_service.get_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID '{order_id}' was not found in demo session.",
        )
    return order


# ---------------------------------------------------------------------------
# Static frontend mounting and root route
# ---------------------------------------------------------------------------

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    """Serve single-page frontend application."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Frontend UI file index.html not found."},
        )
    return FileResponse(str(index_file))


@app.get("/dashboard", include_in_schema=False)
def serve_dashboard():
    """Serve family oversight dashboard."""
    dash_file = STATIC_DIR / "dashboard.html"
    if not dash_file.exists():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Dashboard UI file dashboard.html not found."},
        )
    return FileResponse(str(dash_file))

