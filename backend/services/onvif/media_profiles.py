"""ONVIF Media GetProfiles, GetStreamUri, and GetSnapshotUri retrieval."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlparse
from backend.services.onvif.connection import send_onvif_soap_request
from backend.utils.ip_utils import mask_rtsp_url


def parse_media_profiles_xml(xml_text: str) -> list[dict[str, Any]]:
    """Parse ONVIF GetProfiles response into structured media profile items."""
    profiles: list[dict[str, Any]] = []
    if not xml_text:
        return profiles
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return profiles

    for elem in root.iter():
        local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if local_name == "Profiles":
            token = elem.attrib.get("token", "")
            name = token
            encoding = None
            width = None
            height = None

            for sub in elem.iter():
                sub_name = sub.tag.split("}")[-1] if "}" in sub.tag else sub.tag
                txt = (sub.text or "").strip()
                if sub_name == "Name" and name == token and txt:
                    name = txt
                elif sub_name == "Encoding" and txt:
                    encoding = txt
                elif sub_name == "Width" and txt:
                    width = txt
                elif sub_name == "Height" and txt:
                    height = txt

            resolution = f"{width}x{height}" if (width and height) else None
            profiles.append(
                {
                    "token": token,
                    "name": name,
                    "encoding": encoding or "H264",
                    "resolution": resolution,
                }
            )
    return profiles


def parse_uri_from_xml(xml_text: str) -> str | None:
    """Extract <tt:Uri> text from GetStreamUri or GetSnapshotUri SOAP response."""
    if not xml_text:
        return None
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None
    for elem in root.iter():
        local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if local_name == "Uri" and elem.text:
            return elem.text.strip()
    return None


async def fetch_onvif_media_profiles_and_streams(
    ip_address: str,
    port: int = 80,
    media_xaddr: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> list[dict[str, Any]]:
    """
    Query ONVIF Media service for GetProfiles, and for each profile retrieve its
    RTSP StreamUri and SnapshotUri when supported.
    """
    service_path = "/onvif/media_service"
    if media_xaddr:
        try:
            parsed = urlparse(media_xaddr)
            if parsed.path:
                service_path = parsed.path
        except Exception:
            pass

    res = await send_onvif_soap_request(
        ip_address=ip_address,
        port=port,
        service_path=service_path,
        body_xml="<trt:GetProfiles/>",
        username=username,
        password=password,
    )
    if not res.get("ok"):
        return []

    profiles = parse_media_profiles_xml(res.get("xml", ""))
    for prof in profiles[:8]:
        token = prof.get("token")
        if not token:
            continue
        stream_body = (
            "<trt:GetStreamUri>"
            "<trt:StreamSetup>"
            "<tt:Stream>RTP-Unicast</tt:Stream>"
            "<tt:Transport><tt:Protocol>RTSP</tt:Protocol></tt:Transport>"
            "</trt:StreamSetup>"
            f"<trt:ProfileToken>{token}</trt:ProfileToken>"
            "</trt:GetStreamUri>"
        )
        uri_res = await send_onvif_soap_request(
            ip_address=ip_address,
            port=port,
            service_path=service_path,
            body_xml=stream_body,
            username=username,
            password=password,
        )
        raw_uri = parse_uri_from_xml(uri_res.get("xml", "")) if uri_res.get("ok") else None
        prof["stream_uri"] = raw_uri
        prof["stream_uri_masked"] = mask_rtsp_url(raw_uri)

        snap_body = f"<trt:GetSnapshotUri><trt:ProfileToken>{token}</trt:ProfileToken></trt:GetSnapshotUri>"
        snap_res = await send_onvif_soap_request(
            ip_address=ip_address,
            port=port,
            service_path=service_path,
            body_xml=snap_body,
            username=username,
            password=password,
        )
        prof["snapshot_uri"] = parse_uri_from_xml(snap_res.get("xml", "")) if snap_res.get("ok") else None

    return profiles

