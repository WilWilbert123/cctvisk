"""Controlled, rate-limited TCP service port scanner for authorized local devices."""

from __future__ import annotations

import asyncio
from typing import Any
from backend.app.config import get_settings
from backend.services.ports.common_ports import get_default_scan_ports
from backend.services.ports.service_mapper import (
    infer_protocols_from_ports,
    map_open_ports_to_services,
)
from backend.utils.ip_utils import validate_authorized_ip
from backend.utils.validators import validate_port_list


async def scan_device_ports(
    ip_address: str,
    ports: list[int] | None = None,
    timeout_ms: int | None = None,
    concurrency: int = 16,
) -> dict[str, Any]:
    """
    Perform non-invasive TCP connection checks on a documented list of ports
    for a single authorized local IPv4 address.
    """
    valid_ip = validate_authorized_ip(ip_address)
    settings = get_settings()
    target_ports = validate_port_list(ports) if ports else get_default_scan_ports()
    timeout_sec = max(0.15, (timeout_ms or settings.SCAN_PORT_TIMEOUT_MS) / 1000.0)

    semaphore = asyncio.Semaphore(max(1, min(32, concurrency)))
    open_ports: list[int] = []

    async def _probe(port: int) -> None:
        async with semaphore:
            try:
                _reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(valid_ip, port),
                    timeout=timeout_sec,
                )
                open_ports.append(port)
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass
            except (asyncio.TimeoutError, OSError):
                pass

    await asyncio.gather(*(_probe(p) for p in target_ports))
    sorted_open = sorted(set(open_ports))
    services = map_open_ports_to_services(sorted_open)
    protocols = infer_protocols_from_ports(sorted_open)

    return {
        "ip_address": valid_ip,
        "probed_ports_count": len(target_ports),
        "open_ports": sorted_open,
        "services": services,
        "detected_protocols": protocols,
    }

