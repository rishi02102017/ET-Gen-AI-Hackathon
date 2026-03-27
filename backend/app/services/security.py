from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


class UnsafeUrlError(ValueError):
    pass


def assert_fetchable_http_url(url: str) -> None:
    """
    Reduce SSRF risk for server-side URL fetching.
    Allows only http(s) to public routable hosts (best-effort).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeUrlError("Only http and https URLs are allowed.")
    if not parsed.hostname:
        raise UnsafeUrlError("URL must include a hostname.")

    host = parsed.hostname.lower()
    if host in ("localhost",) or host.endswith(".local"):
        raise UnsafeUrlError("Local hosts are not allowed.")

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return

    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        raise UnsafeUrlError("Non-public IP addresses are not allowed.")
