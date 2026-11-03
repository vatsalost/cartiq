<div align="center">

# 🛒 CartiQ — Agentic Shopping Concierge

### Autonomous AI-Powered Shopping Assistant with Deterministic Financial Guardrails & PayPal Checkout

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://www.postgresql.org/)
[![PayPal Orders v2](https://img.shields.io/badge/PayPal-Orders_v2_API-003087.svg)](https://developer.paypal.com/docs/api/orders/v2/)
[![Tests Passing](https://img.shields.io/badge/tests-127%20passed-brightgreen.svg)](server/tests)
[![Security](https://img.shields.io/badge/Security-Argon2id%20%7C%20IDOR%20Defense-orange.svg)](docs/module-b2-verification-report.md)

**Built for the PayPal AI Hackathon 2026**

</div>

---

## 📖 Executive Summary

**CartiQ** is an autonomous agentic shopping concierge designed to transform natural language shopping requests into high-fidelity, verified retailer product offers. Unlike traditional shopping bots that merely link out or hallucinate purchase actions, CartiQ provides a secure end-to-end shopping journey:

1. **Natural-Language Understanding:** Interprets complex conversational requests and extracts structured shopping parameters.
2. **Multi-Retailer Sourcing:** Discovers real-time candidate items across merchant partners via the Channel3 API.
3. **Deterministic Backend Guardrails:** Strictly evaluates merchant trust, price tolerances, per-item limits, stock availability, and user spending mandates before generating reviewable proposals.
4. **Server-Side PayPal Sandbox Checkout:** Initiates and captures payments through PayPal's Orders v2 REST API using secure idempotency and row-level reservation locks.
5. **Real-time Event Streaming:** Streams live concierge reasoning, candidate evaluation logs, and state updates using Server-Sent Events (SSE).

---

## 🏛️ Core Architectural Philosophy

```
+-----------------------------------------------------------------------------------+
|                              THE THREE CARTIQ PILLARS                             |
+-----------------------------------------------------------------------------------+
|  1. AI Reasons, Backend Decides                                                   |
|     The LLM acts strictly as a recommendation engine. It has ZERO credentials,   |
|     ZERO payment tools, and cannot authorize or initiate financial charges.       |
|                                                                                   |
|  2. Pure Deterministic Mandates                                                   |
|     User-defined financial limits (total budget, per-item caps, domain            |
|     whitelists, max quantities) are enforced by Python code using exact Decimal   |
|     arithmetic and row-level database locking.                                    |
|                                                                                   |
|  3. Safe Human-in-the-Loop Checkout                                               |
|     Every purchase requires explicit user proposal review and standard PayPal     |
|     popup buyer authorization. The backend captures only after validation.        |
+-----------------------------------------------------------------------------------+
```

---

## 🔄 End-to-End System Architecture

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Frontend
    participant Gateway as FastAPI Gateway
    participant Auth as B2 Auth Boundary
    participant Mandate as B3 Mandate Engine
    participant Agent as AI Agent (Gemini)
    participant Channel3 as Channel3 API
    participant PayPal as PayPal Orders v2 API
    participant Audit as Immutable Audit Log

    User->>Gateway: POST /api/mandates (Set Budget $100, Cap $50)
    Gateway->>Auth: Validate Session / Bearer Token
    Gateway->>Mandate: Version & Persist Active Mandate (V1)
    Mandate->>Audit: Record mandate_created

    User->>Gateway: POST /api/requests ("Find a desk lamp under $40")
    Gateway->>Agent: Initiate Agent Orchestration
    Gateway-->>User: 202 Accepted + SSE Stream URL

    Agent->>Channel3: Query Product Offers & Real-Time Stock
    Channel3-->>Agent: Candidate Items & Retailer Offers
    Agent->>Gateway: Run Deterministic Guardrails
    Gateway->>Mandate: Check Cap ($40 <= $50) & Categories
    Gateway-->>User: 200 Proposal Ready (Lumina Lamp: $34.99)

    User->>Gateway: POST /api/proposals/:id/order (Approve Proposal)
    Gateway->>Mandate: Lock Mandate & Reserve $34.99
    Mandate->>Audit: Record budget_reservation_created
    Gateway->>PayPal: Create Order (PayPal-Request-Id: idempotency)
    PayPal-->>Gateway: Return paypal_order_id
    Gateway-->>User: Order Initialized

    User->>PayPal: Authorize Payment (PayPal JS SDK Popup)
    PayPal-->>User: Buyer Approval Granted

    User->>Gateway: POST /api/orders/:id/capture
    Gateway->>PayPal: Capture Payment (PayPal Orders v2 API)
    PayPal-->>Gateway: Capture Confirmed
    Gateway->>Mandate: Convert Reservation to Captured Spend
    Mandate->>Audit: Record budget_reservation_captured
    Gateway-->>User: 200 Order Completed & Receipt
```

---

## 🧩 Backend Module Breakdown

### 🛡️ Module B1: API Gateway & Request Validation
- **Pydantic v2 Schemas**: Strict type checking and request boundary validation.
- **SSE Event Replay**: Real-time event streaming (`GET /api/requests/{id}/stream`) with historical buffer replay.
- **Centralized Error Envelope**: Standardized structured error responses (`{ "error": { "code", "message", "retryable", "details" } }`).
- **Rate Limiting**: Sliding-window rate limiters protecting public, creation, and checkout endpoints.

### 🔐 Module B2: Authentication & User Ownership Boundary
- **Argon2id Cryptographic Hashing**: Secure password storage utilizing memory-hard `argon2-cffi`.
- **Hashed Session Tokens**: Raw cookies/tokens are never stored in plaintext; only `SHA-256(raw_token)` is indexed in the database.
- **Dual Transport Authentication**: Full interoperability between secure HTTP-only SameSite cookies (`carti_session`) and `Authorization: Bearer <token>` headers.
- **Strict IDOR Prevention**: Every database query verifies resource ownership against the authenticated caller.
- **Anti-Enumeration Defense**: Constant-time comparison using dummy hash calculations prevents user enumeration.

### 💰 Module B3: Mandate Service & Financial Engine
- **Immutable Versioning**: Creating a new mandate increments the version (`v1 -> v2 -> v3`) and marks previous records `superseded` without destructive updates.
- **Authoritative Budget Formula**:
  $$\text{Available Budget} = \max(0.00, \text{Total Budget} - \text{Captured Spending} - \text{Active Reservations})$$
- **No Floating-Point Math**: All financial computations utilize Python `Decimal` and PostgreSQL `NUMERIC(12, 2)`.
- **Committed Spend Ceiling**: Prevents lowering a mandate total budget below active committed and reserved spending.
- **Concurrency & Race Defenses**: Row-level locking (`SELECT ... FOR UPDATE`) prevents concurrent checkout attempts from over-reserving available funds.
- **Automatic Lifecycle Invalidation**: Detects expiration and revocation, immediately blocking subsequent checkouts.

### 💳 Module B10: PayPal Orders v2 & Webhook Pipeline
- **Server-Side Order Creation**: Initiates PayPal sandbox orders without exposing API credentials to clients.
- **Safe Capture Engine**: Enforces idempotency via `PayPal-Request-Id` headers.
- **Automated Refund Pipeline**: Processes full refunds for completed purchases, immediately restoring spendable mandate budget.
- **Webhook Reconciliation**: Cryptographically verifies PayPal webhook headers to handle `PAYMENT.CAPTURE.COMPLETED`, `DENIED`, and `REFUNDED` events.

---

## 📡 API Reference Matrix

### Authentication
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register new user account with Argon2id hash | No |
| `POST` | `/api/auth/login` | Authenticate credentials and rotate session | No |
| `POST` | `/api/auth/demo` | Instant demo login (development/test only) | No |
| `POST` | `/api/auth/logout` | Revoke session and clear HTTP-only cookie | Yes |
| `GET` | `/api/auth/me` | Retrieve authenticated user profile | Yes |
| `GET` | `/api/auth/status` | Lightweight session check | No |

### Mandates & Financial Engine
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/mandates/current` | Active mandate with remaining budget breakdown & summary | Yes |
| `POST` | `/api/mandates` | Create new mandate version (supersedes prior active version) | Yes |
| `GET` | `/api/mandates/current/budget` | Standalone real-time available budget calculation | Yes |
| `GET` | `/api/mandates/versions/{version}` | Historical mandate version lookup | Yes |
| `POST` | `/api/mandates/{id}/revoke` | Revoke mandate, halting future agent checkouts | Yes |
| `GET` | `/api/mandates/{id}` | Direct mandate lookup by ID with ownership check | Yes |

### Shopping Requests & Concierge Agent
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/requests` | Submit natural-language request (returns HTTP 202 Accepted) | Yes |
| `GET` | `/api/requests/{id}` | Inspect shopping request status & extracted intent | Yes |
| `GET` | `/api/requests/{id}/stream` | Server-Sent Events (SSE) real-time progress & event replay | Yes |
| `POST` | `/api/requests/{id}/cancel` | Cancel in-flight agent search | Yes |
| `GET` | `/api/requests/{id}/candidates` | Retrieve candidate items & retailer offers | Yes |

### Purchase Proposals & Checkout
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/proposals/{id}` | Proposal review snapshot, policy checks & rationale | Yes |
| `POST` | `/api/proposals/{id}/order` | Revalidate facts, lock budget, and initialize PayPal order | Yes |
| `POST` | `/api/orders/{id}/capture` | Server-side capture after buyer approval | Yes |
| `POST` | `/api/orders/{id}/refund` | Process full refund for captured payment | Yes |
| `GET` | `/api/orders` | Paginated purchase history | Yes |
| `GET` | `/api/orders/{id}` | Detailed receipt with product & refund breakdown | Yes |
| `POST` | `/api/webhooks/paypal` | PayPal webhook event receiver & signature validation | HMAC |

### System Health
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/health` | Service status, API version, and database connectivity | No |

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.11+ | Type-annotated, high-performance async runtime |
| **API Framework** | FastAPI | OpenAPI documentation, Pydantic validation, dependency injection |
| **ASGI Server** | Uvicorn | Production-ready asynchronous web server |
| **ORM & Database** | SQLAlchemy 2.0 / PostgreSQL | Async-capable ORM, row-level locks, transactional integrity |
| **Database Migrations** | Alembic | Version-controlled, schema migration management |
| **Validation** | Pydantic v2 | High-throughput data modeling and input sanitization |
| **Authentication** | Argon2id (`argon2-cffi`) | Memory-hard cryptographic password hashing |
| **Payments** | PayPal REST APIs v2 | Server-side Orders v2, Captures, Refunds, Webhooks |
| **Retailer Sourcing** | Channel3 API | Live multi-retailer catalog discovery & stock verification |
| **LLM Provider** | Google Gemini (2.5-flash) | Natural language intent extraction & ranking explanation |
| **Testing** | Pytest / AnyIO | Automated unit, integration, and security verification |

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.11+** installed
- **PostgreSQL 16+** (or use the built-in SQLite development fallback)
- **Git**

### 2. Clone the Repository
```bash
git clone -b vatsal https://github.com/vatsalost/cartiq.git
cd cartiq
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure your environment variables:
```dotenv
APP_ENV=development
APP_BASE_URL=http://localhost:8000
CLIENT_BASE_URL=http://localhost:5173

# Database (PostgreSQL with SQLite fallback for local dev)
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/carti_db
SQLITE_FALLBACK=true

# AI & Channel3 Settings
LLM_PROVIDER=gemini
LLM_API_KEY=your_gemini_api_key
CHANNEL3_API_KEY=your_channel3_api_key

# PayPal Sandbox Credentials
PAYPAL_ENV=sandbox
PAYPAL_CLIENT_ID=your_paypal_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_paypal_sandbox_client_secret
PAYPAL_WEBHOOK_ID=your_paypal_webhook_id

# Security
SESSION_SECRET=generate_a_random_32_character_string_here
```

### 4. Install Dependencies
```bash
python -m pip install -r server/requirements.txt
```

### 5. Apply Database Migrations
```bash
python -m alembic -c server/alembic.ini upgrade head
```

### 6. Start the API Server
```bash
python -m uvicorn server.app.main:app --reload --port 8000
```

- **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check Endpoint:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 🧪 Comprehensive Automated Test Suite

CartiQ features a comprehensive automated test suite with **127 automated tests** covering unit logic, database migrations, IDOR ownership boundaries, financial calculation states, and concurrency safety:

```bash
python -m pytest server/tests -v
```

### Test Suite Coverage Breakdown

```
============================= test session starts =============================
server/tests/test_auth.py                      [14 passed]  Auth, Argon2id, session rotation, logout
server/tests/test_b2_security_audit.py         [22 passed]  IDOR defenses, cross-user isolation
server/tests/test_b3_financial_audit.py        [11 passed]  15 financial scenarios, Decimal precision
server/tests/test_mandates_b3.py               [37 passed]  Full B3 lifecycle, versioning, reservations
server/tests/test_mandates.py                  [ 3 passed]  Mandate validation and normalization
server/tests/test_orders.py                    [ 3 passed]  PayPal capture & refund delegation
server/tests/test_ownership_b2.py              [ 7 passed]  Cross-resource ownership boundaries
server/tests/test_proposals.py                 [ 4 passed]  Proposal evaluation & checkout order creation
server/tests/test_rate_limit_and_payloads.py   [ 2 passed]  Sliding-window rate limiters & payload caps
server/tests/test_requests.py                  [ 5 passed]  Shopping request lifecycle & cancellation
server/tests/test_security_and_edge_cases.py   [13 passed]  Idempotency keys, injection, token tamper
server/tests/test_webhooks.py                  [ 2 passed]  PayPal webhook verification & replay
server/tests/test_health.py                    [ 2 passed]  Service health & database connectivity
server/tests/test_candidates.py                [ 2 passed]  Candidate ranking and offer mapping
======================= 127 passed, 1 warning in 14.05s =======================
```

---

## 📑 Formal Verification & Audit Reports

Detailed audit and verification reports are available in the [`docs/`](docs/) directory:
- [Module B1 Verification Report](docs/module-b1-verification-report.md) — API Routes & Request Validation
- [Module B2 Implementation Report](docs/module-b2-implementation-report.md) — Authentication & Security Model
- [Module B2 Security Audit Report](docs/module-b2-verification-report.md) — Cross-Resource IDOR Verification
- [Module B3 Implementation Report](docs/module-b3-implementation-report.md) — Mandate Service Architecture
- [Module B3 Financial Logic Audit Report](docs/module-b3-verification-report.md) — Financial Verification & Concurrency Audit

---

## 🔒 Security Best Practices

1. **No Client-Supplied Prices**: The client never sends product prices, amounts, or currency codes to payment endpoints. All monetary amounts are computed strictly from verified database proposal snapshots.
2. **Stable Idempotency Keys**: All financial operations use cryptographic idempotency keys (`PayPal-Request-Id`) derived from internal entity IDs to prevent duplicate charges upon network retries.
3. **Strict Separation of Concerns**: AI components are isolated to recommendation and ranking. Financial rules and payment captures are executed in deterministic Python services.
4. **Append-Only Audit Trail**: Every mandate modification, budget reservation, capture, and cancellation records an immutable event in the `audit_events` table.

---

## 👥 Authors & Acknowledgments

- **Lead Developers**:
  - [Vatsal Chaudhary](https://github.com/vatsalost)
  - [Aditi Pandey](https://github.com/aditispandey)
- **Event**: Built for the **PayPal AI Hackathon 2026**
- **Special Thanks**: PayPal Developer Platform

---

<div align="center">
<sub>Built with precision, security, and financial integrity for the PayPal AI Hackathon 2026.</sub>
</div>
