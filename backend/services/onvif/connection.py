"""ONVIF SOAP 1.2 HTTP connection with WS-Security UsernameToken PasswordDigest support."""

from __future__ import annotations

import base64
import hashlib
import os
from datetime import datetime, timezone
from typing import Any
import httpx
from backend.utils.ip_utils import validate_authorized_ip


def build_wsse_security_header(username: str, password: str) -> str:
    """
    Construct an ONVIF-compliant WS-Security UsernameToken header using
    Base64(SHA1(nonce_bytes + created_utf8 + password_utf8)).
    """
    nonce_bytes = os.urandom(16)
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    digest_raw = hashlib.sha1(
        nonce_bytes + created.encode("utf-8") + password.encode("utf-8")
    ).digest()
    password_digest = base64.b64encode(digest_raw).decode("ascii")
    nonce_b64 = base64.b64encode(nonce_bytes).decode("ascii")

    return (
        '<Security s:mustUnderstand="1" '
        'xmlns="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">'
        "<UsernameToken>"
        f"<Username>{username}</Username>"
        '<Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordDigest">'
        f"{password_digest}</Password>"
        '<Nonce EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary">'
        f"{nonce_b64}</Nonce>"
        '<Created xmlns="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">'
        f"{created}</Created>"
        "</UsernameToken>"
        "</Security>"
    )


def wrap_soap_envelope(body_xml: str, username: str | None = None, password: str | None = None) -> str:
    """Wrap an ONVIF request body in a SOAP 1.2 envelope with optional WS-Security header."""
    header_xml = ""
    if username and password is not None:
        header_xml = f"<s:Header>{build_wsse_security_header(username, password)}</s:Header>"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" '
        'xmlns:tds="http://www.onvif.org/ver10/device/wsdl" '
        'xmlns:trt="http://www.onvif.org/ver10/media/wsdl" '
        'xmlns:tt="http://www.onvif.org/ver10/schema">'
        f"{header_xml}"
        f"<s:Body>{body_xml}</s:Body>"
        "</s:Envelope>"
    )


async def send_onvif_soap_request(
    ip_address: str,
    port: int,
    service_path: str,
    body_xml: str,
    username: str | None = None,
    password: str | None = None,
    timeout: float = 3.0,
) -> dict[str, Any]:
    """Send a SOAP 1.2 request to an authorized local ONVIF device endpoint."""
    valid_ip = validate_authorized_ip(ip_address)
    scheme = "https" if port in (443, 8443) else "http"
    url = f"{scheme}://{valid_ip}:{port}{service_path}"
    envelope = wrap_soap_envelope(body_xml, username=username, password=password)
    headers = {"Content-Type": "application/soap+xml; charset=utf-8"}

    auth = httpx.DigestAuth(username, password) if (username and password is not None) else None

    try:
        async with httpx.AsyncClient(verify=False, timeout=timeout, auth=auth) as client:
            resp = await client.post(url, content=envelope.encode("utf-8"), headers=headers)
            text = resp.text or ""
            if resp.status_code in (401, 403) or "NotAuthorized" in text or "Sender" in text and "Authorized" in text:
                return {
                    "ok": False,
                    "status_code": resp.status_code,
                    "auth_required": True,
                    "xml": text,
                    "error": "ONVIF authentication required or credentials rejected.",
                }
            if resp.status_code == 200 and "Envelope" in text:
                return {
                    "ok": True,
                    "status_code": 200,
                    "auth_required": False,
                    "xml": text,
                }
            return {
                "ok": False,
                "status_code": resp.status_code,
                "auth_required": False,
                "xml": text,
                "error": f"HTTP {resp.status_code}",
            }
    except Exception as exc:
        return {
            "ok": False,
            "status_code": 0,
            "auth_required": False,
            "xml": "",
            "error": str(exc),
        }
