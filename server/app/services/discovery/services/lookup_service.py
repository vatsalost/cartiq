"""Service for resolving retailer URLs into canonical Channel3 products."""

import logging
from typing import Optional
from server.app.services.discovery.client.channel3_client import Channel3Client
from server.app.services.discovery.exceptions import Channel3NotFoundError
from server.app.services.discovery.models.locale import Channel3Locale
from server.app.services.discovery.models.product import NormalizedProduct
from server.app.services.discovery.validators.url_validator import URLValidator

logger = logging.getLogger("cartiq.channel3.lookup")


class LookupService:
    """Resolves arbitrary retailer product web links into canonical catalog products."""

    def __init__(self, client: Channel3Client):
        self.client = client

    async def lookup_url(
        self,
        url: str,
        locale: Optional[Channel3Locale] = None,
    ) -> NormalizedProduct:
        """Validate and resolve a retailer product URL.

        Args:
            url: External retailer link.
            locale: Optional regional/currency configuration.

        Returns:
            NormalizedProduct canonical representation.

        Raises:
            InvalidURLError: If the URL fails SSRF or schema validation.
            Channel3NotFoundError: If the product cannot be resolved by Channel3.
        """
        # Validate locally first before performing external request
        clean_url = URLValidator.validate_lookup_url(url)
        logger.info("Looking up validated retailer URL: %s", clean_url)

        product = await self.client.lookup_product_url(clean_url, locale=locale)
        if not product:
            raise Channel3NotFoundError(f"No canonical product could be resolved for URL: {clean_url}")

        return product
