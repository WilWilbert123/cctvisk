"""Background discovery worker executing multicast ONVIF, mDNS, and SSDP sweeps."""

from __future__ import annotations

from typing import Any
from backend.services.discovery.device_discovery import run_targeted_discovery_probes


async def run_discovery_worker(
    methods: list[str] | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """Execute ONVIF, mDNS, and SSDP multicast probes and update the discovery state store."""
    return await run_targeted_discovery_probes(
        methods=methods, timeout_seconds=timeout_seconds
    )

