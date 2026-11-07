"""Abstract interfaces for Channel3 client, services, and integration adapters."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from server.app.services.discovery.models.locale import Channel3Locale
from server.app.services.discovery.models.offer import NormalizedOffer
from server.app.services.discovery.models.product import NormalizedProduct
from server.app.services.discovery.services.offer_selection import SpendingMandate
from server.app.services.discovery.services.product_service import ProductRefreshResult


class IChannel3Client(ABC):
    """Contract for low-level Channel3 API client implementations."""

    @abstractmethod
    async def search_products(
        self,
        query: str,
        filters: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        locale: Optional[Channel3Locale] = None,
    ) -> list[NormalizedProduct]:
        """Search products on Channel3."""
        ...

    @abstractmethod
    async def lookup_product_url(
        self,
        url: str,
        locale: Optional[Channel3Locale] = None,
    ) -> Optional[NormalizedProduct]:
        """Lookup product by merchant URL."""
        ...

    @abstractmethod
    async def get_product(
        self,
        product_id: str,
        locale: Optional[Channel3Locale] = None,
        variant_options: Optional[dict[str, str]] = None,
    ) -> NormalizedProduct:
        """Fetch canonical product and live offers by ID."""
        ...


class ISearchService(ABC):
    """Contract for search domain service."""

    @abstractmethod
    async def search(
        self,
        query: str,
        filters: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        locale: Optional[Channel3Locale] = None,
    ) -> list[NormalizedProduct]:
        """Execute natural language search."""
        ...


class ILookupService(ABC):
    """Contract for URL lookup domain service."""

    @abstractmethod
    async def lookup_url(
        self,
        url: str,
        locale: Optional[Channel3Locale] = None,
    ) -> NormalizedProduct:
        """Resolve merchant URL to canonical product."""
        ...


class IProductService(ABC):
    """Contract for product details and offer freshness verification."""

    @abstractmethod
    async def get_product_details(
        self,
        product_id: str,
        locale: Optional[Channel3Locale] = None,
        variant_options: Optional[dict[str, str]] = None,
    ) -> NormalizedProduct:
        """Fetch canonical product."""
        ...

    @abstractmethod
    async def refresh_product(
        self,
        product_id: str,
        selected_offer_key: str,
        baseline_offer: Optional[NormalizedOffer] = None,
        locale: Optional[Channel3Locale] = None,
        variant_options: Optional[dict[str, str]] = None,
    ) -> ProductRefreshResult:
        """Verify pre-checkout offer freshness and stability."""
        ...


class IOfferSelectionService(ABC):
    """Contract for deterministic offer selection against spending mandates."""

    @abstractmethod
    def select_offer(
        self,
        product: NormalizedProduct,
        offer_key: str,
        mandate: Optional[SpendingMandate] = None,
    ) -> NormalizedOffer:
        """Deterministically validate and select an offer."""
        ...
