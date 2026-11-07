"""Normalizer for Channel3 canonical product data."""

from datetime import datetime, timezone
from typing import Any
from server.app.services.discovery.constants import PROVIDER_NAME
from server.app.services.discovery.exceptions import Channel3ValidationError
from server.app.services.discovery.models.product import NormalizedProduct
from server.app.services.discovery.normalizers.offer_normalizer import OfferNormalizer
from server.app.services.discovery.normalizers.variant_normalizer import VariantNormalizer
from server.app.services.discovery.validators.response_validator import ResponseValidator


class ProductNormalizer:
    """Transforms raw Channel3 product payloads into structured, validated NormalizedProduct instances."""

    @staticmethod
    def normalize_product_attributes(raw_data: dict[str, Any]) -> dict[str, Any]:
        """Extract and normalize general product specifications and attributes consistently."""
        attributes: dict[str, Any] = {}

        # Standard known Channel3 attribute fields
        for field in ("gender", "age", "materials", "key_features", "dimensions", "weight"):
            if field in raw_data and raw_data[field] is not None:
                attributes[field] = raw_data[field]

        # Any explicit attributes dictionary
        raw_attrs = raw_data.get("attributes")
        if isinstance(raw_attrs, dict):
            attributes.update(raw_attrs)
        elif isinstance(raw_attrs, list):
            for item in raw_attrs:
                if isinstance(item, dict) and "name" in item:
                    attributes[str(item["name"])] = item.get("value")

        return attributes

    @classmethod
    def normalize_product(cls, raw_data: dict[str, Any]) -> NormalizedProduct:
        """Parse and normalize raw Channel3 product dictionary into a NormalizedProduct.

        Args:
            raw_data: Raw JSON dictionary from Channel3 API.

        Returns:
            NormalizedProduct instance.

        Raises:
            Channel3ValidationError: If required fields (product_id, title) are invalid.
        """
        if not isinstance(raw_data, dict):
            raise Channel3ValidationError(f"Expected product dictionary, got {type(raw_data).__name__}")

        # Unwrap nested 'product' envelope if present
        payload = raw_data.get("product") if isinstance(raw_data.get("product"), dict) else raw_data

        # 1. Product ID
        raw_id = payload.get("id") or payload.get("product_id")
        product_id = ResponseValidator.validate_product_id(raw_id)

        # 2. Title
        raw_title = payload.get("title") or payload.get("name")
        title = ResponseValidator.validate_title(raw_title)

        # 3. Brand
        brand: str | None = None
        raw_brands = payload.get("brands")
        if isinstance(raw_brands, list) and raw_brands:
            first = raw_brands[0]
            if isinstance(first, dict):
                brand = first.get("name") or first.get("title")
            elif isinstance(first, str):
                brand = first
        elif isinstance(payload.get("brand"), str):
            brand = payload.get("brand")

        # 4. Category
        category: str | None = None
        raw_cat = payload.get("category")
        if isinstance(raw_cat, dict):
            category = raw_cat.get("title") or raw_cat.get("name") or raw_cat.get("slug")
        elif isinstance(raw_cat, str):
            category = raw_cat

        # 5. Description
        description: str | None = None
        raw_desc = payload.get("description")
        if isinstance(raw_desc, str) and raw_desc.strip():
            description = raw_desc.strip()

        # 6. Images
        images: list[str] = []
        raw_images = payload.get("images")
        if isinstance(raw_images, list):
            for img in raw_images:
                if isinstance(img, str) and img.strip():
                    images.append(img.strip())
                elif isinstance(img, dict) and "url" in img and isinstance(img["url"], str):
                    images.append(img["url"].strip())

        primary_image = payload.get("image_url") or payload.get("image")
        if isinstance(primary_image, str) and primary_image.strip():
            image_url = primary_image.strip()
        elif images:
            image_url = images[0]
        else:
            image_url = None

        if image_url and image_url not in images:
            images.insert(0, image_url)

        # 7. Attributes
        attributes = cls.normalize_product_attributes(payload)

        # 8. Variants
        raw_variants = payload.get("variants") or []
        variants = VariantNormalizer.normalize_variants(raw_variants)

        # 9. Retailer Offers
        raw_offers = payload.get("offers") or []
        offers = OfferNormalizer.normalize_offers(raw_offers)

        return NormalizedProduct(
            provider=PROVIDER_NAME,
            product_id=product_id,
            title=title,
            brand=brand,
            category=category,
            description=description,
            image_url=image_url,
            images=images,
            attributes=attributes,
            variants=variants,
            offers=offers,
            observed_at=datetime.now(timezone.utc),
        )
