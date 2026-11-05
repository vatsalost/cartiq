"""Normalizer for Channel3 product variants."""

from typing import Any
from modules.b6_channel3.models.variant import NormalizedVariant


class VariantNormalizer:
    """Parses raw variant data structures from Channel3 into typed models."""

    @staticmethod
    def normalize_variant(raw_variant: dict[str, Any]) -> NormalizedVariant:
        """Normalize a single raw variant dictionary."""
        if not isinstance(raw_variant, dict):
            return NormalizedVariant()

        variant_id = raw_variant.get("id") or raw_variant.get("variant_id")
        name = raw_variant.get("name") or raw_variant.get("title")

        options: dict[str, str] = {}
        raw_options = raw_variant.get("options")
        if isinstance(raw_options, dict):
            options = {str(k): str(v) for k, v in raw_options.items() if v is not None}
        elif isinstance(raw_options, list):
            for item in raw_options:
                if isinstance(item, dict) and "name" in item and "value" in item:
                    options[str(item["name"])] = str(item["value"])

        sku = raw_variant.get("sku")
        image_url = raw_variant.get("image_url") or raw_variant.get("image")
        if isinstance(image_url, dict):
            image_url = image_url.get("url")

        return NormalizedVariant(
            variant_id=str(variant_id) if variant_id else None,
            name=str(name) if name else None,
            options=options,
            sku=str(sku) if sku else None,
            image_url=str(image_url) if image_url else None,
        )

    @classmethod
    def normalize_variants(cls, raw_variants: list[Any]) -> list[NormalizedVariant]:
        """Normalize a list of raw variants."""
        if not raw_variants or not isinstance(raw_variants, list):
            return []
        normalized: list[NormalizedVariant] = []
        for raw in raw_variants:
            if isinstance(raw, dict):
                normalized.append(cls.normalize_variant(raw))
        return normalized
