"""Module B6 — Channel3 Client and Product Normalization.

Autonomous agentic shopping concierge client providing deterministic validation,
typed normalized models, and pre-checkout freshness re-verification.
"""

from modules.b6_channel3.client import (
    Channel3Auth,
    Channel3Client,
    Channel3HTTPClient,
)
from modules.b6_channel3.config import Channel3Config
from modules.b6_channel3.constants import (
    OfferAvailability,
    OfferCondition,
    RefreshStatus,
)
from modules.b6_channel3.exceptions import (
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
from modules.b6_channel3.models import (
    Channel3Locale,
    NormalizedOffer,
    NormalizedProduct,
    NormalizedVariant,
)
from modules.b6_channel3.normalizers import (
    OfferNormalizer,
    ProductNormalizer,
    VariantNormalizer,
)
from modules.b6_channel3.services import (
    LookupService,
    OfferSelectionService,
    ProductRefreshResult,
    ProductService,
    SearchService,
    SpendingMandate,
)
from modules.b6_channel3.validators import (
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
