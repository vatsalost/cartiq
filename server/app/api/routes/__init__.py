"""API route modules."""

from server.app.api.routes.auth import router as auth_router
from server.app.api.routes.health import router as health_router
from server.app.api.routes.mandates import router as mandates_router
from server.app.api.routes.orders import router as orders_router
from server.app.api.routes.proposals import router as proposals_router
from server.app.api.routes.requests import router as requests_router
from server.app.api.routes.webhooks import router as webhooks_router

__all__ = [
    "auth_router",
    "health_router",
    "mandates_router",
    "requests_router",
    "proposals_router",
    "orders_router",
    "webhooks_router",
]
