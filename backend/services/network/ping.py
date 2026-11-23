"""ICMP Echo and asynchronous TCP connect host liveness checks."""

from __future__ import annotations

import asyncio
import platform
import time
from backend.utils.ip_utils import validate_authorized_ip

QUICK_LIVENESS_PORTS: tuple[int, ...] = (
    80,
    554,
    443,
    445,
    139,
    8000,
    8080,
    37777,
    8899,
    9100,
    53,
)


async def tcp_probe_host(
    ip_address: str,
    ports: tuple[int, ...] = QUICK_LIVENESS_PORTS,
    timeout_ms: int = 500,
) -> tuple[bool, float | None, list[int]]:
    """
    Attempt rapid non-invasive TCP handshake checks against common ports.
    Even an immediate ECONNREFUSED on a local subnet proves the host IP is alive and populates the OS ARP table!
    Returns (is_alive, latency_ms, open_ports).
    """
    validate_authorized_ip(ip_address)
    timeout_sec = max(0.15, timeout_ms / 1000.0)
    open_ports: list[int] = []
    best_latency: float | None = None
    host_responded = False

    async def _check_port(port: int) -> None:
        nonlocal best_latency, host_responded
        start = time.perf_counter()
        try:
            _reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip_address, port),
                timeout=timeout_sec,
            )
            elapsed_ms = round((time.perf_counter() - start) * 1000.0, 2)
            open_ports.append(port)
            host_responded = True
            if best_latency is None or elapsed_ms < best_latency:
                best_latency = elapsed_ms
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
        except ConnectionRefusedError:
            # TCP RST received from host -> device is definitely online on the LAN
            elapsed_ms = round((time.perf_counter() - start) * 1000.0, 2)
            host_responded = True
            if best_latency is None or elapsed_ms < best_latency:
                best_latency = elapsed_ms
        except (asyncio.TimeoutError, OSError):
            pass

    await asyncio.gather(*(_check_port(p) for p in ports))
    return host_responded, best_latency, sorted(open_ports)


async def icmp_ping_host(ip_address: str, timeout_ms: int = 750) -> tuple[bool, float | None]:
    """
    Execute a single OS ICMP Echo request (`ping`) against an authorized local IPv4 address.
    Returns (is_alive, latency_ms).
    """
    validate_authorized_ip(ip_address)
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", str(max(250, timeout_ms)), ip_address]
    elif system == "darwin":
        cmd = ["ping", "-c", "1", "-W", str(max(250, timeout_ms)), ip_address]
    else:
        timeout_s = str(max(1, int(round(timeout_ms / 1000.0))))
        cmd = ["ping", "-c", "1", "-W", timeout_s, ip_address]

    start = time.perf_counter()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout_bytes, _ = await asyncio.wait_for(
            proc.communicate(), timeout=max(1.2, (timeout_ms / 1000.0) + 0.8)
        )
        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 2)
        output = stdout_bytes.decode("utf-8", errors="ignore").lower()
        if proc.returncode == 0 and ("ttl=" in output or "bytes from" in output):
            return True, elapsed_ms
        return False, None
    except Exception:
        return False, None


async def check_host_reachable(
    ip_address: str, timeout_ms: int = 700, enable_icmp: bool = True
) -> tuple[bool, float | None, list[int], str]:
    """
    Check if a host on the local network is online using concurrent TCP probing and optional ICMP ping.
    Returns (is_online, latency_ms, quick_open_ports, method_used).
    """
    tcp_task = asyncio.create_task(tcp_probe_host(ip_address, timeout_ms=timeout_ms))
    if enable_icmp:
        icmp_task = asyncio.create_task(icmp_ping_host(ip_address, timeout_ms=timeout_ms))
        (tcp_alive, tcp_lat, open_ports), (icmp_alive, icmp_lat) = await asyncio.gather(
            tcp_task, icmp_task
        )
    else:
        tcp_alive, tcp_lat, open_ports = await tcp_task
        icmp_alive, icmp_lat = False, None

    is_online = tcp_alive or icmp_alive
    latency = tcp_lat if tcp_lat is not None else icmp_lat
    methods = []
    if tcp_alive:
        methods.append("TCP")
    if icmp_alive:
        methods.append("ICMP")
    method_str = "+".join(methods) if methods else "NONE"
    return is_online, latency, open_ports, method_str

