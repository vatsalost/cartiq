"""URL validation and SSRF defense for Channel3 URL lookup operations."""

import ipaddress
import re
from urllib.parse import urlparse
from modules.b6_channel3.exceptions import InvalidURLError

BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "instance-data",
}


class URLValidator:
    """Validates and sanitizes URLs before forwarding to Channel3 lookup."""

    @staticmethod
    def validate_lookup_url(url: str) -> str:
        """Validate that a URL is a valid, public HTTP/HTTPS retailer link.

        Guards against SSRF, loopback access, and malformed URL attacks.

        Args:
            url: The retailer URL to validate.

        Returns:
            Sanitized URL string.

        Raises:
            InvalidURLError: If the URL is malformed, dangerous, or not HTTP/HTTPS.
        """
        if not url or not isinstance(url, str):
            raise InvalidURLError("URL must be a non-empty string.")

        clean_url = url.strip()
        if len(clean_url) > 2048:
            raise InvalidURLError("URL length exceeds maximum limit of 2048 characters.")

        try:
            parsed = urlparse(clean_url)
        except Exception as e:
            raise InvalidURLError(f"Malformed URL: {e}") from e

        if parsed.scheme.lower() not in ("http", "https"):
            raise InvalidURLError(f"Invalid URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted.")

        hostname = (parsed.hostname or "").lower().strip()
        if not hostname:
            raise InvalidURLError("URL must contain a valid domain hostname.")

        if hostname in BLOCKED_HOSTNAMES:
            raise InvalidURLError(f"Access to '{hostname}' is prohibited.")

        # Check for private or loopback IP addresses
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                raise InvalidURLError(f"Access to private/internal IP address '{hostname}' is strictly prohibited.")
        except ValueError:
            # Not an IP literal, validate standard domain syntax
            pass

        # Ensure hostname contains at least one dot (e.g. retailer.com) unless it's a valid public TLD
        if "." not in hostname:
            raise InvalidURLError(f"Domain '{hostname}' is not a valid fully qualified domain name.")

        # Disallow control characters or non-printable chars
        if re.search(r"[\x00-\x1f\x7f]", clean_url):
            raise InvalidURLError("URL contains prohibited control characters.")

        return clean_url
