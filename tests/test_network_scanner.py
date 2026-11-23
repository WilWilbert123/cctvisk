"""Tests for network interface detection, subnet validation, and simulated local subnet scanning."""

from __future__ import annotations

import pytest
from backend.core.exceptions import UnauthorizedSubnetError
from backend.services.network.interface import get_active_interface, list_network_interfaces
from backend.services.network.scanner import LocalNetworkScanner
from backend.services.network.subnet import get_scannable_hosts, validate_and_describe_subnet
from backend.utils.ip_utils import validate_authorized_ip, validate_authorized_subnet


def test_network_interface_detection() -> None:
    interfaces = list_network_interfaces()
    assert isinstance(interfaces, list)
    active = get_active_interface()
    assert "interface_name" in active
    assert "ip_address" in active
    assert "subnet_cidr" in active


def test_subnet_validation_accepts_private_ranges() -> None:
    info = validate_and_describe_subnet("192.168.10.0/24")
    assert info["valid"] is True
    assert info["normalized_cidr"] == "192.168.10.0/24"
    assert info["host_count"] == 254

    hosts = get_scannable_hosts("192.168.10.0/29")
    assert len(hosts) == 6
    assert "192.168.10.1" in hosts


def test_subnet_validation_rejects_public_ranges() -> None:
    info = validate_and_describe_subnet("8.8.8.0/24")
    assert info["valid"] is False

    with pytest.raises(UnauthorizedSubnetError):
        validate_authorized_subnet("1.1.1.0/24")

    with pytest.raises(UnauthorizedSubnetError):
        validate_authorized_ip("8.8.4.4")


@pytest.mark.asyncio
async def test_scanner_with_simulated_responses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.services.network.scanner.discover_arp_neighbors",
        lambda _cidr: {"192.168.50.10": "28:57:BE:AA:BB:CC"},
    )
    monkeypatch.setattr(
        "backend.services.network.scanner.read_os_arp_table",
        lambda: {"192.168.50.10": "28:57:BE:AA:BB:CC"},
    )

    async def _fake_check_reachable(ip_addr: str, timeout_ms: int = 700, enable_icmp: bool = True):
        if ip_addr == "192.168.50.10":
            return True, 2.4, [80, 554, 8000], "TCP"
        return False, None, [], "NONE"

    monkeypatch.setattr(
        "backend.services.network.scanner.check_host_reachable",
        _fake_check_reachable,
    )

    scanner = LocalNetworkScanner()
    res = await scanner.scan_subnet(subnet_cidr="192.168.50.0/29")
    assert res["cancelled"] is False
    assert "192.168.50.10" in res["hosts"]
    assert res["hosts"]["192.168.50.10"]["mac_address"] == "28:57:BE:AA:BB:CC"

