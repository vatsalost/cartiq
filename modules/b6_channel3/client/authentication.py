"""Authentication handling for Channel3 API."""

from typing import Optional
from pydantic import SecretStr
from modules.b6_channel3.exceptions import Channel3AuthError


class Channel3Auth:
    """Manages Channel3 API key headers and credential safety."""

    def __init__(self, api_key: Optional[SecretStr | str] = None):
        if isinstance(api_key, str):
            self._api_key = SecretStr(api_key.strip()) if api_key.strip() else None
        elif isinstance(api_key, SecretStr):
            self._api_key = api_key
        else:
            self._api_key = None

    @property
    def has_credentials(self) -> bool:
        """Check if a valid API key is present."""
        return self._api_key is not None and bool(self._api_key.get_secret_value())

    def get_auth_headers(self) -> dict[str, str]:
        """Generate headers required for Channel3 API requests.

        Raises:
            Channel3AuthError: If no API key is configured.
        """
        if not self.has_credentials:
            raise Channel3AuthError("Channel3 API key is not configured.")

        # Official Channel3 header: x-api-key
        return {
            "x-api-key": self._api_key.get_secret_value(),  # type: ignore[union-attr]
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CartiQ-Concierge-B6/1.0",
        }

    def __repr__(self) -> str:
        status = "Configured" if self.has_credentials else "Missing"
        return f"Channel3Auth(status={status})"

    def __str__(self) -> str:
        return self.__repr__()
