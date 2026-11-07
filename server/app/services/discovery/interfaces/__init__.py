"""Interfaces for B6 Channel3 module."""

from server.app.services.discovery.interfaces.channel3_interface import (
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
