# 🛒 Module B6: Channel3 Client & Product Normalization

Part of the **CartiQ Agentic Shopping Concierge**.

---

## 📖 1. Overview

Module B6 provides a fully typed, deterministic, server-side client and normalization layer for the **Channel3 API** (`https://api.trychannel3.com`). 

It enables CartiQ to:
1. Query millions of cross-merchant products using natural language and structured filters.
2. Resolve external merchant URLs into canonical products safely with SSRF defenses.
3. Retrieve and refresh canonical product metadata and side-by-side multi-retailer offers.
4. Separate canonical product definitions from mutable individual retailer offers.
5. Deterministically evaluate retailer offers against user spending mandates (budgets, per-item caps, domain whitelists/blacklists) using exact `Decimal` arithmetic.
6. Re-verify offer price, availability, and stability immediately prior to proposal creation and PayPal checkout capture.

---

## 🏛️ 2. Architectural Guardrails

- **Zero Payment Functionality**: B6 contains **no payment credentials, capture calls, or refund endpoints**.
- **No LLM Authority**: LLM recommendations are advisory. Selection and freshness checks are enforced by deterministic Python code.
- **Exact Decimal Pricing**: All monetary amounts use Python `Decimal` to avoid floating-point drift.
- **Offer Identity Preservation**: The canonical product ID and stable retailer `offer_key` are preserved across refreshes. Never silently substitutes another seller or price.
- **Credential Protection**: Server-side API keys (`x-api-key`) are redacted from logs, string representations, and error messages.
- **SSRF Defense**: URL lookup strictly permits HTTP/HTTPS schemes and disallows localhost, loopback, link-local, and private RFC-1918 IP addresses.

---

## 🔌 3. Channel3 API Endpoints Implemented

| Operation | Method | Channel3 Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Product Search** | `POST` | `/v1/search` | Natural language query with filters and limit. |
| **URL Lookup** | `POST` | `/v1/lookup` | Resolves merchant URL to canonical product. |
| **Product Detail** | `GET` | `/v1/products/{product_id}` | Retrieves canonical details and live retailer offers. |

---

## 📦 4. Directory Structure

```text
modules/b6_channel3/
├── __init__.py                # Public module exports
├── README.md                  # Module documentation
├── requirements.txt           # Module dependencies
├── config.py                  # Module configuration & secret masking
├── constants.py               # Constants, endpoints, and enums
├── exceptions.py              # Structured, redacted exception classes
│
├── client/
│   ├── __init__.py
│   ├── authentication.py      # x-api-key header manager
│   ├── http_client.py         # HTTPX async client with retries and backoff
│   └── channel3_client.py     # High-level typed client
│
├── models/
│   ├── __init__.py
│   ├── locale.py              # Channel3Locale (US/en/USD)
│   ├── offer.py               # NormalizedOffer (Decimal price, domain, buy_url)
│   ├── product.py             # NormalizedProduct (canonical product metadata)
│   └── variant.py             # NormalizedVariant (options, SKUs)
│
├── normalizers/
│   ├── __init__.py
│   ├── offer_normalizer.py    # Generates stable offer_keys, normalizes prices
│   ├── product_normalizer.py  # Separates product metadata from offers
│   └── variant_normalizer.py  # Parses variant options
│
├── services/
│   ├── __init__.py
│   ├── search_service.py      # Search orchestration
│   ├── lookup_service.py      # URL lookup with SSRF checks
│   ├── product_service.py     # Freshness verification prior to checkout
│   └── offer_selection.py     # Deterministic mandate constraint evaluation
│
├── validators/
│   ├── __init__.py
│   ├── response_validator.py  # Validates product IDs, prices, currencies
│   └── url_validator.py       # SSRF and URL schema validation
│
├── interfaces/
│   ├── __init__.py
│   └── channel3_interface.py  # Abstract base classes for dependency injection
│
└── tests/                     # Comprehensive isolated test suite
    ├── __init__.py
    ├── conftest.py
    ├── test_channel3_client.py
    ├── test_product_search.py
    ├── test_product_lookup.py
    ├── test_product_details.py
    ├── test_product_normalization.py
    ├── test_offer_normalization.py
    ├── test_multiple_offers.py
    ├── test_price_changes.py
    ├── test_error_handling.py
    └── test_security.py
```

---

## 🚀 5. Usage Example

```python
from decimal import Decimal
from modules.b6_channel3 import (
    Channel3Config,
    Channel3Client,
    SearchService,
    ProductService,
    OfferSelectionService,
    SpendingMandate,
    Channel3Locale,
)

# 1. Initialize client
config = Channel3Config(api_key="your_channel3_api_key")
client = Channel3Client(config=config)

# 2. Search products
search_svc = SearchService(client)
products = await search_svc.search(
    query="ergonomic mechanical keyboard",
    limit=5,
    locale=Channel3Locale(country="US", language="en", currency="USD")
)

# 3. Select an offer deterministically against user mandate
product = products[0]
mandate = SpendingMandate(
    max_budget=Decimal("150.00"),
    per_item_cap=Decimal("150.00"),
    currency="USD",
    allowed_domains=["bestbuy.com", "amazon.com", "target.com"]
)

selected_offer = OfferSelectionService.select_offer(
    product=product,
    offer_key=product.offers[0].offer_key,
    mandate=mandate
)

# 4. Mandatory pre-checkout freshness re-validation
product_svc = ProductService(client)
refresh_result = await product_svc.refresh_product(
    product_id=product.product_id,
    selected_offer_key=selected_offer.offer_key,
    baseline_offer=selected_offer,
)

if refresh_result.is_safe_for_checkout:
    print(f"Verified price: {refresh_result.selected_offer.price_amount} USD")
else:
    print(f"Checkout blocked: {refresh_result.details}")
```

---

## 🛡️ 6. Zero-Modification Isolation

This module is designed as an independent library. It does not import, modify, or monkey-patch any existing files in CartiQ. Future modules (such as B7 Orchestrator or FastAPI routers) can consume B6 via standard dependency injection by importing from `modules.b6_channel3`.
