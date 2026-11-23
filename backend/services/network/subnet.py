"""Subnet calculation, validation, and host list generation."""

from __future__ import annotations

from typing import Any
from backend.core.exceptions import UnauthorizedSubnetError
from backend.utils.ip_utils import enumerate_subnet_hosts, validate_authorized_subnet


def validate_and_describe_subnet(subnet_cidr: str) -> dict[str, Any]:
    """Validate that a subnet CIDR belongs to an authorized local RFC1918/link-local range."""
    try:
        network = validate_authorized_subnet(subnet_cidr)
        host_count = max(0, network.num_addresses - 2) if network.prefixlen <= 30 else network.num_addresses
        return {
            "valid": True,
            "normalized_cidr": str(network),
            "network_address": str(network.network_address),
            "broadcast_address": str(network.broadcast_address),
            "netmask": str(network.netmask),
            "prefixlen": network.prefixlen,
            "host_count": host_count,
            "message": f"Valid local private subnet ({host_count} scannable host addresses).",
        }
    except UnauthorizedSubnetError as exc:
        return {
            "valid": False,
            "normalized_cidr": None,
            "host_count": 0,
            "message": exc.message,
        }


def get_scannable_hosts(subnet_cidr: str, exclude_ips: set[str] | None = None) -> list[str]:
    """Return ordered list of usable host IPs in the validated subnet."""
    return enumerate_subnet_hosts(subnet_cidr, exclude_ips=exclude_ips)

