"""High-level typed Channel3 API Client."""

from typing import Any, Optional
from server.app.services.discovery.client.http_client import Channel3HTTPClient
from server.app.services.discovery.config import Channel3Config
from server.app.services.discovery.constants import (
    DEFAULT_LIMIT,
    LOOKUP_ENDPOINT,
    MAX_LIMIT,
    MIN_LIMIT,
    PRODUCTS_ENDPOINT,
    SEARCH_ENDPOINT,
)
from server.app.services.discovery.exceptions import Channel3ValidationError
from server.app.services.discovery.models.locale import Channel3Locale
from server.app.services.discovery.models.product import NormalizedProduct
from server.app.services.discovery.normalizers.product_normalizer import ProductNormalizer
from server.app.services.discovery.validators.response_validator import ResponseValidator
from server.app.services.discovery.validators.url_validator import URLValidator


class Channel3Client:
    """Server-side client for executing Channel3 search, lookup, and product detail requests."""

    def __init__(
        self,
        config: Optional[Channel3Config] = None,
        http_client: Optional[Channel3HTTPClient] = None,
    ):
        self.config = config or Channel3Config()
        self._http = http_client or Channel3HTTPClient(config=self.config)
        self._owns_http = http_client is None

    async def aclose(self) -> None:
        """Release underlying HTTP client connections."""
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> "Channel3Client":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.aclose()

    async def search_products(
        self,
        query: str,
        filters: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        locale: Optional[Channel3Locale] = None,
    ) -> list[NormalizedProduct]:
        """Execute a natural-language search query on Channel3 catalog.

        Endpoint: POST /v1/search

        Args:
            query: Natural language product search string (e.g. "ergonomic desk chair").
            filters: Optional attribute filters (e.g. {"brand_ids": ["..."], "colors": ["..."]}).
            limit: Maximum number of products to return (bounded between 1 and MAX_LIMIT).
            locale: Optional regional/currency configuration.

        Returns:
            List of normalized product models with separate retailer offers.
        """
        if not query or not query.strip():
            raise Channel3ValidationError("Search query cannot be empty.")

        # Determine and bound limit
        req_limit = limit if limit is not None else self.config.default_limit
        req_limit = max(MIN_LIMIT, min(req_limit, self.config.max_limit))

        payload: dict[str, Any] = {
            "query": query.strip(),
            "limit": req_limit,
        }
        if filters:
            payload["filters"] = filters

        params: dict[str, str] = {}
        if locale:
            params["country"] = locale.country
            params["language"] = locale.language
            params["currency"] = locale.currency

        raw_resp = await self._http.request(
            method="POST",
            path=SEARCH_ENDPOINT,
            json=payload,
            params=params if params else None,
        )

        raw_products = raw_resp.get("products") or []
        if not isinstance(raw_products, list):
            return []

        products: list[NormalizedProduct] = []
        for raw_item in raw_products:
            if isinstance(raw_item, dict):
                try:
                    product = ProductNormalizer.normalize_product(raw_item)
                    products.append(product)
                except Channel3ValidationError:
                    # Skip malformed catalog item safely
                    continue

        return products

    async def lookup_product_url(
        self,
        url: str,
        locale: Optional[Channel3Locale] = None,
    ) -> Optional[NormalizedProduct]:
        """Resolve an external merchant product URL into a canonical Channel3 product.

        Endpoint: POST /v1/lookup

        Args:
            url: Retailer product web link.
            locale: Optional regional/currency configuration.

        Returns:
            NormalizedProduct or None if no match found.

        Raises:
            InvalidURLError: If URL fails security validation or SSRF checks.
            Channel3Error: If provider communication fails.
        """
        sanitized_url = URLValidator.validate_lookup_url(url)

        payload: dict[str, Any] = {
            "url": sanitized_url,
        }

        params: dict[str, str] = {}
        if locale:
            params["country"] = locale.country
            params["language"] = locale.language
            params["currency"] = locale.currency

        raw_resp = await self._http.request(
            method="POST",
            path=LOOKUP_ENDPOINT,
            json=payload,
            params=params if params else None,
        )

        # Response typically wraps result in {"product": {...}}
        if not raw_resp:
            return None

        return ProductNormalizer.normalize_product(raw_resp)

    async def get_product(
        self,
        product_id: str,
        locale: Optional[Channel3Locale] = None,
        variant_options: Optional[dict[str, str]] = None,
    ) -> NormalizedProduct:
        """Fetch canonical product details and fresh retailer offers by Product ID.

        Endpoint: GET /v1/products/{product_id}

        Args:
            product_id: Canonical Channel3 product identifier.
            locale: Optional regional/currency configuration.
            variant_options: Optional variant selectors (e.g. {"Color": "Blue", "Size": "L"}).

        Returns:
            Fresh NormalizedProduct with current offers and availability.

        Raises:
            Channel3NotFoundError: If the product does not exist.
            Channel3ValidationError: If product_id is invalid.
        """
        clean_id = ResponseValidator.validate_product_id(product_id)
        path = f"{PRODUCTS_ENDPOINT}/{clean_id}"

        params: dict[str, str] = {}
        if locale:
            params["country"] = locale.country
            params["language"] = locale.language
            params["currency"] = locale.currency

        if variant_options:
            for opt_key, opt_val in variant_options.items():
                params[f"option_{opt_key}"] = str(opt_val)

        raw_resp = await self._http.request(
            method="GET",
            path=path,
            params=params if params else None,
        )

        return ProductNormalizer.normalize_product(raw_resp)
