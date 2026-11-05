"""Module B6 — Channel3 Client and Product Normalization.

Autonomous agentic shopping concierge client providing deterministic validation,
typed normalized models, and pre-checkout freshness re-verification.
"""

from server.app.services.discovery.client import (
    Channel3Auth,
    Channel3Client,
    Channel3HTTPClient,
)
from server.app.services.discovery.config import Channel3Config
from server.app.services.discovery.constants import (
    OfferAvailability,
    OfferCondition,
    RefreshStatus,
)
from server.app.services.discovery.exceptions import (
    Channel3AuthError,
    Channel3BadRequestError,
    Channel3Error,
    Channel3NetworkError,
    Channel3NotFoundError,
    Channel3RateLimitError,
    Channel3ServerError,
    Channel3TimeoutError,
    Channel3ValidationError,
    CurrencyMismatchError,
    InvalidURLError,
    MandateConstraintViolationError,
    OfferNotFoundError,
    OfferUnavailableError,
)
from server.app.services.discovery.models import (
    Channel3Locale,
    NormalizedOffer,
    NormalizedProduct,
    NormalizedVariant,
)
from server.app.services.discovery.normalizers import (
    OfferNormalizer,
    ProductNormalizer,
    VariantNormalizer,
)
from server.app.services.discovery.services import (
    LookupService,
    OfferSelectionService,
    ProductRefreshResult,
    ProductService,
    SearchService,
    SpendingMandate,
)
from server.app.services.discovery.validators import (
    ResponseValidator,
    URLValidator,
)

__all__ = [
    # Config & Constants
    "Channel3Config",
    "OfferAvailability",
    "OfferCondition",
    "RefreshStatus",
    # Client
    "Channel3Auth",
    "Channel3Client",
    "Channel3HTTPClient",
    # Models
    "Channel3Locale",
    "NormalizedOffer",
    "NormalizedProduct",
    "NormalizedVariant",
    # Normalizers
    "OfferNormalizer",
    "ProductNormalizer",
    "VariantNormalizer",
    # Services
    "LookupService",
    "OfferSelectionService",
    "ProductRefreshResult",
    "ProductService",
    "SearchService",
    "SpendingMandate",
    # Validators
    "ResponseValidator",
    "URLValidator",
    # Exceptions
    "Channel3AuthError",
    "Channel3BadRequestError",
    "Channel3Error",
    "Channel3NetworkError",
    "Channel3NotFoundError",
    "Channel3RateLimitError",
    "Channel3ServerError",
    "Channel3TimeoutError",
    "Channel3ValidationError",
    "CurrencyMismatchError",
    "InvalidURLError",
    "MandateConstraintViolationError",
    "OfferNotFoundError",
    "OfferUnavailableError",
]
