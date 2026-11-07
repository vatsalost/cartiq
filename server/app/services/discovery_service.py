"""Discovery Service (B6) integrating Channel3 product search and normalization into Carti."""

from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import uuid

from server.app.services.discovery.client.channel3_client import Channel3Client
from server.app.services.discovery.config import Channel3Config
from server.app.services.discovery.models.locale import Channel3Locale
from server.app.services.discovery.models.product import NormalizedProduct
from server.app.services.discovery.services.product_service import ProductService
from server.app.services.interfaces import IDiscoveryService

logger = logging.getLogger("carti.discovery")


class DiscoveryService(IDiscoveryService):
    """Product discovery service implementing IDiscoveryService protocol via Channel3."""

    def __init__(
        self,
        config: Optional[Channel3Config] = None,
        product_service: Optional[ProductService] = None,
        channel3_client: Optional[Channel3Client] = None,
    ):
        self.config = config or Channel3Config()
        if product_service:
            self.product_service = product_service
        else:
            client = channel3_client or Channel3Client(config=self.config)
            self.product_service = ProductService(client=client)

    def search_candidates(
        self,
        query: str,
        max_price: Optional[Decimal],
        currency: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search products via Channel3 and return candidate dictionaries."""
        filters = filters or {}
        locale = Channel3Locale(country=self.config.default_country, language=self.config.default_language, currency=currency)

        try:
            products: List[NormalizedProduct] = self.product_service.search_products(
                query=query,
                locale=locale,
            )
        except Exception as exc:
            logger.warning("Channel3 product search failed: %s; falling back to empty list", exc)
            return []

        results: List[Dict[str, Any]] = []
        for prod in products:
            for offer in prod.offers:
                # Filter out unavailable offers
                if offer.availability and offer.availability.lower() == "outofstock":
                    continue
                # Price threshold filter if max_price is given
                if max_price is not None and offer.price_amount > max_price:
                    continue

                candidate_dict = {
                    "product_id": prod.product_id,
                    "title": prod.title,
                    "brand": prod.brand,
                    "category": prod.category,
                    "description": prod.description,
                    "image_url": prod.image_url,
                    "offer_id": offer.offer_key,
                    "domain": offer.domain,
                    "buy_url": offer.buy_url,
                    "price_amount": offer.price_amount,
                    "currency": offer.currency,
                    "availability": offer.availability,
                    "condition": offer.condition,
                    "attributes": prod.attributes,
                    "raw_product": prod,
                }
                results.append(candidate_dict)

        return results
