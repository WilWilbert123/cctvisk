"""Real local network scanner supporting ARP, TCP probing, ICMP, and cancellation."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any
from backend.app.config import get_settings
from backend.core.logging import get_logger
from backend.services.network.arp import discover_arp_neighbors, read_os_arp_table
from backend.services.network.interface import get_active_interface
from backend.services.network.ping import check_host_reachable
from backend.services.network.subnet import get_scannable_hosts
from backend.utils.ip_utils import validate_authorized_subnet

logger = get_logger("scanner")

ProgressCallback = Callable[[float, str, int], Awaitable[None]]


class LocalNetworkScanner:
    """
    Non-destructive local subnet scanner.
    Discovers active hosts via ARP cache, optional Scapy ARP broadcast,
    concurrent TCP service handshakes, and ICMP Echo probes.
    """

    def __init__(self) -> None:
        self._cancel_requested = False

    def request_cancel(self) -> None:
        self._cancel_requested = True

    def reset_cancel(self) -> None:
        self._cancel_requested = False

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_requested

    async def scan_subnet(
        self,
        subnet_cidr: str | None = None,
        interface_name: str | None = None,
        progress_cb: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        """
        Scan an authorized local subnet and return deduplicated alive host records:
        {
          "subnet_cidr": str,
          "interface_name": str,
          "local_ip": str,
          "gateway": str | None,
          "hosts": dict[ip, {"ip_address", "mac_address", "latency_ms", "quick_open_ports", "discovery_methods"}]
        }
        """
        self.reset_cancel()
        settings = get_settings()
        active_iface = get_active_interface(interface_name)
        target_cidr = subnet_cidr or active_iface["subnet_cidr"]
        validated_net = validate_authorized_subnet(target_cidr)
        normalized_cidr = str(validated_net)

        local_ip = active_iface.get("ip_address")
        gateway_ip = active_iface.get("gateway")

        discovered: dict[str, dict[str, Any]] = {}

        if progress_cb:
            await progress_cb(5.0, f"Inspecting ARP cache on {normalized_cidr}", 0)

        # Step 1: Initial ARP discovery (fast, finds already-known LAN neighbors)
        arp_map = await asyncio.to_thread(discover_arp_neighbors, normalized_cidr)
        for ip_addr, mac_addr in arp_map.items():
            discovered[ip_addr] = {
                "ip_address": ip_addr,
                "mac_address": mac_addr,
                "latency_ms": 1.0,
                "quick_open_ports": [],
                "discovery_methods": ["ARP"],
                "is_gateway": ip_addr == gateway_ip,
                "is_host": ip_addr == local_ip,
            }

        if self._cancel_requested:
            return {
                "cancelled": True,
                "subnet_cidr": normalized_cidr,
                "interface_name": active_iface["interface_name"],
                "local_ip": local_ip,
                "gateway": gateway_ip,
                "hosts": discovered,
            }

        # Include the host machine itself if within subnet
        if local_ip and local_ip != "127.0.0.1":
            try:
                import ipaddress
                if ipaddress.ip_address(local_ip) in validated_net:
                    entry = discovered.setdefault(
                        local_ip,
                        {
                            "ip_address": local_ip,
                            "mac_address": active_iface.get("mac_address"),
                            "latency_ms": 0.1,
                            "quick_open_ports": [],
                            "discovery_methods": ["LOCAL_INTERFACE"],
                            "is_gateway": False,
                            "is_host": True,
                        },
                    )
                    if active_iface.get("mac_address") and not entry.get("mac_address"):
                        entry["mac_address"] = active_iface.get("mac_address")
            except ValueError:
                pass

        # Step 2: Active concurrent TCP + ICMP sweep across subnet hosts
        host_ips = get_scannable_hosts(normalized_cidr)
        total_hosts = len(host_ips)
        concurrency = max(8, min(128, settings.SCAN_MAX_CONCURRENCY))
        semaphore = asyncio.Semaphore(concurrency)
        completed_count = 0

        async def _probe_single(ip_addr: str) -> None:
            nonlocal completed_count
            if self._cancel_requested:
                return
            async with semaphore:
                if self._cancel_requested:
                    return
                is_alive, latency, open_ports, method_str = await check_host_reachable(
                    ip_addr,
                    timeout_ms=settings.SCAN_DEFAULT_TIMEOUT_MS,
                    enable_icmp=settings.SCAN_ENABLE_ICMP,
                )
                completed_count += 1
                if is_alive:
                    existing = discovered.get(ip_addr)
                    methods = [m for m in method_str.split("+") if m and m != "NONE"]
                    if existing:
                        existing["latency_ms"] = latency or existing.get("latency_ms")
                        existing["quick_open_ports"] = sorted(
                            set(existing.get("quick_open_ports", []) + open_ports)
                        )
                        existing["discovery_methods"] = sorted(
                            set(existing.get("discovery_methods", []) + methods)
                        )
                    else:
                        discovered[ip_addr] = {
                            "ip_address": ip_addr,
                            "mac_address": None,
                            "latency_ms": latency,
                            "quick_open_ports": open_ports,
                            "discovery_methods": methods or ["TCP"],
                            "is_gateway": ip_addr == gateway_ip,
                            "is_host": ip_addr == local_ip,
                        }

                if progress_cb and (completed_count % 16 == 0 or completed_count == total_hosts):
                    pct = 10.0 + (completed_count / max(1, total_hosts)) * 40.0
                    await progress_cb(
                        pct,
                        f"Probing subnet hosts ({completed_count}/{total_hosts})",
                        len(discovered),
                    )

        await asyncio.gather(*(_probe_single(ip) for ip in host_ips))

        # Step 3: Refresh OS ARP table after active probing (TCP/ICMP packets populate OS ARP cache!)
        refreshed_arp = await asyncio.to_thread(read_os_arp_table)
        for ip_addr, mac_addr in refreshed_arp.items():
            try:
                import ipaddress
                if ipaddress.ip_address(ip_addr) not in validated_net:
                    continue
            except ValueError:
                continue

            if ip_addr in discovered:
                if not discovered[ip_addr].get("mac_address"):
                    discovered[ip_addr]["mac_address"] = mac_addr
                if "ARP" not in discovered[ip_addr]["discovery_methods"]:
                    discovered[ip_addr]["discovery_methods"].append("ARP")
            else:
                discovered[ip_addr] = {
                    "ip_address": ip_addr,
                    "mac_address": mac_addr,
                    "latency_ms": None,
                    "quick_open_ports": [],
                    "discovery_methods": ["ARP"],
                    "is_gateway": ip_addr == gateway_ip,
                    "is_host": ip_addr == local_ip,
                }

        return {
            "cancelled": self._cancel_requested,
            "subnet_cidr": normalized_cidr,
            "interface_name": active_iface["interface_name"],
            "local_ip": local_ip,
            "gateway": gateway_ip,
            "total_hosts_probed": total_hosts,
            "hosts": discovered,
        }

