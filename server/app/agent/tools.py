"""Approved research tools and strict Pydantic argument schemas (Module B5)."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type
import uuid
from pydantic import BaseModel, ConfigDict, Field

from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.mandate import Mandate


class ToolContext:
    """Execution context provided to tools during an agent research session."""

    def __init__(
        self,
        request_id: uuid.UUID,
        user_id: uuid.UUID,
        mandate: Optional[Mandate] = None,
        discovery_service: Optional[Any] = None,
    ):
        self.request_id = request_id
        self.user_id = user_id
        self.mandate = mandate
        self.discovery_service = discovery_service
        self.cached_products: Dict[str, Dict[str, Any]] = {}
        self.cached_offers: Dict[str, Dict[str, Any]] = {}


# --- Strict Input Schemas (extra='forbid' prevents unexpected arguments) ---

class SearchProductsInput(BaseModel):
    """Input parameters for search_products tool."""

    query: str = Field(min_length=2, max_length=200, description="Natural search query for products")
    max_price: Optional[Decimal] = Field(default=None, ge=Decimal("0.01"), description="Upper price limit")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="3-letter ISO currency code")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filtering parameters")

    model_config = ConfigDict(extra="forbid")


class GetProductInput(BaseModel):
    """Input parameters for get_product tool."""

    product_id: str = Field(min_length=1, max_length=128, description="Canonical product ID")
    locale: Optional[Dict[str, str]] = Field(default=None, description="Optional country/language/currency locale")
    selected_variant: Optional[str] = Field(default=None, description="Optional product variant ID")

    model_config = ConfigDict(extra="forbid")


class ProposePurchaseInput(BaseModel):
    """Input parameters for propose_purchase tool."""

    product_id: str = Field(min_length=1, max_length=128, description="Chosen canonical product ID")
    offer_key: str = Field(min_length=1, max_length=128, description="Chosen retailer offer key")
    quantity: int = Field(default=1, ge=1, le=50, description="Quantity to purchase")
    rationale: str = Field(min_length=5, max_length=1000, description="Factual justification based on retrieved attributes")

    model_config = ConfigDict(extra="forbid")


class CompareCandidatesInput(BaseModel):
    """Input parameters for compare_candidates tool."""

    candidate_ids: List[str] = Field(min_length=1, max_length=10, description="List of product IDs to compare")

    model_config = ConfigDict(extra="forbid")


# --- Base Tool Definition ---

class BaseTool(ABC):
    """Abstract interface for all approved research tools."""

    name: str
    description: str
    input_schema: Type[BaseModel]

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any], context: ToolContext) -> Any:
        """Execute tool logic using validated arguments."""
        pass


# --- Concrete Approved Tool Implementations ---

class SearchProductsTool(BaseTool):
    """Tool to search products across authorized retailer catalogs via B6 Channel3."""

    name = "search_products"
    description = "Search authorized retailer catalogs for product candidates matching the query and filters."
    input_schema = SearchProductsInput

    async def execute(self, arguments: Dict[str, Any], context: ToolContext) -> List[Dict[str, Any]]:
        query = arguments["query"]
        max_price = arguments.get("max_price")
        currency = arguments.get("currency", "USD")
        filters = arguments.get("filters") or {}

        # If discovery_service is injected (B6), delegate to it
        if context.discovery_service and hasattr(context.discovery_service, "search_candidates"):
            results = context.discovery_service.search_candidates(
                query=query,
                max_price=max_price,
                currency=currency,
                filters=filters,
            )
            # Cache results in context for get_product and grounding
            for item in results:
                p_id = item.get("product_id") or item.get("id")
                if p_id:
                    context.cached_products[str(p_id)] = item
                    for off in item.get("offers", []):
                        context.cached_offers[str(off.get("offer_key", ""))] = off
            return results

        # Built-in fallback research catalog (deterministic for tests & local demo)
        default_items = [
            {
                "product_id": "lamp_001",
                "title": "Lumino Ergo Warm LED Desk Lamp",
                "brand": "Lumino",
                "category": "Home",
                "description": "Adjustable arm, warm 3000K LED, touch dimmer, flicker-free desk lamp.",
                "image_url": "https://images.unsplash.com/photo-1534349762230-e0cadf78f5da",
                "attributes": {
                    "color_temperature": "3000K warm",
                    "power": "12W",
                    "material": "Brushed Aluminum",
                    "dimmable": True,
                },
                "offers": [
                    {
                        "offer_key": "off_target_001",
                        "domain": "target.com",
                        "price_amount": "34.99",
                        "currency": currency,
                        "availability": "InStock",
                        "condition": "new",
                        "buy_url": "https://target.com/p/lumino-ergo-lamp",
                        "observed_at": datetime.now(timezone.utc).isoformat(),
                    }
                ],
            },
            {
                "product_id": "lamp_002",
                "title": "Aura Glow Minimalist Wooden Desk Lamp",
                "brand": "Aura",
                "category": "Home",
                "description": "Solid oak base with warm diffused ambient light, USB-C charging port.",
                "image_url": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c",
                "attributes": {
                    "color_temperature": "2700K warm ambient",
                    "power": "10W",
                    "material": "Solid Oak",
                    "dimmable": True,
                },
                "offers": [
                    {
                        "offer_key": "off_amazon_002",
                        "domain": "amazon.com",
                        "price_amount": "38.50",
                        "currency": currency,
                        "availability": "InStock",
                        "condition": "new",
                        "buy_url": "https://amazon.com/dp/B08XYZ123",
                        "observed_at": datetime.now(timezone.utc).isoformat(),
                    }
                ],
            },
        ]

        # Filter by max_price if supplied
        filtered = []
        for item in default_items:
            # Check price cap
            cheapest = min(
                (Decimal(str(o["price_amount"])) for o in item["offers"]),
                default=Decimal("9999.00"),
            )
            if max_price is not None and cheapest > max_price:
                continue

            filtered.append(item)
            context.cached_products[item["product_id"]] = item
            for o in item["offers"]:
                context.cached_offers[o["offer_key"]] = o

        return filtered


class GetProductTool(BaseTool):
    """Tool to retrieve fresh canonical product detail and retailer offers via B6."""

    name = "get_product"
    description = "Retrieve detailed information, verified attributes, and refreshed retailer offers for a product."
    input_schema = GetProductInput

    async def execute(self, arguments: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        product_id = arguments["product_id"]

        # Check context cache first
        if product_id in context.cached_products:
            return context.cached_products[product_id]

        # If discovery_service is available, query get_product
        if context.discovery_service and hasattr(context.discovery_service, "get_product"):
            prod = context.discovery_service.get_product(
                product_id=product_id,
                locale=arguments.get("locale"),
            )
            if prod:
                context.cached_products[product_id] = prod
                return prod

        raise CartiAPIException(
            code=CartiErrorCode.TOOL_EXECUTION_FAILED,
            message=f"Product with ID '{product_id}' was not found in research cache or catalog.",
        )


class ProposePurchaseTool(BaseTool):
    """Tool to prepare and pre-validate a candidate purchase for downstream guardrail evaluation."""

    name = "propose_purchase"
    description = "Propose a selected candidate product and retailer offer for backend policy validation."
    input_schema = ProposePurchaseInput

    async def execute(self, arguments: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        product_id = arguments["product_id"]
        offer_key = arguments["offer_key"]
        quantity = arguments["quantity"]
        rationale = arguments["rationale"]

        product = context.cached_products.get(product_id)
        if not product:
            return {
                "eligible": False,
                "reason": f"Product '{product_id}' has not been discovered or validated through search_products.",
            }

        # Find matching offer
        selected_offer = None
        for off in product.get("offers", []):
            if off.get("offer_key") == offer_key:
                selected_offer = off
                break

        if not selected_offer:
            return {
                "eligible": False,
                "reason": f"Offer key '{offer_key}' is not available for product '{product_id}'.",
            }

        # Pre-check against mandate context if available
        if context.mandate:
            offer_price = Decimal(str(selected_offer.get("price_amount", "0.00")))
            if offer_price > context.mandate.per_item_cap:
                return {
                    "eligible": False,
                    "reason": f"Offer price ${offer_price} exceeds user mandate per-item cap of ${context.mandate.per_item_cap}.",
                }

            if context.mandate.allowed_retailers:
                domain = selected_offer.get("domain", "")
                if domain not in context.mandate.allowed_retailers:
                    return {
                        "eligible": False,
                        "reason": f"Retailer domain '{domain}' is not in allowed retailers: {context.mandate.allowed_retailers}.",
                    }

        return {
            "eligible": True,
            "product_id": product_id,
            "offer_key": offer_key,
            "quantity": quantity,
            "rationale": rationale,
            "status": "ready_for_guardrail_evaluation",
        }


class CompareCandidatesTool(BaseTool):
    """Tool to compare multiple candidates side-by-side."""

    name = "compare_candidates"
    description = "Compare up to 10 candidates side-by-side on price, attributes, and ratings."
    input_schema = CompareCandidatesInput

    async def execute(self, arguments: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        candidate_ids = arguments["candidate_ids"]
        comparison = []
        for c_id in candidate_ids:
            prod = context.cached_products.get(c_id)
            if prod:
                comparison.append({
                    "product_id": c_id,
                    "title": prod.get("title"),
                    "brand": prod.get("brand"),
                    "offers": prod.get("offers", []),
                    "attributes": prod.get("attributes", {}),
                })
        return {"compared_count": len(comparison), "items": comparison}
