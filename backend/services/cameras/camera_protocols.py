"""Camera RTSP and HTTP snapshot URL template resolution per manufacturer."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote, urlparse, urlunparse
from backend.app.config import get_settings
from backend.utils.ip_utils import validate_authorized_ip


def get_manufacturer_rtsp_paths(
    manufacturer: str | None, channel: int = 1, subtype: int = 0
) -> list[str]:
    """
    Return ordered candidate RTSP paths for a camera manufacturer, channel (1-based),
    and subtype (0 = Main Stream HD, 1 = Sub Stream SD).
    """
    mfg = (manufacturer or "").lower()
    sub_idx = 1 if subtype == 0 else 2
    reolink_sub = "main" if subtype == 0 else "sub"

    candidates: list[str] = []
    if "hikvision" in mfg:
        candidates.extend(
            [
                f"/Streaming/Channels/{channel}0{sub_idx}",
                f"/h264/ch{channel}/{'main' if subtype == 0 else 'sub'}/av_stream",
            ]
        )
    elif "dahua" in mfg or "amcrest" in mfg:
        candidates.append(f"/cam/realmonitor?channel={channel}&subtype={subtype}")
    elif "axis" in mfg:
        candidates.extend(["/axis-media/media.amp", "/mpeg4/media.amp"])
    elif "reolink" in mfg:
        candidates.append(f"/h264Preview_{channel:02d}_{reolink_sub}")
    elif "uniview" in mfg or "unv" in mfg:
        candidates.extend([f"/media/video{sub_idx}", f"/unicast/c{channel}/s{subtype}/live"])
    elif "hanwha" in mfg or "samsung" in mfg:
        candidates.append(f"/profile{2 if subtype == 0 else 1}/media.smp")
    elif "tp-link" in mfg or "tapo" in mfg:
        candidates.append(f"/stream{sub_idx}")

    # Load fallback templates from config/manufacturers.json
    settings = get_settings()
    mfg_file = settings.config_dir / "manufacturers.json"
    if mfg_file.exists():
        try:
            data = json.loads(mfg_file.read_text(encoding="utf-8"))
            generic_list = data.get("rtsp_templates", {}).get("Generic", [])
            for path in generic_list:
                if path not in candidates:
                    candidates.append(path)
        except Exception:
            pass

    if not candidates:
        candidates = [
            f"/Streaming/Channels/{channel}0{sub_idx}",
            f"/cam/realmonitor?channel={channel}&subtype={subtype}",
            "/stream1",
            "/live/ch0",
        ]
    return candidates


def get_manufacturer_snapshot_paths(manufacturer: str | None, channel: int = 1) -> list[str]:
    """Return ordered HTTP snapshot endpoint paths for a camera manufacturer."""
    mfg = (manufacturer or "").lower()
    if "hikvision" in mfg:
        return [f"/ISAPI/Streaming/channels/{channel}01/picture", "/onvif-http/snapshot"]
    if "dahua" in mfg or "amcrest" in mfg:
        return [f"/cgi-bin/snapshot.cgi?channel={channel}", "/cgi-bin/snapshot.cgi"]
    if "axis" in mfg:
        return ["/axis-cgi/jpg/image.cgi"]
    if "reolink" in mfg:
        return [f"/cgi-bin/api.cgi?cmd=Snap&channel={max(0, channel - 1)}"]
    return [
        "/snapshot.jpg",
        "/cgi-bin/snapshot.cgi",
        f"/ISAPI/Streaming/channels/{channel}01/picture",
        "/axis-cgi/jpg/image.cgi",
    ]


def build_authenticated_rtsp_url(
    ip_address: str,
    rtsp_port: int = 554,
    stream_path: str = "/Streaming/Channels/101",
    username: str | None = None,
    password: str | None = None,
) -> str:
    """
    Construct a server-side RTSP URL with URL-encoded credentials.
    This URL is ONLY used inside backend server-side FFmpeg/RTSP connections and is
    NEVER returned unmasked to frontend clients.
    """
    valid_ip = validate_authorized_ip(ip_address)
    path = stream_path if stream_path.startswith("/") else f"/{stream_path}"
    auth_prefix = ""
    if username:
        enc_user = quote(username, safe="")
        if password is not None and password != "":
            enc_pass = quote(password, safe="")
            auth_prefix = f"{enc_user}:{enc_pass}@"
        else:
            auth_prefix = f"{enc_user}@"
    return f"rtsp://{auth_prefix}{valid_ip}:{int(rtsp_port)}{path}"


def inject_credentials_into_uri(
    uri: str, username: str | None, password: str | None
) -> str:
    """Inject username and password into an ONVIF-returned RTSP or HTTP URI server-side."""
    if not username:
        return uri
    parsed = urlparse(uri)
    host_port = f"{parsed.hostname}:{parsed.port}" if parsed.port else (parsed.hostname or "")
    enc_user = quote(username, safe="")
    enc_pass = quote(password or "", safe="")
    netloc = f"{enc_user}:{enc_pass}@{host_port}" if password else f"{enc_user}@{host_port}"
    return urlunparse(
        (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
    )


def describe_camera_protocols(
    open_ports: list[int], onvif_supported: bool, rtsp_available: bool
) -> dict[str, Any]:
    """Return structured protocol capability summary for a camera."""
    port_set = set(open_ports)
    return {
        "onvif": {
            "supported": onvif_supported,
            "ports": [p for p in (80, 8899, 8000, 8080) if p in port_set],
        },
        "rtsp": {
            "available": rtsp_available or (554 in port_set) or (8554 in port_set),
            "ports": [p for p in (554, 8554) if p in port_set] or [554],
        },
        "http_web": {
            "available": bool({80, 443, 8080, 8443, 8000} & port_set),
            "ports": [p for p in (80, 443, 8080, 8443, 8000) if p in port_set],
        },
    }

