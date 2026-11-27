"""Evidence-based device classifier.

Strictly adheres to the requirement:
- Do NOT label every device with port 80 or port 554 as a CCTV camera.
- Require corroborating discovery evidence (ONVIF response, CCTV OUI vendor, RTSP OPTIONS server signature,
  CCTV SDK port 8000/37777/34567/9000, or explicit camera/recorder banner/mDNS/SSDP metadata).
- Unknown devices are classified as UNKNOWN with transparent evidence.
"""

from __future__ import annotations

from typing import Any
from backend.core.constants import ConfidenceLevel, DeviceCategory
from backend.services.ports.service_mapper import infer_protocols_from_ports


def classify_device_from_evidence(fingerprint: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate a device fingerprint and return:
    {
      "category": DeviceCategory value,
      "confidence": ConfidenceLevel value,
      "evidence": list[str],
      "manufacturer": str | None,
      "model": str | None,
      "onvif_available": bool,
      "rtsp_available": bool,
      "detected_protocols": list[str],
    }
    """
    evidence: list[str] = list(fingerprint.get("manufacturer_evidence", []))
    open_ports: list[int] = fingerprint.get("open_ports", [])
    port_set = set(open_ports)
    banners: dict[str, Any] = fingerprint.get("banners", {})
    onvif_info: dict[str, Any] = fingerprint.get("onvif_info") or {}
    mdns_info: dict[str, Any] = fingerprint.get("mdns_info") or {}
    ssdp_info: dict[str, Any] = fingerprint.get("ssdp_info") or {}
    mac_vendor: dict[str, Any] = fingerprint.get("mac_vendor") or {}

    manufacturer: str | None = fingerprint.get("manufacturer")
    model: str | None = onvif_info.get("model") or ssdp_info.get("model") or mdns_info.get("model")
    hostname = (fingerprint.get("hostname") or "").lower()
    is_cctv_vendor = bool(fingerprint.get("is_cctv_vendor", False))
    rtsp_verified = bool(fingerprint.get("rtsp_verified", False))
    onvif_supported = bool(onvif_info.get("reachable") or onvif_info.get("onvif_supported"))

    banner_text = " ".join(str(v) for v in banners.values()).lower()
    scopes_text = " ".join(str(s) for s in onvif_info.get("scopes", [])).lower()
    ssdp_text = str(ssdp_info).lower()
    mdns_text = str(mdns_info).lower()
    combined_meta = f"{hostname} {banner_text} {scopes_text} {ssdp_text} {mdns_text} {(model or '').lower()}"

    detected_protocols = infer_protocols_from_ports(open_ports, onvif_available=onvif_supported)
    if rtsp_verified and "RTSP" not in detected_protocols:
        detected_protocols.append("RTSP")

    # 1. Check for NVR / DVR indicators first (recorders often also support ONVIF/RTSP)
    # Note: Exclude "dnvrs-webs" (which Hikvision IP cameras use as an HTTP server header)
    clean_nvr_meta = combined_meta.replace("dnvrs-webs", "")
    nvr_keywords = (" nvr", "nvr-", "nvr_", "network video recorder", "ds-76", "ds-77", "ds-96", "nvr4", "nvr5", "rln8", "rln16")
    dvr_keywords = (" dvr", "dvr-", "dvr_", "digital video recorder", "ds-72", "dh-xvr", "xvr", "xmeye")

    if any(k in clean_nvr_meta for k in nvr_keywords):
        evidence.append("Device metadata/model matched Network Video Recorder (NVR) signature")
        confidence = ConfidenceLevel.HIGH if (onvif_supported or is_cctv_vendor) else ConfidenceLevel.MEDIUM
        return {
            "category": DeviceCategory.NVR.value,
            "confidence": confidence.value,
            "evidence": evidence,
            "manufacturer": manufacturer,
            "model": model,
            "onvif_available": onvif_supported,
            "rtsp_available": rtsp_verified or (554 in port_set),
            "detected_protocols": sorted(set(detected_protocols)),
        }

    if 34567 in port_set or any(k in combined_meta for k in dvr_keywords):
        if 34567 in port_set:
            evidence.append("Detected DVR control service port 34567 (XMeye/DVR)")
        else:
            evidence.append("Device metadata/model matched Digital Video Recorder (DVR) signature")
        confidence = ConfidenceLevel.HIGH if is_cctv_vendor else ConfidenceLevel.MEDIUM
        return {
            "category": DeviceCategory.DVR.value,
            "confidence": confidence.value,
            "evidence": evidence,
            "manufacturer": manufacturer,
            "model": model,
            "onvif_available": onvif_supported,
            "rtsp_available": rtsp_verified or (554 in port_set),
            "detected_protocols": sorted(set(detected_protocols)),
        }

    # 2. Check for ONVIF Camera
    if onvif_supported:
        evidence.append("Device responded to ONVIF WS-Discovery / SOAP device service")
        return {
            "category": DeviceCategory.ONVIF_CAMERA.value,
            "confidence": ConfidenceLevel.HIGH.value,
            "evidence": evidence,
            "manufacturer": manufacturer,
            "model": model,
            "onvif_available": True,
            "rtsp_available": rtsp_verified or (554 in port_set),
            "detected_protocols": sorted(set(detected_protocols + ["ONVIF"])),
        }

    # 3. Check for IP Camera with corroborating signals
    #    - Verified RTSP OPTIONS responder (`RTSP/1.0` on port 554/8554/10554) or CCTV SDK port (8000/37777/8899/9000/34567)
    #    - Or CCTV vendor OUI / HTTP camera banner
    cctv_sdk_ports = {8000, 37777, 37778, 8899, 9000, 9527, 34567} & port_set
    camera_keywords = (
        "ipcamera",
        "ip camera",
        "netcam",
        "webfont",
        "hikvision",
        "dahua",
        "axis",
        "reolink",
        "amcrest",
        "uniview",
        "vivotek",
        "tapo",
        "vigi",
        "ezviz",
        "imou",
        "tiandy",
        "xmeye",
        "cam-",
        "ipc-",
    )
    has_camera_keyword = any(k in combined_meta for k in camera_keywords)

    camera_score = 0
    if is_cctv_vendor:
        camera_score += 2
        evidence.append(f"Identified CCTV manufacturer ({manufacturer})")
    if rtsp_verified:
        camera_score += 3
        evidence.append("Verified active RTSP streaming responder via OPTIONS handshake")
    elif 554 in port_set or 8554 in port_set or 10554 in port_set:
        camera_score += 2
        evidence.append("TCP RTSP port 554/8554/10554 open")
    if cctv_sdk_ports:
        camera_score += 3
        evidence.append(f"CCTV vendor control ports open: {sorted(cctv_sdk_ports)}")
    if has_camera_keyword:
        camera_score += 2
        evidence.append("HTTP/RTSP/mDNS service metadata contains IP camera signature")

    if camera_score >= 3:
        conf = ConfidenceLevel.HIGH if camera_score >= 4 else ConfidenceLevel.MEDIUM
        return {
            "category": DeviceCategory.CAMERA.value,
            "confidence": conf.value,
            "evidence": evidence,
            "manufacturer": manufacturer,
            "model": model,
            "onvif_available": False,
            "rtsp_available": rtsp_verified or bool({554, 8554, 10554} & port_set),
            "detected_protocols": sorted(set(detected_protocols)),
        }

    # 4. Check for Router / Gateway / Managed Network Switch / Access Point
    is_managed_switch_or_ap = (
        ("logoninfo" in banner_text and "g_lan" in banner_text)
        or ("/base/nanoscroller.css" in banner_text)
        or hostname.startswith(("rap22", "rg-es", "rg-eg", "rg-nbr", "eap", "unifi", "ap-"))
        or (
            manufacturer
            and any(v in manufacturer.lower() for v in ("tp-link", "netgear", "cisco", "ubiquiti", "d-link", "mikrotik", "ruijie"))
            and 80 in port_set
            and 445 not in port_set
        )
    )
    if (
        fingerprint.get("is_gateway")
        or (53 in port_set and (80 in port_set or 443 in port_set))
        or is_managed_switch_or_ap
    ):
        if fingerprint.get("is_gateway"):
            evidence.append("Device IP matches the active subnet's default gateway")
            model = model or "Network Gateway / Router"
        elif hostname.startswith("rap"):
            evidence.append(f"Hostname '{hostname}' identifies Ruijie Reyee Wireless Access Point")
            model = model or f"Reyee Wi-Fi Access Point ({hostname.split('.')[0].upper()})"
        elif hostname.startswith("rg-es"):
            evidence.append(f"Hostname '{hostname}' identifies Ruijie Smart PoE Managed Switch")
            model = model or f"Ruijie Smart Managed Switch ({hostname.split('.')[0].upper()})"
        elif 53 in port_set:
            evidence.append("DNS resolver port 53 open alongside web administration")
            model = model or "DNS / Network Router"
        elif is_managed_switch_or_ap:
            evidence.append("HTTP management interface matched managed network switch / AP")
            model = model or "Managed Network Switch / AP"
        return {
            "category": DeviceCategory.ROUTER.value,
            "confidence": ConfidenceLevel.HIGH.value if (fingerprint.get("is_gateway") or hostname.startswith(("rap", "rg-"))) else ConfidenceLevel.MEDIUM.value,
            "evidence": evidence,
            "manufacturer": manufacturer,
            "model": model,
            "onvif_available": False,
            "rtsp_available": False,
            "detected_protocols": sorted(set(detected_protocols)),
        }

    # 5. Check for Network Printer
    if 9100 in port_set or 631 in port_set or mac_vendor.get("category_hint") == "PRINTER":
        if 9100 in port_set or 631 in port_set:
            evidence.append("Network printing ports (631 IPP / 9100 JetDirect) open")
        if mac_vendor.get("category_hint") == "PRINTER":
            evidence.append(f"MAC OUI belongs to printer vendor ({manufacturer})")
        return {
            "category": DeviceCategory.PRINTER.value,
            "confidence": ConfidenceLevel.HIGH.value if (9100 in port_set and mac_vendor.get("category_hint") == "PRINTER") else ConfidenceLevel.MEDIUM.value,
            "evidence": evidence,
            "manufacturer": manufacturer,
            "model": model or "Network Printer",
            "onvif_available": False,
            "rtsp_available": False,
            "detected_protocols": sorted(set(detected_protocols)),
        }

    # 6. Check for Computer / Workstation / Host / NAS Server / Mobile Device
    mobile_tokens = ("xiaomi", "redmi", "realme", "oppo", "vivo", "s23", "s24", "galaxy", "iphone", "ipad", "lmu-lx9", "honor", "21051182g")
    is_mobile_or_client = any(t in hostname for t in mobile_tokens) or ("lpt" in hostname or "pc" in hostname or "desktop" in hostname or "macbook" in hostname)
    if fingerprint.get("is_host") or 445 in port_set or mac_vendor.get("category_hint") == "COMPUTER" or is_mobile_or_client:
        if fingerprint.get("is_host"):
            evidence.append("Device is the local host machine running the scanner")
            inferred_model = "Local Scanner Host"
        elif manufacturer and "qnap" in manufacturer.lower():
            evidence.append("QNAP NAS storage server signature (SMB 445 + Web Admin)")
            inferred_model = "QNAP NAS Storage Server"
        elif manufacturer and "synology" in manufacturer.lower():
            evidence.append("Synology NAS storage server signature")
            inferred_model = "Synology NAS Server"
        elif 445 in port_set:
            evidence.append("SMB/CIFS workstation file-sharing port 445 open")
            inferred_model = "Windows / SMB Workstation"
        elif is_mobile_or_client:
            evidence.append(f"Hostname '{hostname}' identifies client workstation / mobile device")
            inferred_model = f"Client Device ({hostname.split('.')[0]})"
        else:
            evidence.append(f"MAC OUI belongs to computer hardware vendor ({manufacturer})")
            inferred_model = "Desktop / Laptop Workstation"
        return {
            "category": DeviceCategory.COMPUTER.value,
            "confidence": ConfidenceLevel.HIGH.value if fingerprint.get("is_host") else ConfidenceLevel.MEDIUM.value,
            "evidence": evidence,
            "manufacturer": manufacturer,
            "model": model or inferred_model,
            "onvif_available": False,
            "rtsp_available": False,
            "detected_protocols": sorted(set(detected_protocols)),
        }

    # 6b. Check if MAC address uses a randomized Locally Administered bit (bit 1 of first octet: x2, x6, xA, xE)
    #     when no server ports are open (typical iOS / Android / macOS Wi-Fi client)
    mac_addr = fingerprint.get("mac_address") or ""
    if not open_ports and len(mac_addr) >= 2 and mac_addr[1].upper() in {"2", "6", "A", "E"}:
        evidence.append(f"MAC {mac_addr} uses Locally Administered / Randomized Privacy MAC (iOS / Android / macOS Wi-Fi client)")
        return {
            "category": DeviceCategory.COMPUTER.value,
            "confidence": ConfidenceLevel.LOW.value,
            "evidence": evidence,
            "manufacturer": manufacturer or "Mobile / Wi-Fi Client (Randomized MAC)",
            "model": model or "Smartphone / Tablet / Laptop",
            "onvif_available": False,
            "rtsp_available": False,
            "detected_protocols": sorted(set(detected_protocols)),
        }

    # 7. Fallback: Do NOT invent a camera when only port 80 or 554 is open without corroboration!
    if open_ports:
        evidence.append(f"Responded on TCP ports {open_ports}, but no conclusive device category signature matched")
        fallback_conf = ConfidenceLevel.LOW.value
    else:
        evidence.append("Host responded to ARP/ICMP liveness check without identifiable service ports")
        fallback_conf = ConfidenceLevel.UNKNOWN.value

    return {
        "category": DeviceCategory.UNKNOWN.value,
        "confidence": fallback_conf,
        "evidence": evidence,
        "manufacturer": manufacturer,
        "model": model,
        "onvif_available": False,
        "rtsp_available": rtsp_verified,
        "detected_protocols": sorted(set(detected_protocols)),
    }
