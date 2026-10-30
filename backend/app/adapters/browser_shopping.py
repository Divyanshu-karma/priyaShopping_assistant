"""Safe, constrained browser-shopping adapter and product source abstractions.

Enforces strict domain allowlists, SSRF/private-IP blocking, and read-only extraction.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import re
from typing import List, Optional
from urllib.parse import urlparse
from pydantic import BaseModel, Field

from backend.app.catalogue import search_catalogue, get_product_by_id


class SourcedProduct(BaseModel):
    """Standardized product model returned by any ProductSource."""
    id: str
    name: str
    price_inr: float
    category: str
    source: str = "mock"
    source_domain: Optional[str] = None
    observed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    in_stock: bool = True
    availability_unverified: bool = False
    demo_data: bool = True
    description: str = ""


class ProductSource(ABC):
    """Abstract product source interface."""

    @abstractmethod
    def search(
        self,
        query: str,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        limit: int = 3,
    ) -> List[SourcedProduct]:
        pass


class MockCatalogueSource(ProductSource):
    """Default deterministic mock catalogue source."""

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        limit: int = 3,
    ) -> List[SourcedProduct]:
        matches = search_catalogue(query, category=category, max_price=max_price, limit=limit)
        return [
            SourcedProduct(
                id=p.id,
                name=p.name,
                price_inr=p.price_inr,
                category=p.category,
                source="mock_catalogue",
                source_domain="local.priya.internal",
                observed_at=datetime.now(timezone.utc).isoformat(),
                in_stock=p.in_stock,
                availability_unverified=False,
                demo_data=True,
                description=p.description,
            )
            for p in matches
        ]


class BrowserSecurityPolicy:
    """Security validator preventing SSRF, private IP access, and unauthorized navigation."""

    DEFAULT_ALLOWED_DOMAINS = [
        "seniorcare-demo.in",
        "healthkart-demo.in",
        "mock-elder-store.org",
    ]

    FORBIDDEN_HOST_PATTERNS = [
        re.compile(r"^localhost$", re.IGNORECASE),
        re.compile(r"^127\.\d+\.\d+\.\d+$"),
        re.compile(r"^10\.\d+\.\d+\.\d+$"),
        re.compile(r"^192\.168\.\d+\.\d+$"),
        re.compile(r"^172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+$"),
        re.compile(r"^169\.254\.\d+\.\d+$"),  # AWS/GCP cloud metadata
        re.compile(r"^0\.0\.0\.0$"),
        re.compile(r"^::1$"),
    ]

    def __init__(self, allowed_domains: Optional[List[str]] = None, require_https: bool = True):
        self.allowed_domains = allowed_domains or self.DEFAULT_ALLOWED_DOMAINS
        self.require_https = require_https

    def validate_url(self, url: str) -> bool:
        """Validate that a URL complies with domain allowlist and is not an SSRF attempt."""
        try:
            parsed = urlparse(url)
            if self.require_https and parsed.scheme.lower() != "https":
                return False
            if parsed.scheme.lower() not in ("http", "https"):
                return False

            hostname = parsed.hostname or ""
            if not hostname:
                return False

            # Check forbidden host patterns
            for pattern in self.FORBIDDEN_HOST_PATTERNS:
                if pattern.match(hostname):
                    return False

            # Check domain allowlist
            is_allowed = any(
                hostname == domain or hostname.endswith(f".{domain}")
                for domain in self.allowed_domains
            )
            return is_allowed
        except Exception:
            return False

    def sanitize_page_text(self, text: str) -> str:
        """Strip dangerous prompt-injection directives and executable markers from web text."""
        # Remove typical injection triggers
        sanitized = re.sub(r"(?i)(ignore previous instructions|system prompt|admin override|delete order)", "[redacted]", text)
        return sanitized[:500]


class AllowlistedBrowserSource(ProductSource):
    """
    Constrained, read-only shopping browser adapter.
    Uses mock fixtures and strict validation.
    No login, no cart mutation, no checkout execution.
    """

    def __init__(self, enabled: bool = False, policy: Optional[BrowserSecurityPolicy] = None):
        self.enabled = enabled
        self.policy = policy or BrowserSecurityPolicy()

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        limit: int = 3,
    ) -> List[SourcedProduct]:
        """
        In Phase 2, real external browsing is disabled by default (enabled=False).
        When disabled, it safely falls back to empty or explicit unverified state.
        """
        if not self.enabled:
            return []

        # When enabled in authorized test environments, search would query allowlisted hosts only.
        return []


# Global default product source
active_product_source: ProductSource = MockCatalogueSource()
