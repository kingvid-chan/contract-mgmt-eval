"""Audit logger dependency for FastAPI — extracts client IP from request."""

import ipaddress

from fastapi import Request


# Private IP networks for filtering X-Forwarded-For entries
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
]


def _is_private_ip(ip_str: str) -> bool:
    """Return True if the IP address is in a private/internal range."""
    try:
        addr = ipaddress.ip_address(ip_str.strip())
        return any(addr in net for net in _PRIVATE_NETWORKS)
    except ValueError:
        return True  # Treat unparseable IPs as private (skip them)


class AuditLogger:
    """FastAPI dependency that extracts the real client IP from the request.

    Usage:
        @router.post("/some-endpoint")
        def handler(audit: AuditLogger = Depends(), ...):
            ip = audit.ip_address
    """

    def __init__(self, request: Request):
        self._request = request
        self._ip_address: str | None = None

    @property
    def ip_address(self) -> str:
        """Extract the real client IP using the priority chain.

        Priority:
        1. X-Real-IP header (set directly by Nginx)
        2. X-Forwarded-For — first non-private IP from the left
        3. request.client.host (direct connection fallback)
        """
        if self._ip_address is None:
            self._ip_address = self._extract_client_ip()
        return self._ip_address

    def _extract_client_ip(self) -> str:
        # 1. X-Real-IP
        real_ip = self._request.headers.get("X-Real-IP")
        if real_ip:
            ip = real_ip.strip()
            try:
                ipaddress.ip_address(ip)
                return ip
            except ValueError:
                pass

        # 2. X-Forwarded-For — first non-private IP
        forwarded = self._request.headers.get("X-Forwarded-For")
        if forwarded:
            for token in forwarded.split(","):
                ip = token.strip()
                try:
                    ipaddress.ip_address(ip)
                    if not _is_private_ip(ip):
                        return ip
                except ValueError:
                    continue

        # 3. request.client.host (direct connection)
        if self._request.client and self._request.client.host:
            return self._request.client.host

        return "unknown"
