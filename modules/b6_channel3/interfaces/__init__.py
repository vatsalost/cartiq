"""Interfaces for B6 Channel3 module."""

from modules.b6_channel3.interfaces.channel3_interface import (
    IChannel3Client,
    ILookupService,
    IOfferSelectionService,
    IProductService,
    ISearchService,
)

__all__ = [
    "IChannel3Client",
    "ILookupService",
    "IOfferSelectionService",
    "IProductService",
    "ISearchService",
]
