"""IPv4 and subnet validation and calculation utilities with SSRF protection."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse
from backend.core.exceptions import UnauthorizedSubnetError


def is_authorized_private_ip(ip_str: str) -> bool:
    """
    Return True ONLY if ip_str is a valid IPv4 private (RFC1918) or link-local address.
    Loopback, multicast, broadcast, unspecified, and public internet IPs are rejected for scanning.
    """
    try:
        ip_obj = ipaddress.ip_address(ip_str.strip())
        if not isinstance(ip_obj, ipaddress.IPv4Address):
            return False
        if ip_obj.is_multicast or ip_obj.is_unspecified or ip_obj.is_loopback:
            return False
        if str(ip_obj) == "255.255.255.255":
            return False
        return ip_obj.is_private or ip_obj.is_link_local
    except ValueError:
        return False


def validate_authorized_ip(ip_str: str) -> str:
    """Validate and normalize an IPv4 address belonging to an authorized private network."""
    cleaned = ip_str.strip()
    if not is_authorized_private_ip(cleaned):
        raise UnauthorizedSubnetError(cleaned)
    return str(ipaddress.IPv4Address(cleaned))


def validate_authorized_subnet(cidr_str: str, max_hosts: int = 1024) -> ipaddress.IPv4Network:
    """
    Validate that a CIDR string is a private RFC1918 or link-local IPv4 subnet
    and is not excessively large (e.g., /16 or /8) to prevent accidental network flooding.
    """
    cleaned = cidr_str.strip()
    try:
        network = ipaddress.ip_network(cleaned, strict=False)
    except ValueError as exc:
        raise UnauthorizedSubnetError(cleaned) from exc

    if not isinstance(network, ipaddress.IPv4Network):
        raise UnauthorizedSubnetError(cleaned)

    if (
        not (network.is_private or network.is_link_local)
        or network.is_loopback
        or network.is_multicast
        or network.is_unspecified
    ):
        raise UnauthorizedSubnetError(cleaned)

    if network.num_addresses > max_hosts:
        raise UnauthorizedSubnetError(
            f"{cleaned} (subnet exceeds maximum allowed size of {max_hosts} addresses; use /22 to /30)"
        )

    return network


def netmask_to_cidr(ip_str: str, netmask_str: str) -> str:
    """Convert an IPv4 address and dotted netmask (e.g. 255.255.255.0) into network CIDR."""
    network = ipaddress.IPv4Network(f"{ip_str}/{netmask_str}", strict=False)
    return str(network)


def enumerate_subnet_hosts(cidr_str: str, exclude_ips: set[str] | None = None) -> list[str]:
    """Return all usable host IPv4 addresses in an authorized private subnet."""
    network = validate_authorized_subnet(cidr_str)
    excluded = exclude_ips or set()
    if network.prefixlen >= 31:
        return [str(ip) for ip in network if str(ip) not in excluded]
    return [str(ip) for ip in network.hosts() if str(ip) not in excluded]


def construct_safe_admin_url(ip_address: str, port: int = 80, use_https: bool = False) -> str:
    """
    Construct a safe local HTTP/HTTPS administration URL after validating the IP and port.
    Never embeds credentials in the URL.
    """
    valid_ip = validate_authorized_ip(ip_address)
    if not (1 <= int(port) <= 65535):
        raise ValueError(f"Invalid TCP port: {port}")
    scheme = "https" if use_https or port in (443, 8443) else "http"
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        return f"{scheme}://{valid_ip}/"
    return f"{scheme}://{valid_ip}:{port}/"


def mask_rtsp_url(rtsp_url: str | None) -> str | None:
    """Mask any embedded password in an RTSP or HTTP URL before returning or logging."""
    if not rtsp_url:
        return None
    try:
        parsed = urlparse(rtsp_url)
        if parsed.password:
            user = parsed.username or "admin"
            host_port = f"{parsed.hostname}:{parsed.port}" if parsed.port else (parsed.hostname or "")
            path_query = parsed.path or ""
            if parsed.query:
                path_query = f"{path_query}?{parsed.query}"
            return f"{parsed.scheme}://{user}:***@{host_port}{path_query}"
        return rtsp_url
    except Exception:
        return rtsp_url

