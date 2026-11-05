"""Service for querying Channel3 product search."""

import logging
from typing import Any, Optional
from server.app.services.discovery.client.channel3_client import Channel3Client
from server.app.services.discovery.models.locale import Channel3Locale
from server.app.services.discovery.models.product import NormalizedProduct

logger = logging.getLogger("cartiq.channel3.search")


class SearchService:
    """Orchestrates natural-language product discovery queries against Channel3."""

    def __init__(self, client: Channel3Client):
        self.client = client

    async def search(
        self,
        query: str,
        filters: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        locale: Optional[Channel3Locale] = None,
    ) -> list[NormalizedProduct]:
        """Execute product search.

        Search results are intended for preliminary agent reasoning and catalog display.
        Authoritative checkout operations must refresh the selected offer before proposing.
        """
        logger.info("Initiating Channel3 search query: '%s' (limit=%s)", query, limit)
        return await self.client.search_products(
            query=query,
            filters=filters,
            limit=limit,
            locale=locale,
        )
