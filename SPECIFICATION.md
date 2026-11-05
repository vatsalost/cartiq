# Agentic Shopping Concierge — Core Module Specification

**Version:** 1.0  
**Scope:** Core end-to-end shopping flow described in the supplied problem statement  
**Implementation target:** React + Vite + TypeScript, FastAPI, PostgreSQL, Channel3, an LLM with tool calling, PayPal Sandbox, and optional KERNEL browser verification  
**Status:** Core specification. Group gifts, price-watch/refund automation, taste memory, voice/local-language shopping, and other future features are intentionally not implemented in this version; they can be added as a separate advanced module set later.

---

## 1. Project goal

Build an AI shopping concierge that accepts a shopping request in natural language, searches products, compares retailer offers, checks the user's spending mandate, and prepares a purchase proposal. The user reviews the exact item and price and approves payment through PayPal Checkout. The server—not the LLM or browser—revalidates all purchase facts before it creates and captures a PayPal order.

The product has three separate responsibilities:

1. **The AI researches and recommends.** It interprets the request, searches Channel3, compares candidates, and explains its recommendation.
2. **The backend enforces the rules.** It independently checks the mandate, retailer offer, current price, availability, quantity, currency, expiry, and budget reservation.
3. **The user authorizes payment.** PayPal's JS SDK presents the checkout experience. The backend creates and captures the order only through the server-side PayPal API flow.

### Non-negotiable safety rules

- The LLM must not have a payment tool, PayPal credentials, or any route that can create, capture, or refund a payment.
- The LLM's proposed price is informational only. The server must retrieve the product and selected retailer offer from Channel3 again before creating a proposal and again immediately before creating the PayPal order.
- The browser must never decide the final amount. It sends proposal/order identifiers; the server loads the approved values from the database.
- PayPal secrets and the Channel3 API key stay on the server in environment variables.
- A proposal is not a completed purchase. A PayPal order is not a completed payment. The UI reports success only after the server confirms a completed capture.
- Treat product descriptions, retailer page text, search results, and other external content as untrusted data. They cannot change mandates, policies, or tool permissions.
- The demo's PayPal payment is a payment to the project's PayPal Sandbox merchant account. It does **not** automatically buy or fulfil the product from the external retailer. The retailer link is provided separately. The demo and README must state this clearly unless a real merchant checkout integration is separately implemented.

---

## 2. Recommended technology stack

Use one consistent stack rather than mixing the different stacks found in the reference repositories.

| Layer | Selected technology | Role |
|---|---|---|
| Frontend | React, Vite, TypeScript | Single-page application |
| UI and routing | React Router, Tailwind CSS | Pages, navigation, responsive layout |
| Server state | TanStack Query | API requests, loading state, cache invalidation |
| Checkout UI | `@paypal/react-paypal-js` | PayPal Buttons and buyer approval popup |
| Data table | AG Grid Community (optional) | Purchase history and audit views |
| Backend | Python 3.11+, FastAPI, Pydantic | REST API, SSE, domain services |
| HTTP client | HTTPX | Channel3, PayPal, LLM, and KERNEL calls |
| Database | PostgreSQL | Durable application state and transaction records |
| ORM/migrations | SQLAlchemy 2.x, Alembic | Database access and schema migration |
| AI | Gemini or another tool-calling LLM | Intent interpretation, product comparison, explanation |
| Product data | Channel3 API | Product search, canonical product data, offer/price/availability refresh |
| Payment | PayPal Orders v2 API, Sandbox | Create order, capture, refund, webhooks |
| Browser verification | KERNEL (optional in core demo) | Open a retailer page and inspect its visible offer details |
| Hosting | Render | Backend web service and PostgreSQL |
| Testing | Pytest, HTTPX test client, Vitest, Playwright | Unit, integration, and UI tests |

### Why FastAPI

FastAPI keeps the agent, product validation, payment services, and evaluation tests in one Python backend. One of the supplied references, AgentPay, uses React + TypeScript + Vite with FastAPI + HTTPX, server-side Channel3 refresh, PayPal Orders v2, and optional Elastic audit indexing. That is a close fit for this project. Other references use Next.js or Node, but the project should select one backend framework and keep it consistent.

### Currency for the initial version

Use one configured currency for the whole mandate and checkout. For the initial hackathon flow, use `USD` unless the PayPal Sandbox app, country settings, Channel3 locale, and judging requirements are deliberately configured for another supported currency. Do not silently convert currencies. Store the currency code alongside every monetary amount.

---

## 3. System architecture

```mermaid
flowchart LR
    U[User] --> FE[React + Vite Frontend]
    FE -->|REST| API[FastAPI API]
    FE <-->|SSE progress| API
    FE -->|PayPal JS SDK approval UI| PP[PayPal Sandbox]
    API --> DB[(PostgreSQL)]
    API --> AG[Agent Orchestrator]
    AG --> LLM[Tool-calling LLM]
    AG --> C3[Channel3 Adapter]
    C3 --> CAPI[Channel3 API]
    API --> GR[Deterministic Guardrails]
    API --> K[KERNEL Verification Adapter]
    K --> WEB[Retailer Product Page]
    API --> PAY[PayPal Service]
    PAY <-->|OAuth, create, capture, refund| PP
    PP -->|Verified webhook| WH[Webhook Processor]
    WH --> DB
    API --> AUD[Audit Service]
    AUD --> DB
```

### Request-to-receipt sequence

```mermaid
sequenceDiagram
    actor User
    participant UI as React UI
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Agent as Agent + LLM
    participant C3 as Channel3
    participant Guard as Guardrails
    participant K as KERNEL (optional)
    participant PP as PayPal Sandbox

    User->>UI: Save mandate and submit shopping request
    UI->>API: POST /api/requests
    API->>DB: Save request
    API-->>UI: 202 Accepted + request_id
    UI->>API: GET /api/requests/{id}/stream
    API->>Agent: Start agent run
    Agent->>C3: Search products
    C3-->>Agent: Products and retailer offers
    Agent->>C3: Retrieve selected product details
    C3-->>Agent: Refreshed product and offers
    Agent->>Guard: Candidate and offer facts
    Guard-->>Agent: Allow/block + reasons
    opt Retailer verification enabled
        Agent->>K: Verify exact retailer offer page
        K-->>Agent: Visible title, price, stock, timestamp, evidence
    end
    Agent->>DB: Save candidates, checks, proposal
    API-->>UI: SSE proposal_ready event
    User->>UI: Review and click PayPal button
    UI->>API: POST /api/proposals/{id}/order
    API->>C3: Re-fetch canonical product and offer
    C3-->>API: Current offer facts
    API->>Guard: Revalidate and reserve budget
    Guard-->>API: Pass/fail
    API->>PP: Create PayPal order (server-side)
    PP-->>API: PayPal order ID
    API-->>UI: PayPal order ID
    UI->>PP: Buyer approves in PayPal popup
    PP-->>UI: onApprove callback
    UI->>API: POST /api/orders/{id}/capture
    API->>PP: Capture order (server-side)
    PP-->>API: Capture status
    API->>DB: Save capture result
    PP->>API: PAYMENT.CAPTURE.COMPLETED webhook
    API->>PP: Verify webhook signature
    API->>DB: Deduplicate event and reconcile order
    API-->>UI: Receipt/order status available
```

---

# 4. Frontend modules

## Module F1 — Application shell, navigation, and user session

### Purpose

Provide the overall application layout and route users to the shopping request, mandate settings, approval, receipt, and history screens.

### Screens / components

- `AppLayout`: shared header, side navigation, responsive content area.
- `DashboardPage`: current mandate, remaining budget, latest request, latest order.
- `RequestPage`: new shopping request and agent progress.
- `MandatePage`: create/edit active spending mandate.
- `ProposalPage`: compare products and inspect the selected proposal.
- `CheckoutPage`: PayPal Buttons and payment state.
- `ReceiptPage`: final payment result and retailer destination link.
- `HistoryPage`: requests, proposals, orders, and audit trail.
- `SettingsPage`: environment-independent user settings, currency display, and optional integrations status.

### Required behavior

- Keep navigation visible and consistent on desktop and mobile.
- Show the active mandate state and remaining spend amount wherever payment decisions are displayed.
- Load sensitive user-owned data only through authenticated API requests.
- Display clear loading, empty, success, and error states.
- Do not store PayPal client secret, PayPal access tokens, Channel3 key, or LLM key in the frontend.

### Acceptance criteria

- A user can move between all main screens without losing a saved request or proposal.
- Refreshing a page restores its state from the backend.
- A user cannot view another user's mandate, request, proposal, or order by changing an ID in the URL.

---

## Module F2 — Mandate settings panel

### Purpose

Let the user define the boundaries within which the agent may search and propose purchases.

### Inputs

| Field | Type | Validation |
|---|---|---|
| Total budget | Decimal | Greater than zero; no more than configured maximum |
| Currency | Select | One supported currency; fixed for this mandate |
| Per-item cap | Decimal | Greater than zero and no more than total budget |
| Allowed categories | Multi-select | At least one category, unless an explicit all-categories mode is selected |
| Blocked categories | Multi-select (optional) | Must not contradict allowed categories |
| Allowed retailers | Multi-select/text list (optional) | Normalize domains; reject malformed domains |
| Mandate expiry | Date/time | Must be in the future |
| Maximum quantity per product | Integer | Greater than or equal to 1 |
| Price change tolerance | Percentage or fixed amount | Default 0%; any increase beyond configured tolerance forces re-approval |

### User experience

- Show a plain-language summary before saving, for example: “The agent may recommend products in Home and Electronics up to $80 total, no more than $40 per item, until 30 November.”
- Display the previous mandate's usage and active/pending reservations.
- Saving a changed mandate creates a new version. Do not overwrite the mandate rules that were used for an existing proposal or payment.
- Require confirmation before reducing a budget below the amount already spent or reserved.

### Backend interaction

- `POST /api/mandates` creates a new mandate version or updates the active one using version control.
- `GET /api/mandates/current` loads the active mandate.
- The backend returns the canonical saved values; the UI must not assume that the submitted values were accepted unchanged.

### Validation ownership

Frontend validation improves usability. The backend repeats every validation and is authoritative.

### Acceptance criteria

- Invalid caps, categories, currency, and expiry are rejected by the API.
- A request cannot start without an active, unexpired mandate.
- The proposal screen always shows the mandate version and checks used for that proposal.

---

## Module F3 — Shopping request panel and agent progress

### Purpose

Allow the user to describe a shopping goal in natural language and follow the agent's work as it searches and compares products.

### Example request

> “Find a desk lamp for a student room, warm light, adjustable brightness, under $40. Prefer a reliable retailer and a compact design.”

### UI elements

- Text input with a practical character limit.
- Optional structured fields: category, maximum price, preferred brand, preferred retailer, required attributes.
- Submit button and cancel button.
- Progress timeline with events such as:
  - Understanding the request
  - Checking mandate
  - Searching Channel3
  - Comparing retailer offers
  - Refreshing product details
  - Checking price and availability
  - Running purchase rules
  - Preparing proposal
- Error panel with a retry action where appropriate.

### API workflow

1. Submit request to `POST /api/requests`.
2. Receive `request_id` and status `queued` or `running`.
3. Open `GET /api/requests/{request_id}/stream` using Server-Sent Events.
4. Render progress events as they arrive.
5. On `proposal_ready`, fetch the request and proposal details.
6. On `blocked`, `no_match`, or `failed`, show the backend's safe reason and next action.

### SSE event contract

Each SSE message should include an `event` name and JSON `data`. Recommended event names:

- `request_started`
- `mandate_checked`
- `search_started`
- `search_results_received`
- `candidate_refreshed`
- `candidate_rejected`
- `guardrail_passed`
- `guardrail_blocked`
- `verification_started`
- `verification_completed`
- `proposal_ready`
- `request_blocked`
- `request_failed`
- `heartbeat`

Example payload:

```json
{
  "request_id": "req_123",
  "step": "price_check",
  "message": "Refreshing the selected retailer offer before preparing the proposal.",
  "progress": 70,
  "created_at": "2026-11-03T15:00:00Z"
}
```

### UI rules

- Progress messages must describe the actual backend action, not fabricated LLM status text.
- Do not show “purchase complete” during the agent search phase.
- The user may cancel an agent run before a proposal is committed.
- Reconnecting to the SSE stream should resume from stored request events or safely reload the current request state.

### Acceptance criteria

- User can submit a request and see progress without refreshing.
- If the stream disconnects, the UI reconnects or fetches current state.
- When the request completes, the UI shows either a valid proposal or an explicit no-match/block reason.

---

## Module F4 — Product results and comparison view

### Purpose

Display products, their retailer offers, the agent's reasoning, and the products or offers that were rejected by deterministic checks.

### Product card fields

- Product image and title
- Brand and product category
- Product attributes relevant to the request
- Canonical Channel3 product ID (not necessarily shown to the user)
- Retailer domain/name
- Offer amount and currency
- Availability
- New/used/refurbished condition
- Buy/retailer link
- Last refreshed timestamp
- Match explanation
- Policy result and rejection reason, where relevant

### Comparison behavior

- Treat one canonical Channel3 product and each retailer offer as separate comparison choices.
- Show the same product from multiple retailers as multiple offers under one product group.
- Compare only compatible amounts and currencies. Never rank a USD offer against a GBP offer as if the numbers were equivalent.
- Show the selected offer and at least one viable alternative when available.
- For rejected choices, explain the concrete cause: out of stock, too expensive, excluded category, disallowed retailer, wrong condition, failed attribute requirement, or failed retailer verification.

### Selection behavior

The user may choose another candidate only if it passed the deterministic checks. Changing the chosen product or offer invalidates the old proposal and creates a new proposal version. The frontend sends the selected proposal/candidate identifier, not a trusted price.

### Acceptance criteria

- The displayed price and availability come from the backend's latest Channel3 response.
- Rejected offers show specific reasons rather than a generic “not eligible”.
- The UI cannot alter the proposal amount by editing browser state or request payloads.

---

## Module F5 — Proposal review and approval screen

### Purpose

Give the user a final view of the exact product and retailer offer that the server is prepared to charge for through PayPal.

### Required display

- Product name, image, selected variant, and quantity
- Selected retailer domain and retailer link
- Current offer price, currency, and any explicitly known shipping/tax values
- Total amount calculated by the server
- Last Channel3 refresh time
- KERNEL verification status when enabled
- Mandate checks: total budget, per-item cap, category, retailer, expiry, quantity, availability, price tolerance
- Agent's explanation and alternative products
- Notice that the PayPal Sandbox payment goes to the demo merchant and does not place the retailer's order

### Actions

- “Continue with PayPal” renders the PayPal Buttons and starts the create-order callback.
- “Choose another option” returns to eligible alternatives.
- “Reject proposal” marks the proposal rejected.

### Important distinction

The proposal review button is not a payment. The PayPal Buttons create a PayPal order, then the buyer must approve in the PayPal popup. The server captures only after the SDK's `onApprove` callback reaches the backend.

### Acceptance criteria

- The exact amount about to be sent to PayPal is visible before the PayPal approval window.
- If revalidation fails, the PayPal Buttons are not rendered or are disabled and a fresh proposal is requested.
- The user can reject without creating a PayPal order.

---

## Module F6 — PayPal checkout component

### Purpose

Integrate PayPal's buyer-facing approval UI while keeping all server credentials and payment operations on the backend.

### Component

Use `PayPalScriptProvider` and `PayPalButtons` from `@paypal/react-paypal-js`.

### Callback responsibilities

**`createOrder`**

- Call `POST /api/proposals/{proposal_id}/order`.
- Backend reloads proposal and mandate, refreshes the product/offer, reruns guardrails, reserves budget, and creates the PayPal order.
- Return only the PayPal order ID to the SDK.

**`onApprove`**

- Send the PayPal order ID and the app's internal order ID to `POST /api/orders/{order_id}/capture`.
- Backend calls PayPal capture API using server OAuth token.
- Frontend does not call the PayPal capture REST endpoint directly.

**`onCancel`**

- Notify the backend that the buyer cancelled, if supported by the current order state.
- Leave the proposal available for a controlled retry only if no order/capture was completed. Do not create duplicate order records.

**`onError`**

- Display a recoverable error.
- Fetch internal order status before offering a retry because the network may have failed after PayPal created an order.

### Acceptance criteria

- A sandbox buyer can approve the payment.
- The browser never receives the PayPal client secret or access token.
- Double-clicks and network retries do not create duplicate captures.

---

## Module F7 — Order status, receipt, and refund action

### Purpose

Show the final state of the PayPal transaction and provide a controlled way to request a refund.

### Receipt fields

- Internal order ID
- PayPal order ID
- PayPal capture ID
- Product name and selected retailer offer
- Captured amount and currency
- Payment status
- Capture timestamp
- Retailer link
- Sandbox/demo fulfilment note
- Refund state, when applicable

### Statuses to display

- Awaiting buyer approval
- Buyer cancelled
- Payment processing
- Payment completed
- Payment failed
- Refund processing
- Refunded
- Refund failed / requires support

### Refund action

- Show the action only for a completed captured payment that is eligible for refund.
- For the first version, implement full refunds only unless partial refunds are explicitly required.
- Confirm the refund with the user before calling the API.
- The backend uses the saved capture ID and amount; it never accepts a browser-supplied capture amount as authoritative.

### Important wording

This refund returns the PayPal Sandbox payment made to the demo merchant. It does not automatically request a refund from the external retailer because the app has not placed an order on that retailer's system.

---

## Module F8 — History and audit dashboard

### Purpose

Give the user a transparent record of requests, recommendations, approvals, payments, refunds, and blocked decisions.

### Views

1. **Requests:** original text, created date, status, mandate version.
2. **Candidate comparison:** products/retailer offers considered and reasons for rejection.
3. **Orders:** product, amount, PayPal order/capture IDs, and payment status.
4. **Audit timeline:** each meaningful agent and server action with timestamp and result.

### Filters

- Date range
- Request status
- Order status
- Category
- Retailer
- Mandate version

### AG Grid

AG Grid Community can be used for sortable, filterable order history. Do not make AG Grid a hard dependency for the core purchase logic. A standard React table is acceptable if setup or time becomes a problem.

### Acceptance criteria

- Every order and proposal can be traced back to its request and mandate version.
- Blocked decisions remain visible in history.
- The UI distinguishes a recommendation, a PayPal order, a captured payment, and a refund.

---

# 5. Backend modules

## Module B1 — API routes and request validation

### Purpose

Expose a small REST API for the frontend and an SSE endpoint for agent progress. Keep business logic out of route handlers; routes should validate input, call a service, and return a typed response.

### Responsibilities

- Request and response schema validation with Pydantic.
- Authentication and ownership checks.
- Consistent error format.
- Rate limiting on request creation and expensive external calls.
- SSE streaming and cancellation.
- API versioning under `/api`.

### Core endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Health check; no secrets |
| `GET` | `/api/mandates/current` | Load current active mandate |
| `POST` | `/api/mandates` | Create/update mandate version |
| `POST` | `/api/requests` | Create request and start agent run |
| `GET` | `/api/requests/{request_id}` | Current request state |
| `GET` | `/api/requests/{request_id}/stream` | SSE progress stream |
| `POST` | `/api/requests/{request_id}/cancel` | Cancel an active agent run |
| `GET` | `/api/requests/{request_id}/candidates` | Candidates and comparison data |
| `GET` | `/api/proposals/{proposal_id}` | Proposal and policy checks |
| `POST` | `/api/proposals/{proposal_id}/order` | Revalidate and create PayPal order |
| `POST` | `/api/orders/{order_id}/capture` | Capture after buyer approval |
| `POST` | `/api/orders/{order_id}/refund` | Refund completed capture |
| `GET` | `/api/orders` | Order history |
| `GET` | `/api/orders/{order_id}` | One order/receipt |
| `POST` | `/api/webhooks/paypal` | Receive and verify PayPal events |

### Example: create request

Request:

```json
{
  "text": "Find a desk lamp for a student room, warm light, adjustable brightness, under $40.",
  "filters": {
    "category": "Home",
    "max_price": "40.00",
    "currency": "USD"
  }
}
```

Response (`202 Accepted`):

```json
{
  "request_id": "req_123",
  "status": "queued",
  "stream_url": "/api/requests/req_123/stream"
}
```

### Example: create PayPal order

Request:

```json
{
  "checkout_attempt_id": "attempt_123"
}
```

The client does not send `amount`, `currency`, `product_price`, `capture_id`, or `paypal_client_secret`. These values are loaded or calculated by the backend.

Response:

```json
{
  "order_id": "ord_internal_123",
  "paypal_order_id": "PAYPAL_ORDER_ID",
  "status": "created",
  "amount": "32.50",
  "currency": "USD"
}
```

### Error format

Use a consistent structure:

```json
{
  "error": {
    "code": "OFFER_PRICE_CHANGED",
    "message": "The retailer offer changed after the proposal was prepared.",
    "retryable": true,
    "details": {
      "proposal_id": "prop_123"
    }
  }
}
```

Do not return provider secrets, stack traces, raw access tokens, or sensitive webhook contents.

---

## Module B2 — Authentication and user ownership boundary

### Purpose

Ensure mandates, requests, proposals, and orders belong to the signed-in user.

### Minimum hackathon implementation

- Create a lightweight user/session mechanism suitable for the demo.
- Resolve the current user on the backend for every protected request.
- Use a secure, HTTP-only session cookie or validated bearer token.
- Never trust a `user_id` supplied in the request body.

### Production requirements

- Passwordless email/OAuth identity provider or another maintained authentication provider.
- CSRF protection if cookie-based authentication is used.
- Session rotation, logout, and expiry.
- Ownership checks in every service method and SQL query.

### Development-only fallback

A single seeded demo user may be used locally, but it must be clearly isolated behind a development configuration. Do not silently ship a public app in which every visitor shares the same mandate and order history.

---

## Module B3 — Mandate service

### Purpose

Store, version, retrieve, and validate spending rules independently from the LLM.

### Core operations

- `create_mandate(user_id, mandate_input)`
- `get_active_mandate(user_id)`
- `get_mandate_version(mandate_id, version)`
- `validate_mandate_is_active(mandate)`
- `calculate_available_budget(mandate_id)`
- `revoke_mandate(mandate_id, user_id)`

### Mandate rule set

- Total budget.
- Currency.
- Per-item spending cap.
- Allowed categories and blocked categories.
- Optional allowed retailer domains.
- Expiration time.
- Maximum quantity per product.
- Price-change tolerance.

### Versioning

When a user edits the mandate, create a new version instead of modifying the old version used by an existing request or proposal. Every request records the mandate ID and version. This makes the decision auditable later.

### Available budget calculation

The budget calculation must account for:

- Captured/completed payments during the mandate period.
- Active reservations for checkout orders or pending purchases.
- Released reservations from expired, rejected, cancelled, or failed orders.

Use a database transaction and row-level lock when reserving budget so two concurrent requests cannot both spend the same remaining amount.

### Acceptance criteria

- An expired or revoked mandate blocks new proposals and new orders.
- A mandate edit does not retroactively rewrite old proposal rules.
- The backend rejects all requests that exceed the total or per-item cap.

---

## Module B4 — Request lifecycle and orchestration service

### Purpose

Manage a request from submission to proposal, including progress events, timeouts, cancellation, and failures.

### Request lifecycle

`queued → running → proposal_ready | no_match | blocked | failed | cancelled`

### Responsibilities

- Validate that the user has a current active mandate.
- Snapshot the mandate version for the request.
- Persist the original user request and normalized filters.
- Start the agent run in a controlled background task/worker.
- Persist each progress event before publishing it through SSE.
- Stop work after cancellation, timeout, or the maximum tool-call budget.
- Save candidates and final proposal in a transaction.

### Background execution

For a small prototype, FastAPI background tasks or an asyncio task can run the agent. For a deployment that must survive restarts or handle multiple concurrent jobs, move the execution to a durable worker queue such as Redis-backed jobs or Render Workflows. The request state must live in PostgreSQL, not only in process memory.

### SSE requirements

- Send heartbeats to keep the stream open.
- Support reconnect using event IDs or reload the latest request state.
- Do not leak events between users.
- Stop publishing after terminal request state.

---

## Module B5 — Agent loop and LLM tool gateway

### Purpose

Translate a natural-language shopping request into one or more product searches, evaluate candidates, and produce a purchase proposal.

### Allowed tools

Only these shopping tools are available to the LLM:

1. `search_products(query, max_price, currency, filters)`
2. `get_product(product_id, locale, selected_variant)`
3. `propose_purchase(product_id, offer_key, quantity, rationale)`

The agent may also use a non-mutating `compare_candidates(candidate_ids)` helper if useful. It must not have `create_paypal_order`, `capture_payment`, `refund_payment`, direct SQL, shell, or arbitrary HTTP tools.

### Tool contracts

**`search_products`**

Input:

```json
{
  "query": "adjustable warm-light desk lamp",
  "max_price": "40.00",
  "currency": "USD",
  "filters": {
    "availability": ["InStock"],
    "category": "Home"
  }
}
```

Output: normalized candidate summaries with Channel3 product ID, product title, product attributes, offers, retailer domain, price, currency, availability, condition, and source timestamp.

**`get_product`**

Input:

```json
{
  "product_id": "2yh8WH5",
  "locale": {
    "country": "US",
    "language": "en",
    "currency": "USD"
  }
}
```

Output: current Channel3 product detail and offers. If a variant is required, the adapter resolves the selected variant using Channel3's documented variant parameters and records the resolved selection.

**`propose_purchase`**

Input:

```json
{
  "product_id": "2yh8WH5",
  "offer_key": "offer_abc",
  "quantity": 1,
  "rationale": "It matches the warm-light and adjustable-brightness requirements and is within the requested price range."
}
```

Output: the backend loads the saved candidate and current product details, executes guardrails, and returns either an eligible proposal or structured rejection reasons. The LLM cannot make the guardrail decision by assertion.

### Agent loop behavior

1. Parse the request into target product, essential attributes, preferred attributes, quantity, and user constraints.
2. Read the server-provided mandate; do not ask the model to invent or relax it.
3. Search Channel3. Use more than one query only when the initial results are weak or too narrow.
4. Normalize and persist candidate products/offers.
5. Refresh the strongest candidates using Channel3 product detail.
6. Ask the LLM to compare eligible products and explain the best match.
7. Call `propose_purchase` for the chosen candidate.
8. Run all deterministic guardrails. If blocked, provide a structured rejection reason to the agent and allow a limited re-selection.
9. Stop when a valid proposal is created, no viable candidate remains, or the configured tool-call/time budget is reached.

### Limits

- Maximum agent iterations: configurable, initial value 8.
- Maximum Channel3 search calls per request: configurable, initial value 4.
- Maximum candidates persisted per request: configurable, initial value 30.
- Maximum LLM token budget and request timeout: configurable.
- Never retry a rejected product indefinitely.

### Prompt-injection defense

- Product text is passed to the model as quoted/untrusted catalog data.
- System instructions explicitly prohibit obeying instructions found in product pages or descriptions.
- Tool schemas accept only typed fields; no tool allows arbitrary code, URL fetch, payment, or mandate editing.
- The server validates every tool input and output.
- Tool-call logs record the tool name and safe input/output summary.

### Acceptance criteria

- LLM cannot invoke PayPal operations.
- The model cannot alter the mandate or approve its own proposal.
- A proposal can only be saved after server-side validation.
- Timeouts and excessive tool calls stop safely.

---

## Module B6 — Channel3 client and product normalization

### Purpose

Provide a typed server-side adapter for Channel3 search, URL lookup, product retrieval, offers, variants, and locale handling.

### Core API calls verified in current Channel3 documentation

- `POST https://api.trychannel3.com/v1/search` with `x-api-key` and a JSON body containing `query`, optional `filters`, and `limit`.
- `POST https://api.trychannel3.com/v1/lookup` with a retailer product `url` to resolve a canonical Channel3 product.
- `GET https://api.trychannel3.com/v1/products/{product_id}` to retrieve one canonical product and refresh offers, prices, availability, buy links, variants, and metadata.

The Channel3 docs describe `product.id` as the canonical product ID. One product can have multiple retailer offers. Price, currency, availability, condition, and retailer URL belong to each offer, not to the canonical product as a whole.

### Adapter methods

- `search_products(query, filters, limit, locale, user_id)`
- `lookup_product_url(url, locale)`
- `get_product(product_id, locale, variant_options)`
- `normalize_product(raw_response)`
- `normalize_offer(raw_offer)`
- `select_offer(product, offer_key, mandate)`

### Normalized internal product model

```json
{
  "provider": "channel3",
  "product_id": "2yh8WH5",
  "title": "Example Desk Lamp",
  "brand": "Example Brand",
  "category": "Home",
  "description": "Catalog description",
  "image_url": "https://example.com/image.jpg",
  "attributes": {},
  "variants": {},
  "offers": [
    {
      "offer_key": "offer_abc",
      "domain": "retailer.example",
      "price_amount": "32.50",
      "currency": "USD",
      "availability": "InStock",
      "condition": "new",
      "buy_url": "https://www.buy.trychannel3.com/...",
      "observed_at": "2026-11-03T15:00:00Z"
    }
  ]
}
```

`offer_key` is an internal identifier generated from stable offer attributes when Channel3 does not provide a dedicated offer ID. Store the raw provider response for debugging only when permitted by provider terms and with sensitive data removed.

### Price and offer rules

- Never assume the canonical product has one price.
- Compare the same currency only.
- Filter retailer offers by availability, allowed retailer, condition, and price.
- Persist the specific retailer offer selected by the user/agent.
- Immediately before PayPal order creation, retrieve the canonical product again and locate the same retailer offer. If the offer disappeared, is no longer available, changed currency, or exceeded tolerance, mark the proposal stale and require a new proposal.
- Do not silently switch to a different retailer offer or seller at checkout. A different offer requires a new proposal and user review.

### Locale handling

Pass the configured country, language, and currency when supported. Record which locale was used for the offer refresh. Do not display converted prices as if they were retailer prices.

### Reliability

- Set connection/read timeouts.
- Retry only transient errors with bounded exponential backoff.
- Treat rate-limit responses according to Channel3's current documentation.
- Cache search responses briefly for display, but do not use cached values for final proposal/order validation.
- Log provider request IDs and status codes, but never log API keys.

---

## Module B7 — Candidate ranking and explanation service

### Purpose

Turn Channel3 results into a comprehensible comparison list and help the LLM explain the strongest choice.

### Ranking inputs

- Required-attribute match
- Price relative to request/mandate cap
- Availability
- Retailer allowlist match
- Product condition
- User's explicit preferences in the current request
- Completeness and freshness of product data

### Recommended approach

1. Deterministic pre-filter: remove offers that fail hard rules (out of stock, wrong currency, above cap, blocked category/retailer, wrong condition).
2. Ranking: use a transparent score or LLM ordering over only eligible options. The LLM can explain trade-offs but does not decide whether an option is eligible.
3. Explanation: generate one short explanation tied to observable product attributes and policy results.
4. Persist both the selected option and rejected alternatives with their rejection reasons.

### Example explanation

“Selected because it supports adjustable brightness, is listed as in stock, and the selected retailer offer is $32.50, below the $40 request limit. The $28 alternative was excluded because it is marked refurbished.”

Do not claim shipping speed, warranty, authenticity, safety, or product quality unless a reliable data source provides that fact.

---

## Module B8 — Deterministic guardrails and policy engine

### Purpose

Enforce purchase rules in ordinary backend code. This is the security boundary between the LLM's recommendation and payment creation.

### Pure-function design

Implement rules as deterministic functions with structured results. They should not call the LLM or external APIs.

Suggested interface:

```python
check_proposal(
    mandate=mandate_snapshot,
    product=refreshed_product,
    offer=selected_offer,
    quantity=quantity,
    request=request_snapshot,
    now=utc_now,
) -> GuardrailResult
```

Each check returns:

```json
{
  "rule": "PER_ITEM_CAP",
  "passed": true,
  "actual": "32.50",
  "limit": "40.00",
  "reason": "Offer price is within the per-item cap."
}
```

### Required checks

| Check | Logic | Failure action |
|---|---|---|
| Mandate active | Not revoked and not expired | Block |
| Currency | Offer currency equals mandate currency | Block; no implicit FX |
| Total budget | Captured spend + active reservations + new total does not exceed mandate budget | Block |
| Per-item cap | Unit price does not exceed per-item cap | Block |
| Quantity | Positive integer and no more than mandate max quantity | Block |
| Category | Category is allowed and not blocked | Block |
| Retailer | Offer domain is allowed when an allowlist exists | Block |
| Availability | Exact offer is `InStock` | Block |
| Condition | Meets request and mandate condition rules | Block |
| Price freshness | Refreshed offer is current enough for checkout | Refresh or block |
| Price drift | Current offer has not exceeded saved proposal amount beyond tolerance | Mark stale; require new proposal |
| Product identity | Same canonical product and selected variant | Block/require new proposal |
| Offer identity | Same selected retailer offer; no silent retailer substitution | Block/require new proposal |
| KERNEL verification | When enabled, visible retailer details match the selected offer | Block or mark needs review |

### Total cost calculation

Use `Decimal`, not floating-point arithmetic.

`line_total = unit_price × quantity`

For the first version, only include additional costs (shipping, taxes, fees) when they are explicitly available and can be represented accurately. If the Channel3 offer does not include those charges and the retailer page is not being used to compute them, label the amount as the product-offer subtotal rather than claiming it is the final retailer checkout total.

### Guardrail results

- `PASS`: all mandatory checks passed.
- `BLOCK`: one or more hard rules failed.
- `REVIEW`: optional verification is inconclusive or a configured warning needs a user decision.
- `STALE`: facts changed after the proposal; create a fresh proposal.

### Budget reservation

At PayPal order creation, begin a database transaction, lock the mandate row, recompute spent and reserved budget, rerun policy checks, and reserve the exact amount. Release the reservation if the buyer cancels, the PayPal order expires/fails, or the proposal is invalidated. Convert the reservation to captured spend after payment completion.

### Acceptance criteria

- Unit tests cover all individual rules and combinations.
- No code path can call PayPal create/capture unless the latest guardrail result is `PASS`.
- Any price or offer change forces a new proposal or explicit re-approval.

---

## Module B9 — Proposal service and KERNEL retailer verification

### Part A: Proposal service

#### Purpose

Create an immutable proposal snapshot after the agent selects a candidate and guardrails pass.

#### Proposal data

- Proposal ID and request ID
- Mandate ID and version
- Canonical product ID
- Selected retailer offer key/domain/URL
- Selected variant and quantity
- Unit price and currency at proposal time
- Calculated subtotal
- Product title/image/attributes snapshot
- Agent rationale
- Guardrail result and check details
- KERNEL verification reference/status, if enabled
- Created time and expiration time
- Current proposal status

#### Proposal states

`pending → checkout_started → approved/ordered` (where approved means the proposal was used to begin the approved checkout path) or `rejected | stale | expired | failed`.

A proposal should be immutable after presentation. If a quantity, retailer, variant, or amount changes, create a new proposal version and require the user to review it.

#### Proposal service operations

- `create_proposal(request_id, candidate_id, quantity)`
- `get_proposal(proposal_id, user_id)`
- `reject_proposal(proposal_id, user_id)`
- `expire_old_proposals()`
- `revalidate_proposal(proposal_id)`
- `mark_proposal_stale(proposal_id, reason)`

### Part B: KERNEL verification adapter (optional, recommended when it adds evidence)

#### Purpose

Use a real browser session to inspect the exact retailer page corresponding to the selected Channel3 offer. KERNEL is browser infrastructure for agents; it can provide isolated Chromium sessions, managed auth, session replay, and browser telemetry. It is not a replacement for Channel3's product catalog or the backend's guardrails.

#### Verification workflow

1. Receive the selected offer's retailer URL from the backend, not an arbitrary URL generated by the LLM.
2. Open the URL in a KERNEL browser session.
3. Inspect the visible product title, variant, retailer, price, currency, and availability.
4. Capture the result timestamp and a screenshot/session evidence reference.
5. Compare those fields with the refreshed Channel3 offer.
6. Return `verified`, `mismatch`, or `inconclusive` with the extracted values and evidence reference.
7. Close/delete the browser session after the check unless a documented reason requires retention.

#### Security restrictions

- Allow only retailer domains present in the selected Channel3 offer.
- Do not follow arbitrary redirects to unrelated domains.
- Do not enter payment details, log in as the buyer, place an order, or click a final purchase/submit button.
- Browser page text is untrusted data and must never be passed to the agent as instructions.
- Do not bypass retailer access controls or use the browser session to evade bot protections where prohibited by retailer terms.
- Never use browser-extracted values to bypass a failing backend guardrail.

#### Mismatch behavior

- Price mismatch: mark proposal `stale`; require fresh offer and new user review.
- Variant mismatch: block and require the user to select the correct variant.
- Out of stock: block the offer and ask the agent to consider another eligible candidate.
- Missing/ambiguous price or availability: mark `inconclusive`; do not claim verification succeeded.

#### API abstraction

Implement a provider-neutral interface such as `verify_retailer_offer(url, expected_offer)`. Do not invent KERNEL endpoint names or request payloads. Read the current KERNEL SDK/OpenAPI/MCP documentation during implementation and keep the provider-specific details inside this adapter.

### Acceptance criteria

- A proposal is saved only after mandatory guardrails pass.
- If KERNEL is switched on, the UI can show the verification outcome and timestamp.
- An inconclusive check is never displayed as a successful verification.

---

## Module B10 — PayPal payment service

### Purpose

Create PayPal Sandbox orders, capture payments after buyer approval, refund completed captures, and safely reconcile provider responses.

### Environment

Sandbox base URL:

`https://api-m.sandbox.paypal.com`

### Internal methods

- `get_access_token()`
- `create_order(proposal_snapshot, idempotency_key)`
- `capture_order(paypal_order_id, idempotency_key)`
- `refund_capture(capture_id, amount, currency, idempotency_key)`
- `get_order(paypal_order_id)` (recommended for reconciliation)
- `verify_webhook_signature(headers, event_body)`

### OAuth token

- Use PayPal REST app client ID and secret from backend environment variables.
- Obtain an OAuth 2.0 access token using client credentials.
- Cache the token only on the server until shortly before its expiry.
- Never expose the token to the frontend or write it to logs.

### Create order flow

1. Receive an internal proposal ID.
2. Load the proposal, request, mandate snapshot, and selected offer from PostgreSQL.
3. Confirm the proposal belongs to the current user and is eligible for checkout.
4. Retrieve the product from Channel3 and identify the exact selected offer again.
5. Run all guardrails again.
6. Lock the mandate row and reserve the exact amount in a PostgreSQL transaction.
7. Create a PayPal order with `intent: "CAPTURE"` and a `purchase_units` amount derived from the stored/refreshed server-side amount.
8. Send a stable `PayPal-Request-Id` for the logical create-order operation.
9. Persist the PayPal order ID and return it to the frontend.

The PayPal API request should contain a single purchase unit for the proposal's amount. Add a concise description and internal reference identifiers where supported. Do not copy retailer shipping or tax amounts unless they are known and included in the proposal snapshot.

### Capture flow

1. Receive the internal order ID from the frontend after the PayPal SDK `onApprove` event.
2. Load the order and PayPal order ID from the database.
3. Check that the order is in a capturable state and not already captured/refunded.
4. Use a stable capture idempotency key for this internal order.
5. Call the PayPal Orders v2 capture endpoint from the backend.
6. Persist the returned capture ID, amount, currency, and status.
7. Mark completed only when the PayPal response confirms a completed capture; otherwise set a pending/failed state and reconcile through a follow-up order read or webhook.

### Refund flow

1. Confirm the internal order is captured and refundable.
2. Load the capture ID and captured amount from the database.
3. For the first version, issue a full refund.
4. Use a stable idempotency key for that refund operation.
5. Persist the refund ID and result.
6. Do not mark refunded until PayPal confirms the refund state.

### Idempotency

Use `PayPal-Request-Id` on create, capture, and refund POST operations. Persist each logical idempotency key before or as part of the database operation. Reuse the same key when retrying the same logical action; do not generate a new key for every network retry. Also enforce a database uniqueness constraint so one proposal cannot create two internal orders and one order cannot be captured twice.

### Payment security

- PayPal API calls happen server-side.
- Never trust a price, amount, currency, capture ID, or status from the frontend.
- Use a fixed Sandbox base URL from configuration; do not let an LLM or user-supplied URL select the PayPal host.
- Use `Decimal` and format PayPal amounts as strings with the correct currency precision.
- Log internal order ID and provider request ID, not access tokens or full sensitive payloads.

### Acceptance criteria

- Buyer approval in the PayPal popup is required before capture.
- Duplicate browser callbacks cannot create duplicate captures.
- Server-side amount exactly matches the validated proposal amount.
- Full refund works for a completed Sandbox capture.

---

## Module B11 — PayPal webhook processor

### Purpose

Receive asynchronous payment notifications from PayPal, verify authenticity, deduplicate events, and reconcile internal order state.

### Required setup

- Register the backend webhook URL in the PayPal Developer Dashboard.
- Store the returned `PAYPAL_WEBHOOK_ID`.
- Subscribe to at least `PAYMENT.CAPTURE.COMPLETED`; also subscribe to relevant denied/refunded events needed by the chosen implementation.

### Processing steps

1. Receive the original raw HTTP body and PayPal transmission headers.
2. Verify the signature using PayPal's documented verification process. For the simple implementation, call the PayPal `POST /v1/notifications/verify-webhook-signature` endpoint with the webhook ID, transmission headers, certificate URL, auth algorithm, signature, and webhook event. Alternatively, implement PayPal's self-cryptographic verification exactly as documented.
3. Reject invalid events without changing order state.
4. Insert the PayPal event ID into `webhook_events` with a unique constraint.
5. If the event was already processed, return success without repeating the state transition.
6. Match the capture/order reference to the internal order.
7. Apply an allowed state transition and write an audit event.
8. Return HTTP 2xx for a valid event after it is durably processed.

### Events to handle

- `PAYMENT.CAPTURE.COMPLETED`: confirm the captured payment.
- `PAYMENT.CAPTURE.DENIED`: mark capture failed/denied and release reservation if no payment settled.
- `PAYMENT.CAPTURE.REFUNDED`: reconcile the refund state.

### Duplicate and retry behavior

PayPal may retry webhook delivery. Use a unique provider event ID and idempotent state transitions. Do not assume events arrive once or in order. Never change an order from `refunded` back to `completed` because an older capture event arrived later.

### Acceptance criteria

- Invalid signatures do not update orders.
- Duplicate events are recorded once and do not duplicate ledger entries.
- A valid capture webhook reconciles an internal order even if the original frontend request timed out.

---

## Module B12 — Database, repositories, and persistence layer

### Purpose

Persist all state needed to resume a request, prove why a proposal was allowed/blocked, prevent duplicate payment, and display order history.

### Tables

The following is the recommended core schema. Names and columns can be adjusted during implementation, but the relationships and uniqueness constraints should be retained.

#### `users`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID, PK | Internal user ID |
| `email` | CITEXT/text, unique | If using email login |
| `created_at` | timestamptz | |
| `updated_at` | timestamptz | |

#### `mandates`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `user_id` | UUID, FK users | Owner |
| `version` | integer | Increment on every change |
| `total_budget` | numeric(12,2) | Never float |
| `per_item_cap` | numeric(12,2) | |
| `currency` | char(3) | ISO currency code |
| `allowed_categories` | jsonb | Category allowlist |
| `blocked_categories` | jsonb | Optional |
| `allowed_retailers` | jsonb | Optional normalized domains |
| `max_quantity_per_product` | integer | |
| `price_tolerance_pct` | numeric(7,4) | Default 0 |
| `expires_at` | timestamptz | |
| `status` | text | active, expired, revoked, superseded |
| `created_at` | timestamptz | |

Unique constraint: `(user_id, version)`.

#### `requests`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `user_id` | UUID, FK users | Owner |
| `mandate_id` | UUID, FK mandates | Exact version used |
| `request_text` | text | Original request |
| `normalized_intent` | jsonb | Extracted attributes/filters |
| `status` | text | queued, running, proposal_ready, no_match, blocked, failed, cancelled |
| `error_code` | text, nullable | Safe internal code |
| `created_at` | timestamptz | |
| `updated_at` | timestamptz | |

#### `request_events`

| Column | Type | Notes |
|---|---|---|
| `id` | bigserial, PK | SSE event sequence |
| `request_id` | UUID, FK requests | |
| `event_type` | text | e.g. search_started |
| `payload` | jsonb | Safe display payload |
| `created_at` | timestamptz | |

#### `candidates`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID, PK | Internal candidate ID |
| `request_id` | UUID, FK requests | |
| `provider_product_id` | text | Channel3 canonical product ID |
| `title` | text | Snapshot |
| `brand` | text, nullable | |
| `category` | text, nullable | |
| `image_url` | text, nullable | |
| `attributes` | jsonb | Snapshot |
| `rank_score` | numeric(8,4), nullable | Optional score |
| `rank_reason` | text, nullable | Explanation |
| `rejected_reason` | text, nullable | Why not eligible |
| `raw_snapshot` | jsonb | Sanitized provider fields if permitted |
| `observed_at` | timestamptz | |

Unique constraint: `(request_id, provider_product_id)` unless multiple variant snapshots require a variant-aware key.

#### `candidate_offers`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID, PK | Internal offer key |
| `candidate_id` | UUID, FK candidates | |
| `provider_offer_id` | text, nullable | If Channel3 exposes one |
| `domain` | text | Retailer domain |
| `buy_url` | text | Channel3 attributed offer URL |
| `price_amount` | numeric(12,2) | |
| `currency` | char(3) | |
| `availability` | text | InStock/OutOfStock/unknown |
| `condition` | text | new/used/refurbished/unknown |
| `variant_data` | jsonb | Selected option/variant |
| `observed_at` | timestamptz | |
| `is_eligible` | boolean | Deterministic result |
| `rejection_reason` | text, nullable | |

#### `proposals`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `request_id` | UUID, FK requests | |
| `user_id` | UUID, FK users | Ownership and query convenience |
| `mandate_id` | UUID, FK mandates | Immutable mandate version reference |
| `candidate_id` | UUID, FK candidates | |
| `offer_id` | UUID, FK candidate_offers | Exact selected offer |
| `quantity` | integer | |
| `unit_price_at_proposal` | numeric(12,2) | |
| `subtotal_at_proposal` | numeric(12,2) | |
| `currency` | char(3) | |
| `rationale` | text | Agent explanation |
| `guardrail_result` | jsonb | All rule results |
| `verification_result` | jsonb, nullable | KERNEL verification details |
| `status` | text | pending, checkout_started, rejected, stale, expired, failed, ordered |
| `expires_at` | timestamptz | |
| `created_at` | timestamptz | |

#### `orders`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID, PK | Internal ID |
| `proposal_id` | UUID, FK proposals, unique | One internal order per proposal |
| `user_id` | UUID, FK users | |
| `paypal_order_id` | text, unique, nullable | PayPal ID |
| `paypal_capture_id` | text, unique, nullable | Capture ID |
| `create_request_id` | text, unique | PayPal-Request-Id for create |
| `capture_request_id` | text, unique | PayPal-Request-Id for capture |
| `amount` | numeric(12,2) | Server-calculated amount |
| `currency` | char(3) | |
| `status` | text | created, buyer_approved, capture_pending, completed, failed, cancelled, refund_pending, refunded |
| `budget_reserved` | numeric(12,2) | Reserved mandate amount |
| `captured_at` | timestamptz, nullable | |
| `created_at` | timestamptz | |
| `updated_at` | timestamptz | |

#### `refunds`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `order_id` | UUID, FK orders | |
| `paypal_refund_id` | text, unique, nullable | |
| `request_idempotency_key` | text, unique | Stable retry key |
| `amount` | numeric(12,2) | |
| `currency` | char(3) | |
| `status` | text | pending, completed, failed |
| `created_at` | timestamptz | |

#### `webhook_events`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `provider_event_id` | text, unique | PayPal event ID |
| `event_type` | text | |
| `resource_id` | text, nullable | Capture/order/refund ID |
| `verified` | boolean | |
| `processed` | boolean | |
| `payload` | jsonb | Sanitized event body |
| `received_at` | timestamptz | |
| `processed_at` | timestamptz, nullable | |

#### `audit_events`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `user_id` | UUID, FK users | |
| `request_id` | UUID, nullable | |
| `proposal_id` | UUID, nullable | |
| `order_id` | UUID, nullable | |
| `event_type` | text | agent_tool_call, guardrail_passed, payment_created, etc. |
| `actor` | text | user, system, agent, paypal_webhook |
| `decision` | text, nullable | allow, block, info |
| `reason` | text, nullable | Human-readable reason |
| `details` | jsonb | Non-secret context |
| `created_at` | timestamptz | |

### Database constraints and indexes

- `orders.proposal_id` must be unique.
- `orders.paypal_order_id` must be unique when non-null.
- `orders.paypal_capture_id` must be unique when non-null.
- `webhook_events.provider_event_id` must be unique.
- Each PayPal logical operation's idempotency key must be unique.
- Monetary values use `numeric`, never `float`/`real`.
- Index request/order history by `(user_id, created_at DESC)`.
- Index `request_events` by `(request_id, id)` for SSE replay.
- Use foreign keys and explicit deletion rules. Prefer soft revocation for mandates and records that affect payments/audit.

---

## Module B13 — Audit logging and observability

### Purpose

Record what the agent attempted, what the server checked, and why a proposal was allowed or blocked.

### Events to record

- Mandate created, changed, revoked, or expired.
- Request submitted, cancelled, failed, or completed.
- Agent tool invocation and normalized result summary.
- Channel3 search/retrieve success or failure.
- Candidate accepted/rejected and reason.
- Every guardrail result.
- KERNEL verification result, if enabled.
- Proposal created, rejected, stale, or expired.
- PayPal order created, buyer cancelled, capture requested, capture completed/failed.
- Webhook received, verified, deduplicated, or rejected.
- Refund requested and completed/failed.

### Logging rules

- Do not log PayPal secrets, access tokens, user passwords, full card/payment data, or API keys.
- Keep audit facts distinct from diagnostic logs.
- Use structured logs with request ID, proposal ID, order ID, provider name, status, and elapsed time.
- Redact user request text from generic operational logs when it may contain personal information; store the original request only in the protected application table.
- Never let the LLM write or rewrite audit rows directly.

### Acceptance criteria

A reviewer can follow one order from original user request through mandate check, product selection, proposal, PayPal capture, and refund without relying on process logs alone.

---

## Module B14 — Background jobs and scheduled tasks

### Purpose

Handle work that should not block an HTTP request.

### Core-version jobs

- Expire old requests and proposals.
- Release budget reservations for expired/cancelled/failed orders.
- Reconcile orders whose capture response was ambiguous.
- Retry transient provider/webhook processing failures safely.

### Optional price-watch job

The supplied problem statement proposes a later price watcher. Keep the data model extensible, but do not make it a dependency of the first end-to-end demo. A later implementation can store watch rules, periodically call Channel3 product retrieval, compare current offer data with the recorded purchase/proposal, and create a price-drop alert or a drafted request. Do not promise an automatic retailer refund or price adjustment unless the retailer itself provides a supported process.

### Execution

For initial deployment, use a scheduled Render Cron Job or a durable worker. Every job must be idempotent and safe to run more than once.

---

## Module B15 — Evaluation and test harness

### Purpose

Measure whether the system follows the mandate and payment rules, not just whether the LLM produces plausible shopping text.

### Evaluation dataset

Start with at least 30 synthetic requests covering:

- Straightforward valid purchase.
- Product not found.
- No in-stock offer.
- Product over per-item cap.
- Basket/request over total budget.
- Expired mandate.
- Revoked mandate.
- Blocked category.
- Retailer not in allowlist.
- Disallowed used/refurbished condition.
- Wrong currency.
- Quantity above mandate maximum.
- Price increase after proposal.
- Offer disappears between proposal and checkout.
- Variant mismatch.
- KERNEL price mismatch or inconclusive result.
- Duplicate PayPal create callback.
- Duplicate capture callback.
- Buyer cancels PayPal popup.
- Capture failure.
- Duplicate webhook.
- Invalid webhook signature.
- Refund on completed payment.
- Refund requested for an uncaptured order.
- Prompt injection inside product description.

### Metrics

- Hard-rule violation count (must be zero).
- Total-budget adherence (must be 100%).
- Per-item-cap adherence (must be 100%).
- Duplicate order/capture count (must be zero).
- False-positive eligibility rate.
- Product match quality (manual or rubric-based evaluation).
- Search latency and total request latency.
- Provider error rate.
- Proposal freshness at checkout.
- Explanation faithfulness: every stated reason must be supported by product/offer facts.

### Testing layers

- Unit tests for pure guardrail functions.
- Adapter tests with mocked Channel3/PayPal/KERNEL responses.
- API integration tests with a temporary PostgreSQL database.
- PayPal Sandbox end-to-end test using sandbox buyer and merchant accounts.
- Frontend Playwright tests for request → proposal → checkout → receipt.
- Webhook tests for valid signature, invalid signature, duplicate event, and out-of-order event.

### Release gate

Do not deploy a release if any test permits an over-budget purchase, duplicate capture, payment without buyer approval, or order creation using a stale/changed offer.

---

# 6. End-to-end workflows in detail

## Workflow A — User creates a mandate

1. User opens Mandate Settings.
2. User enters total budget, per-item cap, currency, categories, optional retailers, max quantity, expiry, and price tolerance.
3. Frontend validates basic formatting.
4. Backend validates all fields, checks ownership, creates a new mandate version, and stores it.
5. Backend returns the normalized saved mandate.
6. Frontend shows the plain-language mandate summary and available budget.

## Workflow B — User starts a shopping request

1. User enters a natural-language request.
2. Frontend sends request text and optional request-specific constraints.
3. Backend verifies the active mandate and creates a request record using a snapshot of the mandate version.
4. Backend starts the agent job and returns a request ID.
5. Frontend opens the SSE stream.
6. Agent parses request intent and searches Channel3.
7. Channel3 results are normalized and persisted.
8. The agent compares candidates and refreshes product detail.
9. Guardrails filter out ineligible offers.
10. Optional KERNEL verification checks the exact retailer page for the selected offer.
11. Agent chooses an eligible candidate and submits a proposal request.
12. Proposal service independently validates and stores an immutable proposal.
13. Frontend receives `proposal_ready` and opens the comparison/proposal screen.

## Workflow C — User checks out with PayPal

1. User reviews the item, retailer, quantity, amount, mandate checks, and verification outcome.
2. User clicks Continue with PayPal.
3. PayPal SDK `createOrder` calls the backend.
4. Backend reloads the saved proposal and mandate snapshot.
5. Backend re-fetches Channel3 product details and locates the exact selected offer.
6. Backend reruns every guardrail. If anything changed, it marks the proposal stale and returns a clear error.
7. Backend locks the mandate budget row, reserves the amount, creates a PayPal order using the stored server-side amount, and persists the PayPal order ID.
8. PayPal popup asks the buyer to approve.
9. After approval, PayPal SDK `onApprove` calls the backend capture endpoint.
10. Backend captures using PayPal Orders v2 and saves the result.
11. PayPal webhook is verified, deduplicated, and reconciled.
12. Frontend displays the receipt only after a confirmed capture state.

## Workflow D — User requests a refund

1. User opens an eligible completed order.
2. User clicks Refund and confirms.
3. Backend verifies ownership and captured/refundable state.
4. Backend sends a refund request using the saved PayPal capture ID.
5. Backend persists refund status and reconciles the PayPal response/webhook.
6. Frontend displays Refunded only after confirmation.

---

# 7. Folder structure

```text
agentic-shopping-concierge/
├── client/
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   │   ├── App.tsx
│   │   │   ├── router.tsx
│   │   │   └── providers.tsx
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   ├── mandate/
│   │   │   ├── request/
│   │   │   ├── products/
│   │   │   ├── proposal/
│   │   │   ├── checkout/
│   │   │   ├── receipt/
│   │   │   └── history/
│   │   ├── hooks/
│   │   │   ├── useRequestStream.ts
│   │   │   └── useMandate.ts
│   │   ├── pages/
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── server/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── errors.py
│   │   ├── api/
│   │   │   ├── dependencies.py
│   │   │   └── routes/
│   │   │       ├── mandates.py
│   │   │       ├── requests.py
│   │   │       ├── proposals.py
│   │   │       ├── orders.py
│   │   │       └── webhooks.py
│   │   ├── schemas/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── services/
│   │   │   ├── mandate_service.py
│   │   │   ├── request_service.py
│   │   │   ├── proposal_service.py
│   │   │   ├── audit_service.py
│   │   │   └── order_service.py
│   │   ├── agent/
│   │   │   ├── orchestrator.py
│   │   │   ├── prompts.py
│   │   │   ├── tools.py
│   │   │   └── schemas.py
│   │   ├── integrations/
│   │   │   ├── channel3_client.py
│   │   │   ├── paypal_client.py
│   │   │   ├── kernel_client.py
│   │   │   └── llm_client.py
│   │   ├── guardrails/
│   │   │   ├── engine.py
│   │   │   ├── budget.py
│   │   │   ├── category.py
│   │   │   ├── retailer.py
│   │   │   ├── availability.py
│   │   │   └── price.py
│   │   ├── workers/
│   │   │   ├── agent_worker.py
│   │   │   ├── reconciliation.py
│   │   │   └── cleanup.py
│   │   └── db/
│   │       ├── session.py
│   │       └── migrations/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── fixtures/
│   ├── eval/
│   │   ├── scenarios.json
│   │   └── run_eval.py
│   ├── requirements.txt
│   └── alembic.ini
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── threat-model.md
│   └── demo-script.md
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

# 8. Environment variables

Create `.env.example` with placeholder values only. Do not commit `.env`.

```env
APP_ENV=development
APP_BASE_URL=http://localhost:8000
CLIENT_BASE_URL=http://localhost:5173

DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME

LLM_PROVIDER=gemini
LLM_API_KEY=replace_me
LLM_MODEL=replace_with_supported_model

CHANNEL3_API_KEY=replace_me
CHANNEL3_BASE_URL=https://api.trychannel3.com/v1
CHANNEL3_COUNTRY=US
CHANNEL3_LANGUAGE=en
CHANNEL3_CURRENCY=USD

PAYPAL_ENV=sandbox
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
PAYPAL_CLIENT_ID=replace_me
PAYPAL_CLIENT_SECRET=replace_me
PAYPAL_WEBHOOK_ID=replace_me

KERNEL_ENABLED=false
KERNEL_API_KEY=replace_me

SESSION_SECRET=replace_with_random_secret
LOG_LEVEL=INFO
```

Only the frontend PayPal client ID may be exposed as a public configuration value where required by the JS SDK. The PayPal secret, webhook ID, Channel3 API key, LLM key, KERNEL key, database password, and session secret remain backend-only.

---

# 9. Deployment plan on Render

## Services

1. **PostgreSQL database:** persistent application data.
2. **FastAPI web service:** API, SSE, PayPal webhook endpoint, and optionally serves the built frontend.
3. **Frontend:** either build and serve from the backend or deploy as a separate static site. For a straightforward demo, serving the built frontend from the same web service reduces CORS and cookie complexity.
4. **Cron/worker (optional):** cleanup and reconciliation jobs.

## Deployment requirements

- Configure all secrets as Render environment variables.
- Run Alembic migrations during deployment in a controlled release step.
- Configure HTTPS and the PayPal webhook URL.
- Add health and readiness endpoints.
- Set request/body limits and sensible API timeouts.
- Configure CORS only for the actual frontend origin if using separate services.
- Ensure SSE proxy buffering is disabled or configured so progress events reach the browser promptly.
- Persist logs and database data; do not rely on local filesystem storage for application state.
- Keep Sandbox enabled for the hackathon demo.

---

# 10. Security and failure handling checklist

| Situation | Required behavior |
|---|---|
| Price changes after proposal | Mark proposal stale; refresh and create a new proposal |
| Product becomes out of stock | Block selected offer; agent may select another candidate |
| Product disappears from Channel3 | Block and request a new search |
| Retailer offer changes | Do not silently switch; require fresh proposal |
| Over total budget | Block before PayPal order creation |
| Over per-item cap | Block before proposal/checkout |
| Mandate expires during checkout | Block new order/capture according to state; do not bypass expiry |
| User cancels PayPal popup | Keep payment uncaptured; release reservation when safe |
| Create-order request times out | Query internal order state and reuse the same idempotency key |
| Capture request times out | Reconcile PayPal order/capture before retrying |
| Duplicate webhook | Deduplicate by PayPal event ID |
| Invalid webhook signature | Reject and do not mutate order state |
| Webhook arrives out of order | Apply only valid monotonic state transitions |
| Product text contains prompt injection | Treat as untrusted content; do not change tools or policy |
| LLM provider fails | Mark request failed/retryable; no payment path is opened |
| Channel3 rate limit/provider outage | Return a clear retryable error; do not use stale cached data for payment |
| KERNEL page is inaccessible | Mark verification inconclusive; do not claim it passed |
| Double-click on PayPal button | One internal order per proposal; stable PayPal idempotency key |
| User changes browser data | Backend reloads all prices and amounts from persisted validated records |

---

# 11. Implementation order for Antigravity

Build and test one module at a time. Do not ask an agent to generate the whole project in one prompt.

## Step 1 — Scaffold

**Prompt:**

> Create a monorepo with a React + Vite + TypeScript frontend in `/client` and a Python FastAPI backend in `/server`. Use PostgreSQL, SQLAlchemy 2.x, Alembic, Pydantic, and HTTPX. Create the folder structure in the project specification. Add health endpoint, frontend routing, typed API client, `.env.example`, `.gitignore`, and README run instructions. Do not implement payments or the LLM yet. Run the frontend and backend and add basic tests.

**Completion test:** frontend loads, `/api/health` responds, database connects, migrations run.

## Step 2 — Database and mandate service

**Prompt:**

> Implement PostgreSQL models, repositories, and Alembic migrations for users, mandates, requests, request_events, candidates, candidate_offers, proposals, orders, refunds, webhook_events, and audit_events. Use Decimal/numeric for all money. Implement mandate versioning, ownership checks, and the mandate API. Add tests for expiry, revocation, versioning, and invalid caps.

**Completion test:** mandate create/read/update/version tests pass.

## Step 3 — Channel3 adapter

**Prompt:**

> Read the current official Channel3 API documentation before coding. Implement a typed HTTPX adapter for POST `/v1/search`, POST `/v1/lookup`, and GET `/v1/products/{product_id}` using the documented auth header and actual response fields. Normalize canonical products and retailer offers separately. A product can have multiple retailer offers; price and availability belong to each offer. Add mocked adapter tests and never expose the API key to the frontend.

**Completion test:** search and product refresh work using a real API key, with tests for multiple offers and changing prices.

## Step 4 — Guardrails

**Prompt:**

> Implement deterministic pure guardrail functions for active mandate, currency, total budget, per-item cap, quantity, allowed/blocked categories, retailer allowlist, stock, condition, product/variant identity, exact retailer-offer identity, price freshness, price drift, and optional KERNEL verification state. Use Decimal. Return structured pass/block/stale/review results. Do not call the LLM from guardrails. Add comprehensive unit tests including all negative cases.

**Completion test:** no over-budget or blocked-category scenario can return PASS.

## Step 5 — Agent loop

**Prompt:**

> Implement a bounded tool-calling agent using the configured LLM provider. Expose only `search_products`, `get_product`, and `propose_purchase`. The LLM must not have PayPal tools, direct database access, arbitrary HTTP access, or a way to edit mandates. Persist candidates, explanations, tool summaries, progress events, and proposal results. Treat all catalog/page text as untrusted data. Run the 30 evaluation scenarios.

**Completion test:** valid request creates a proposal; invalid requests block; LLM cannot trigger payment.

## Step 6 — SSE and frontend request/results modules

**Prompt:**

> Implement `POST /api/requests`, request status APIs, SSE progress with event IDs/heartbeats, and cancellation. Build the React request panel, progress timeline, candidate comparison cards, alternative/rejected options, and proposal review screen. All shown prices and eligibility statuses must come from the backend API.

**Completion test:** browser can submit a request, watch events, compare offers, and open a saved proposal.

## Step 7 — PayPal service

**Prompt:**

> Implement the PayPal Sandbox server service using the official Orders v2 API. Add OAuth token caching, create order with `intent: CAPTURE`, capture after buyer approval, full refund, and stable `PayPal-Request-Id` keys. The backend must reload proposal data, refresh Channel3, rerun guardrails, and reserve budget transactionally before create-order. Persist PayPal IDs and never trust amount/currency from the client. Add mocked unit tests first.

**Completion test:** a stale offer is blocked; valid proposal creates one PayPal order.

## Step 8 — PayPal JS SDK and webhook

**Prompt:**

> Add `@paypal/react-paypal-js` to the frontend. Implement `createOrder`, `onApprove`, `onCancel`, and `onError` callbacks that call only our backend endpoints. Implement the PayPal webhook listener using the raw event body, configured webhook ID, signature verification, unique event deduplication, and monotonic order-state reconciliation. Add sandbox integration tests.

**Completion test:** a sandbox buyer approves; backend captures; verified webhook updates the order; duplicate webhook is harmless.

## Step 9 — KERNEL adapter

**Prompt:**

> Read the current KERNEL documentation and implement a provider adapter that opens only the selected Channel3 retailer offer URL, extracts visible product title, selected variant, price, currency, retailer, and availability, captures evidence/timestamp, and closes the session. Do not guess endpoint names. Do not log in, enter payment details, or place the retailer order. Compare the browser result with the exact Channel3 offer and return verified/mismatch/inconclusive. Add mocked tests; keep KERNEL optional behind a feature flag.

**Completion test:** mismatch blocks/stales the proposal; unavailable browser is inconclusive and never reported as verified.

## Step 10 — History, audit, deployment, and evaluation

**Prompt:**

> Implement the history dashboard and order receipt, structured audit logging, cleanup/reconciliation jobs, 30-case evaluation report, Render deployment configuration, complete README, and a Playwright end-to-end test. Ensure secrets are not committed and all core tests pass. Clearly label that PayPal Sandbox payment is to the demo merchant and does not fulfil a retailer order.

**Completion test:** a clean clone can be configured and run using the README, and the demo flow works from mandate to receipt.

---

# 12. MVP completion checklist

## Product flow

- [ ] User can create a spending mandate.
- [ ] User can submit a natural-language shopping request.
- [ ] Agent searches Channel3 using live data.
- [ ] Agent compares products and retailer offers.
- [ ] Channel3 product detail refresh runs before a proposal.
- [ ] Guardrails run in deterministic backend code.
- [ ] Proposal includes exact canonical product, retailer offer, variant, quantity, amount, currency, and checks.
- [ ] User sees the rejected alternatives and reasons.
- [ ] PayPal Buttons appear only for an eligible proposal.
- [ ] Server refreshes the exact offer and reruns guardrails before order creation.
- [ ] Buyer approves through PayPal Sandbox.
- [ ] Server captures payment and stores capture ID.
- [ ] Webhook signature is verified and duplicate events are ignored.
- [ ] Receipt and history show the correct state.
- [ ] Full refund is available for eligible captured Sandbox payments.

## Safety

- [ ] LLM has no payment tool.
- [ ] Frontend has no PayPal secret or Channel3 secret.
- [ ] No price from the LLM/browser is used as the final amount.
- [ ] One proposal cannot create two internal orders.
- [ ] One order cannot be captured twice.
- [ ] Budget reservation is atomic under concurrent requests.
- [ ] All failed/blocked actions have a safe reason and audit record.
- [ ] Product-page prompt injection cannot change policy or tools.
- [ ] The demo clearly explains the difference between a PayPal Sandbox payment and an actual retailer order.

---

# 13. Reference repositories and how to use them

These repositories were inspected at the README/repository overview level for architecture and workflow patterns. They are hackathon projects/prototypes, not independently security-audited production libraries. Reuse ideas and inspect source code before copying any implementation.

| Reference | Useful patterns to study | How to apply |
|---|---|---|
| [JacobEGarcia/allowance](https://github.com/JacobEGarcia/allowance) | Mandate-first shopping, goal in plain English, agent picks, user approval, PayPal checkout, ledger, optional server-side Orders v2 flow | Study its mandate/ledger framing and concise buyer journey; do not copy browser-stored API secrets |
| [theSrijan13/AgentPay](https://github.com/theSrijan13/AgentPay) | React + TypeScript + Vite, FastAPI + HTTPX, Channel3 live search, server-side product refresh, PayPal Sandbox, optional Elastic audit indexing, Postman/Render setup | Closest architectural reference for the stack selected in this specification |
| [andreajoseph1510-star/paypal-purchasing-agent](https://github.com/andreajoseph1510-star/paypal-purchasing-agent) | Gemini + Channel3, code-enforced per-purchase/monthly policy, human approval, history/audit; repository is forked from PayPal AG Grid boilerplate | Study policy display, audit/history screens, and agent-to-approval flow |
| [rayhannajla-hash/procure-agent](https://github.com/rayhannajla-hash/procure-agent) | Procurement-style constraints, approved retailers, restricted categories, cost-center budgets, approval routing, product comparisons | Study its structured policy model and explanations for rejected items |
| [andreyalchin/Mandate-Agentic-Ecommerce-PayPal-AI-Hackathon-2026](https://github.com/andreyalchin/Mandate-Agentic-Ecommerce-PayPal-AI-Hackathon-2026) | Natural-language mandates, threshold-based approvals, recurring purchases, one-tap approval, refund path, extensive docs/tests/e2e folders | Study mandate UX and its testing/docs organization; do not copy sandbox credentials or secrets from any repository |

### Reference review limitations

This review uses public README and repository overview information to identify architecture and feature patterns. It is not a full source-code audit of every file, dependency, license condition, or runtime behavior. Before reusing code, inspect the individual implementation, license, dependencies, secrets handling, and current API compatibility.

---

# 14. External API documentation to follow during implementation

Use the provider's current documentation and SDKs instead of guessing endpoint shapes:

- [Channel3 developer overview](https://www.trychannel3.com/developers/)
- [Channel3 search guide](https://channel3.ai/docs/guides/make-a-search)
- [Channel3 URL lookup](https://channel3.ai/docs/guides/url-lookup)
- [Channel3 product detail](https://channel3.ai/docs/guides/product-detail)
- [Channel3 offer model](https://channel3.ai/docs/guides/offer)
- [KERNEL documentation](https://www.kernel.sh/docs)
- [PayPal Orders v2 integration guide](https://developer.paypal.com/api/rest/integration/orders-api)
- [PayPal REST API requests and idempotency](https://developer.paypal.com/api/make-api-requests)
- [PayPal webhooks integration](https://developer.paypal.com/api/rest/webhooks/rest/)
- [PayPal AI Hackathon rules](https://paypalaihackathon.devpost.com/rules)

### Verified integration notes

- Channel3's search endpoint accepts a natural-language query, optional filters, and a result limit. The API requires a Channel3 API key.
- Channel3 supports URL lookup to resolve a retailer product URL into a canonical product ID.
- Channel3 supports retrieving a canonical product by ID. Use this to refresh offers before showing a price and before checkout.
- Channel3 models a product separately from its retailer offers. Price and availability are offer-level values.
- The Channel3 developer overview currently describes its `/checkout` functionality as coming soon/request early access. Do not assume that Channel3 can place a retailer order in this build.
- PayPal REST APIs use OAuth 2.0 access tokens. The Sandbox base URL is `https://api-m.sandbox.paypal.com`.
- PayPal recommends `PayPal-Request-Id` for POST/PUT operations to support idempotent retries.
- PayPal webhooks require signature verification and can be retried; the listener must deduplicate events.
- KERNEL provides cloud browser infrastructure for agents. Its specific endpoints, SDK signatures, and authorization model must be taken from its current docs; do not invent them.

---

# 15. Features deliberately not included in this core version

These came from the supplied problem statement or the planned extension discussion, but should be implemented only after the core request-to-PayPal-capture flow is reliable:

- Group gift concierge and contribution pools.
- Multiple PayPal contributors and pool-target triggers.
- Post-purchase price-drop monitoring and drafted adjustment/refund requests.
- Elastic vector-based taste memory.
- Accessibility- or dietary-constraint-specific shopping profiles.
- Voice input and local-language shopping.
- Basket optimizer and multi-item budget allocation.
- Automatic/threshold-based agent wallet spending.
- Merchant-side fulfilment or automated retailer checkout.

The core schema should remain extensible, but do not add unfinished UI or placeholder buttons for these features in the first MVP.

---

**End of core module specification.**
