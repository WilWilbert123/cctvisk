"""mDNS / Zeroconf service discovery for IP cameras, Axis/RTSP streams, printers, and computers."""

from __future__ import annotations

import asyncio
import socket
import time
from typing import Any
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
from backend.core.logging import get_logger
from backend.utils.ip_utils import is_authorized_private_ip

logger = get_logger("mdns_discovery")

MDNS_SERVICE_TYPES: list[str] = [
    "_rtsp._tcp.local.",
    "_axis-video._tcp.local.",
    "_onvif._tcp.local.",
    "_http._tcp.local.",
    "_ipp._tcp.local.",
    "_printer._tcp.local.",
    "_smb._tcp.local.",
    "_workstation._tcp.local.",
]


class _MDNSCollector(ServiceListener):
    def __init__(self, zc: Zeroconf) -> None:
        self.zc = zc
        self.records: dict[str, dict[str, Any]] = {}

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self._resolve(zc, type_, name)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self._resolve(zc, type_, name)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def _resolve(self, zc: Zeroconf, type_: str, name: str) -> None:
        try:
            info = zc.get_service_info(type_, name, timeout=800)
            if not info:
                return
            for addr_bytes in info.addresses:
                if len(addr_bytes) == 4:
                    ip_str = socket.inet_ntoa(addr_bytes)
                    if not is_authorized_private_ip(ip_str):
                        continue
                    props: dict[str, str] = {}
                    for k, v in (info.properties or {}).items():
                        key_s = k.decode("utf-8", errors="ignore") if isinstance(k, bytes) else str(k)
                        val_s = v.decode("utf-8", errors="ignore") if isinstance(v, bytes) else str(v)
                        props[key_s] = val_s

                    entry = self.records.setdefault(
                        ip_str,
                        {
                            "ip_address": ip_str,
                            "hostname": (info.server or "").rstrip("."),
                            "services": [],
                            "properties": {},
                            "model": props.get("model") or props.get("ty") or props.get("product"),
                        },
                    )
                    entry["services"].append(
                        {"type": type_, "name": name, "port": info.port}
                    )
                    entry["properties"].update(props)
        except Exception:
            pass


def _sync_mdns_discover(timeout_seconds: float = 2.0) -> list[dict[str, Any]]:
    try:
        zc = Zeroconf()
    except Exception as exc:
        logger.debug("Zeroconf initialization skipped: %s", exc)
        return []

    collector = _MDNSCollector(zc)
    try:
        _browsers = [ServiceBrowser(zc, st, collector) for st in MDNS_SERVICE_TYPES]
        time.sleep(max(0.5, min(5.0, timeout_seconds)))
    except Exception as exc:
        logger.debug("Zeroconf browse error: %s", exc)
    finally:
        try:
            zc.close()
        except Exception:
            pass

    return list(collector.records.values())


async def discover_mdns_services(timeout_seconds: float = 2.0) -> list[dict[str, Any]]:
    """Run Zeroconf mDNS service discovery asynchronously."""
    return await asyncio.to_thread(_sync_mdns_discover, timeout_seconds)

