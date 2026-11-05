"""Health and system readiness endpoint."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from server.app.core.config import settings
from server.app.db.session import check_db_connectivity

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="System health and database check")
async def get_health():
    """
    Return basic application status, API version, and database connectivity.
    Never exposes credentials or internal secrets.
    """
    db_connected = check_db_connectivity()
    status_str = "ok" if db_connected else "degraded"
    status_code = status.HTTP_200_OK if db_connected else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": status_str,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "database": "connected" if db_connected else "disconnected",
        },
    )
