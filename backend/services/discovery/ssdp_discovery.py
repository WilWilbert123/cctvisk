"""SSDP (Simple Service Discovery Protocol) UPnP multicast discovery (239.255.255.250:1900)."""

from __future__ import annotations

import asyncio
import socket
import time
from typing import Any
from backend.core.constants import SSDP_MULTICAST_IP, SSDP_MULTICAST_PORT
from backend.core.logging import get_logger
from backend.utils.ip_utils import is_authorized_private_ip

logger = get_logger("ssdp_discovery")


def build_ssdp_msearch_packet(search_target: str = "ssdp:all", mx: int = 2) -> bytes:
    """Build standard UDP M-SEARCH multicast payload."""
    lines = [
        "M-SEARCH * HTTP/1.1",
        f"HOST: {SSDP_MULTICAST_IP}:{SSDP_MULTICAST_PORT}",
        'MAN: "ssdp:discover"',
        f"MX: {mx}",
        f"ST: {search_target}",
        "USER-AGENT: CCTV-Discovery-Assistant/1.0 UPnP/1.1",
        "",
        "",
    ]
    return "\r\n".join(lines).encode("ascii")


def parse_ssdp_response(raw_text: str, sender_ip: str) -> dict[str, Any] | None:
    """Parse HTTP-like SSDP 200 OK header lines."""
    if not raw_text or "200 OK" not in raw_text.splitlines()[0]:
        return None
    headers: dict[str, str] = {}
    for line in raw_text.splitlines()[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()

    return {
        "ip_address": sender_ip,
        "server": headers.get("server", ""),
        "location": headers.get("location", ""),
        "st": headers.get("st", ""),
        "usn": headers.get("usn", ""),
    }


def _sync_ssdp_discover(timeout_seconds: float = 2.0) -> list[dict[str, Any]]:
    results_by_ip: dict[str, dict[str, Any]] = {}
    packet = build_ssdp_msearch_packet()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.settimeout(0.35)
        sock.sendto(packet, (SSDP_MULTICAST_IP, SSDP_MULTICAST_PORT))

        deadline = time.monotonic() + max(0.5, min(5.0, timeout_seconds))
        while time.monotonic() < deadline:
            try:
                data, addr = sock.recvfrom(8192)
                sender_ip = addr[0]
                if not is_authorized_private_ip(sender_ip):
                    continue
                parsed = parse_ssdp_response(data.decode("utf-8", errors="ignore"), sender_ip)
                if parsed:
                    results_by_ip[sender_ip] = parsed
            except socket.timeout:
                continue
            except OSError:
                break
    except Exception as exc:
        logger.debug("SSDP discovery socket error: %s", exc)
    finally:
        sock.close()

    return list(results_by_ip.values())


async def discover_ssdp_devices(timeout_seconds: float = 2.0) -> list[dict[str, Any]]:
    """Run SSDP UPnP multicast discovery asynchronously."""
    return await asyncio.to_thread(_sync_ssdp_discover, timeout_seconds)

