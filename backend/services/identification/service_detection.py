"""Non-invasive HTTP and RTSP service header inspection."""

from __future__ import annotations

import asyncio
import re
from typing import Any
import httpx
from backend.utils.ip_utils import validate_authorized_ip

TITLE_REGEX = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


async def probe_http_service(
    ip_address: str, port: int = 80, use_https: bool = False, timeout: float = 1.5
) -> dict[str, Any]:
    """
    Perform a safe HTTP GET `/` request to inspect Server headers, WWW-Authenticate realm, and HTML <title>.
    Does not attempt authentication or brute-forcing.
    """
    valid_ip = validate_authorized_ip(ip_address)
    scheme = "https" if use_https or port in (443, 8443) else "http"
    url = f"{scheme}://{valid_ip}:{port}/"
    try:
        async with httpx.AsyncClient(verify=False, timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url)
            server_hdr = resp.headers.get("server", "")
            auth_hdr = resp.headers.get("www-authenticate", "")
            content_sample = resp.text[:4096] if resp.text else ""
            title_match = TITLE_REGEX.search(content_sample)
            page_title = title_match.group(1).strip() if title_match else ""
            return {
                "reachable": True,
                "status_code": resp.status_code,
                "server": server_hdr,
                "www_authenticate": auth_hdr,
                "title": page_title[:120],
                "snippet": content_sample[:320],
            }
    except Exception:
        return {"reachable": False}


async def probe_rtsp_options(
    ip_address: str, port: int = 554, timeout: float = 1.5
) -> dict[str, Any]:
    """
    Perform a non-invasive RTSP OPTIONS handshake (`OPTIONS * RTSP/1.0`) to verify
    whether port 554/8554 is genuinely speaking RTSP and capture its Server header.
    """
    valid_ip = validate_authorized_ip(ip_address)
    request_bytes = (
        f"OPTIONS rtsp://{valid_ip}:{port}/ RTSP/1.0\r\n"
        f"CSeq: 1\r\n"
        f"User-Agent: CCTV-Discovery-Assistant/1.0\r\n\r\n"
    ).encode("ascii")

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(valid_ip, port), timeout=timeout
        )
        writer.write(request_bytes)
        await writer.drain()
        raw_resp = await asyncio.wait_for(reader.read(1024), timeout=timeout)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass

        text = raw_resp.decode("utf-8", errors="ignore")
        if text.startswith("RTSP/1.0"):
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            status_line = lines[0] if lines else "RTSP/1.0"
            server_hdr = ""
            public_methods = ""
            for line in lines[1:]:
                if line.lower().startswith("server:"):
                    server_hdr = line.split(":", 1)[1].strip()
                elif line.lower().startswith("public:"):
                    public_methods = line.split(":", 1)[1].strip()
            return {
                "is_rtsp": True,
                "status_line": status_line,
                "server": server_hdr,
                "public_methods": public_methods,
                "requires_auth": "401" in status_line,
            }
    except Exception:
        pass

    return {"is_rtsp": False}


async def inspect_device_services(
    ip_address: str, open_ports: list[int]
) -> dict[str, Any]:
    """Inspect open HTTP/HTTPS and RTSP ports on a discovered device."""
    banners: dict[str, Any] = {}
    rtsp_verified = False
    port_set = set(open_ports)

    tasks: list[tuple[str, asyncio.Task[dict[str, Any]]]] = []
    for http_p in (80, 81, 82, 88, 8080, 8000, 8899):
        if http_p in port_set:
            tasks.append((f"http_{http_p}", asyncio.create_task(probe_http_service(ip_address, http_p, False))))
    for https_p in (443, 8443):
        if https_p in port_set:
            tasks.append((f"https_{https_p}", asyncio.create_task(probe_http_service(ip_address, https_p, True))))
    for rtsp_p in (554, 8554, 10554):
        if rtsp_p in port_set:
            tasks.append((f"rtsp_{rtsp_p}", asyncio.create_task(probe_rtsp_options(ip_address, rtsp_p))))

    for key, task in tasks:
        res = await task
        if res.get("reachable") or res.get("is_rtsp"):
            banners[key] = res
            if res.get("is_rtsp"):
                rtsp_verified = True

    return {
        "banners": banners,
        "rtsp_verified": rtsp_verified,
    }

