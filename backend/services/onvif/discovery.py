"""ONVIF UDP multicast WS-Discovery implementation (239.255.255.250:3702)."""

from __future__ import annotations

import asyncio
import re
import socket
import uuid
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlparse
from backend.core.constants import ONVIF_MULTICAST_IP, ONVIF_MULTICAST_PORT
from backend.core.logging import get_logger
from backend.utils.ip_utils import is_authorized_private_ip

logger = get_logger("onvif_discovery")


def build_ws_discovery_probe_xml(message_id: str | None = None) -> str:
    """Build standard ONVIF WS-Discovery Probe SOAP 1.2 envelope for NetworkVideoTransmitter."""
    msg_uuid = message_id or f"uuid:{uuid.uuid4()}"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope" '
        'xmlns:w="http://schemas.xmlsoap.org/ws/2004/08/addressing" '
        'xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery" '
        'xmlns:dn="http://www.onvif.org/ver10/network/wsdl">'
        "<e:Header>"
        f"<w:MessageID>{msg_uuid}</w:MessageID>"
        '<w:To e:mustUnderstand="true">urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To>'
        '<w:Action a:mustUnderstand="true" xmlns:a="http://www.w3.org/2003/05/soap-envelope">'
        "http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</w:Action>"
        "</e:Header>"
        "<e:Body>"
        "<d:Probe>"
        "<d:Types>dn:NetworkVideoTransmitter</d:Types>"
        "</d:Probe>"
        "</e:Body>"
        "</e:Envelope>"
    )


def parse_ws_discovery_response(xml_text: str, sender_ip: str) -> dict[str, Any] | None:
    """
    Parse an ONVIF WS-Discovery ProbeMatch XML payload.
    Extracts XAddrs, Scopes, Types, EndpointReference, manufacturer/model/name from onvif:// scopes.
    """
    if not xml_text or "ProbeMatch" not in xml_text:
        return None

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    xaddrs_list: list[str] = []
    scopes_list: list[str] = []
    types_list: list[str] = []
    endpoint_ref: str | None = None

    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        text_val = (elem.text or "").strip()
        if not text_val:
            continue
        if tag == "XAddrs":
            xaddrs_list.extend(text_val.split())
        elif tag == "Scopes":
            scopes_list.extend(text_val.split())
        elif tag == "Types":
            types_list.extend(text_val.split())
        elif tag == "Address" and not endpoint_ref:
            endpoint_ref = text_val

    manufacturer: str | None = None
    model: str | None = None
    location: str | None = None

    for scope in scopes_list:
        lower = scope.lower()
        if "onvif://www.onvif.org/name/" in lower:
            raw_name = scope.split("/name/", 1)[1].replace("%20", " ")
            if not model:
                model = raw_name
        elif "onvif://www.onvif.org/hardware/" in lower:
            hw = scope.split("/hardware/", 1)[1].replace("%20", " ")
            model = hw
        elif "onvif://www.onvif.org/manufacturer/" in lower or "onvif://www.onvif.org/mfg/" in lower:
            mfg_part = re.split(r"/(?:manufacturer|mfg)/", scope, flags=re.IGNORECASE)[1]
            manufacturer = mfg_part.replace("%20", " ")
        elif "onvif://www.onvif.org/location/" in lower:
            location = scope.split("/location/", 1)[1].replace("%20", " ")

    onvif_port = 80
    for xaddr in xaddrs_list:
        try:
            parsed = urlparse(xaddr)
            if parsed.port:
                onvif_port = parsed.port
                break
        except Exception:
            pass

    return {
        "ip_address": sender_ip,
        "onvif_port": onvif_port,
        "xaddrs": xaddrs_list,
        "scopes": scopes_list,
        "types": types_list,
        "endpoint_reference": endpoint_ref,
        "manufacturer": manufacturer,
        "model": model,
        "location": location,
        "onvif_supported": True,
    }


def _sync_multicast_ws_discovery(timeout_seconds: float = 2.5) -> list[dict[str, Any]]:
    """Send UDP multicast WS-Discovery probes and collect responses until timeout."""
    discovered_by_ip: dict[str, dict[str, Any]] = {}
    probe_bytes = build_ws_discovery_probe_xml().encode("utf-8")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.settimeout(0.4)
        sock.sendto(probe_bytes, (ONVIF_MULTICAST_IP, ONVIF_MULTICAST_PORT))

        import time
        deadline = time.monotonic() + max(0.5, timeout_seconds)
        while time.monotonic() < deadline:
            try:
                data, addr = sock.recvfrom(65535)
                sender_ip = addr[0]
                if not is_authorized_private_ip(sender_ip):
                    continue
                xml_str = data.decode("utf-8", errors="ignore")
                parsed = parse_ws_discovery_response(xml_str, sender_ip)
                if parsed:
                    discovered_by_ip[sender_ip] = parsed
            except socket.timeout:
                continue
            except OSError:
                break
    except Exception as exc:
        logger.debug("ONVIF multicast socket error: %s", exc)
    finally:
        sock.close()

    return list(discovered_by_ip.values())


async def discover_onvif_devices(timeout_seconds: float = 2.5) -> list[dict[str, Any]]:
    """Run ONVIF UDP multicast discovery asynchronously."""
    return await asyncio.to_thread(_sync_multicast_ws_discovery, timeout_seconds)

