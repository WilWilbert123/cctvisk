"""Unified Device Discovery Coordinator combining Subnet Scan, ONVIF, mDNS, SSDP, Port Scanning, and Classification."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any
from backend.app.config import get_settings
from backend.core.logging import get_logger
from backend.services.discovery.camera_discovery import extract_camera_candidate_attributes
from backend.services.discovery.mdns_discovery import discover_mdns_services
from backend.services.discovery.nvr_discovery import extract_nvr_candidate_attributes
from backend.services.discovery.onvif_discovery import (
    interrogate_onvif_device,
    run_onvif_discovery_with_enrichment,
)
from backend.services.discovery.ssdp_discovery import discover_ssdp_devices
from backend.services.identification.device_classifier import classify_device_from_evidence
from backend.services.identification.device_fingerprint import build_device_fingerprint
from backend.services.ports.port_scanner import scan_device_ports

logger = get_logger("device_discovery")


class DiscoveryStateStore:
    """In-memory cache of the most recent raw ONVIF, mDNS, SSDP, and fingerprint evidence."""

    def __init__(self) -> None:
        self.onvif_results: list[dict[str, Any]] = []
        self.mdns_results: list[dict[str, Any]] = []
        self.ssdp_results: list[dict[str, Any]] = []
        self.fingerprints: list[dict[str, Any]] = []
        self.last_updated: str | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "onvif": self.onvif_results,
            "mdns": self.mdns_results,
            "ssdp": self.ssdp_results,
            "fingerprints": self.fingerprints,
            "last_updated": self.last_updated,
        }


discovery_state = DiscoveryStateStore()


async def run_targeted_discovery_probes(
    methods: list[str] | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """Run multicast/broadcast ONVIF, mDNS, and SSDP discovery probes in parallel."""
    settings = get_settings()
    selected = {m.lower() for m in (methods or ["onvif", "mdns", "ssdp"])}

    onvif_task = (
        asyncio.create_task(
            run_onvif_discovery_with_enrichment(
                timeout_seconds or settings.ONVIF_DISCOVERY_TIMEOUT_SECONDS
            )
        )
        if "onvif" in selected
        else None
    )
    mdns_task = (
        asyncio.create_task(
            discover_mdns_services(timeout_seconds or settings.MDNS_DISCOVERY_TIMEOUT_SECONDS)
        )
        if "mdns" in selected
        else None
    )
    ssdp_task = (
        asyncio.create_task(
            discover_ssdp_devices(timeout_seconds or settings.SSDP_DISCOVERY_TIMEOUT_SECONDS)
        )
        if "ssdp" in selected
        else None
    )

    if onvif_task:
        discovery_state.onvif_results = await onvif_task
    if mdns_task:
        discovery_state.mdns_results = await mdns_task
    if ssdp_task:
        discovery_state.ssdp_results = await ssdp_task

    discovery_state.last_updated = datetime.now(timezone.utc).isoformat()
    return discovery_state.snapshot()


async def enrich_and_classify_host(
    ip_address: str,
    host_base: dict[str, Any],
    onvif_by_ip: dict[str, dict[str, Any]],
    mdns_by_ip: dict[str, dict[str, Any]],
    ssdp_by_ip: dict[str, dict[str, Any]],
    scan_ports: bool = True,
) -> dict[str, Any]:
    """Perform port scan, ONVIF check, service banner inspection, and evidence classification for one host."""
    open_ports = list(host_base.get("quick_open_ports", []))
    if scan_ports:
        port_res = await scan_device_ports(ip_address)
        open_ports = sorted(set(open_ports + port_res.get("open_ports", [])))

    onvif_info = onvif_by_ip.get(ip_address)
    if not onvif_info and (8899 in open_ports or 80 in open_ports or 8000 in open_ports):
        # Check if device responds to ONVIF SOAP on port 8899 or 80
        probe_port = 8899 if 8899 in open_ports else 80
        probed_onvif = await interrogate_onvif_device(ip_address, port=probe_port)
        if probed_onvif.get("reachable"):
            onvif_info = probed_onvif

    mdns_info = mdns_by_ip.get(ip_address)
    ssdp_info = ssdp_by_ip.get(ip_address)

    fingerprint = await build_device_fingerprint(
        ip_address=ip_address,
        mac_address=host_base.get("mac_address"),
        open_ports=open_ports,
        onvif_info=onvif_info,
        mdns_info=mdns_info,
        ssdp_info=ssdp_info,
        is_gateway=bool(host_base.get("is_gateway", False)),
        is_host=bool(host_base.get("is_host", False)),
    )
    classification = classify_device_from_evidence(fingerprint)

    methods = list(host_base.get("discovery_methods", []))
    if onvif_info:
        methods.append("ONVIF")
    if mdns_info:
        methods.append("mDNS")
    if ssdp_info:
        methods.append("SSDP")

    camera_attrs = extract_camera_candidate_attributes(ip_address, classification, fingerprint)
    nvr_attrs = extract_nvr_candidate_attributes(ip_address, classification, fingerprint)

    return {
        "ip_address": ip_address,
        "mac_address": fingerprint.get("mac_address"),
        "hostname": fingerprint.get("hostname"),
        "manufacturer": classification.get("manufacturer"),
        "model": classification.get("model"),
        "category": classification["category"],
        "confidence": classification["confidence"],
        "classification_evidence": classification["evidence"],
        "open_ports": open_ports,
        "service_banners": fingerprint.get("banners", {}),
        "detected_protocols": classification.get("detected_protocols", []),
        "discovery_methods": sorted(set(methods)),
        "onvif_available": classification.get("onvif_available", False),
        "rtsp_available": classification.get("rtsp_available", False),
        "latency_ms": host_base.get("latency_ms"),
        "is_online": True,
        "fingerprint": fingerprint,
        "camera_attributes": camera_attrs,
        "nvr_attributes": nvr_attrs,
    }

