"""Asynchronous network scan worker orchestrating subnet discovery, ONVIF/mDNS/SSDP, port checks, and DB persistence."""

from __future__ import annotations

import asyncio
from typing import Any
from backend.core.constants import ScanStatus
from backend.core.events import event_manager
from backend.core.exceptions import ScanInProgressError
from backend.core.logging import get_logger
from backend.database.session import session_scope
from backend.repositories.camera_repository import CameraRepository
from backend.repositories.device_repository import DeviceRepository
from backend.repositories.nvr_repository import NVRRepository
from backend.repositories.scan_repository import ScanRepository
from backend.services.discovery.device_discovery import (
    discovery_state,
    enrich_and_classify_host,
    run_targeted_discovery_probes,
)
from backend.services.network.interface import get_active_interface
from backend.services.network.scanner import LocalNetworkScanner
from backend.utils.ip_utils import validate_authorized_subnet

logger = get_logger("scan_worker")


class ScanWorkerManager:
    """Singleton manager for running and tracking local network discovery scans."""

    def __init__(self) -> None:
        self._scanner = LocalNetworkScanner()
        self._active_task: asyncio.Task[None] | None = None
        self.current_scan_id: int | None = None
        self.is_running: bool = False
        self.progress: float = 0.0
        self.stage: str = "Idle"
        self.message: str = "Ready to scan"
        self.devices_found: int = 0
        self.cameras_found: int = 0
        self.nvrs_found: int = 0

    def start_scan(
        self,
        subnet_cidr: str | None = None,
        interface_name: str | None = None,
        scan_ports: bool = True,
        enable_onvif: bool = True,
        enable_mdns: bool = True,
        enable_ssdp: bool = True,
    ) -> dict[str, Any]:
        if self.is_running and self._active_task and not self._active_task.done():
            raise ScanInProgressError()

        active_iface = get_active_interface(interface_name)
        target_cidr = str(validate_authorized_subnet(subnet_cidr or active_iface["subnet_cidr"]))

        methods_used = ["ARP", "TCP", "ICMP"]
        if enable_onvif:
            methods_used.append("ONVIF")
        if enable_mdns:
            methods_used.append("mDNS")
        if enable_ssdp:
            methods_used.append("SSDP")

        with session_scope() as session:
            scan_repo = ScanRepository(session)
            scan_row = scan_repo.create_scan(
                subnet_cidr=target_cidr,
                interface_name=active_iface["interface_name"],
                local_ip=active_iface.get("ip_address"),
                methods_used=methods_used,
            )
            scan_id = scan_row.id
            scan_dict = {
                "id": scan_row.id,
                "subnet_cidr": scan_row.subnet_cidr,
                "interface_name": scan_row.interface_name,
                "local_ip": scan_row.local_ip,
                "status": scan_row.status,
                "progress": scan_row.progress,
                "current_stage": scan_row.current_stage,
                "total_hosts_probed": scan_row.total_hosts_probed,
                "devices_discovered": scan_row.devices_discovered,
                "cameras_discovered": scan_row.cameras_discovered,
                "nvrs_discovered": scan_row.nvrs_discovered,
                "methods_used": scan_row.methods_used,
                "scan_summary": scan_row.scan_summary,
                "error_message": scan_row.error_message,
                "started_at": scan_row.started_at,
                "completed_at": scan_row.completed_at,
                "duration_seconds": scan_row.duration_seconds,
            }

        self.current_scan_id = scan_id
        self.is_running = True
        self.progress = 2.0
        self.stage = "Initializing network scan"
        self.message = f"Scanning authorized subnet {target_cidr}"
        self.devices_found = 0
        self.cameras_found = 0
        self.nvrs_found = 0

        loop = asyncio.get_running_loop()
        self._active_task = loop.create_task(
            self._execute_scan_pipeline(
                scan_id=scan_id,
                subnet_cidr=target_cidr,
                interface_name=active_iface["interface_name"],
                scan_ports=scan_ports,
                enable_onvif=enable_onvif,
                enable_mdns=enable_mdns,
                enable_ssdp=enable_ssdp,
            )
        )
        return scan_dict

    def cancel_scan(self) -> dict[str, Any]:
        if not self.is_running:
            return {"cancelled": False, "message": "No scan is currently running."}
        self._scanner.request_cancel()
        self.stage = "Cancelling scan..."
        self.message = "Cancellation requested by user"
        return {"cancelled": True, "scan_id": self.current_scan_id, "message": "Scan cancellation requested."}

    async def _broadcast_progress(self, scan_id: int, pct: float, stage: str, devices_cnt: int) -> None:
        self.progress = round(min(100.0, max(0.0, pct)), 1)
        self.stage = stage
        self.message = stage
        self.devices_found = devices_cnt
        with session_scope() as session:
            ScanRepository(session).update_scan_progress(
                scan_id=scan_id,
                progress=self.progress,
                stage=stage,
                devices_discovered=self.devices_found,
                cameras_discovered=self.cameras_found,
                nvrs_discovered=self.nvrs_found,
            )
        await event_manager.broadcast(
            "scan_progress",
            {
                "scan_id": scan_id,
                "status": ScanStatus.RUNNING.value,
                "progress": self.progress,
                "stage": self.stage,
                "message": self.message,
                "devices_found": self.devices_found,
                "cameras_found": self.cameras_found,
                "nvrs_found": self.nvrs_found,
            },
        )

    async def _execute_scan_pipeline(
        self,
        scan_id: int,
        subnet_cidr: str,
        interface_name: str,
        scan_ports: bool,
        enable_onvif: bool,
        enable_mdns: bool,
        enable_ssdp: bool,
    ) -> None:
        try:
            # Phase 1: Run multicast discovery (ONVIF, mDNS, SSDP) concurrently with ARP/TCP/ICMP subnet sweep
            discovery_methods: list[str] = []
            if enable_onvif:
                discovery_methods.append("onvif")
            if enable_mdns:
                discovery_methods.append("mdns")
            if enable_ssdp:
                discovery_methods.append("ssdp")

            multicast_task = (
                asyncio.create_task(run_targeted_discovery_probes(methods=discovery_methods))
                if discovery_methods
                else None
            )

            async def _on_subnet_progress(pct: float, msg: str, count: int) -> None:
                await self._broadcast_progress(scan_id, pct, msg, count)

            subnet_result = await self._scanner.scan_subnet(
                subnet_cidr=subnet_cidr,
                interface_name=interface_name,
                progress_cb=_on_subnet_progress,
            )

            if self._scanner.is_cancelled:
                if multicast_task and not multicast_task.done():
                    multicast_task.cancel()
                with session_scope() as session:
                    ScanRepository(session).finalize_scan(scan_id, ScanStatus.CANCELLED)
                self.is_running = False
                await event_manager.broadcast(
                    "scan_progress",
                    {
                        "scan_id": scan_id,
                        "status": ScanStatus.CANCELLED.value,
                        "progress": self.progress,
                        "stage": "Scan cancelled",
                        "message": "Network scan was cancelled by the user.",
                        "devices_found": self.devices_found,
                        "cameras_found": self.cameras_found,
                    },
                )
                return

            multicast_data = await multicast_task if multicast_task else {"onvif": [], "mdns": [], "ssdp": []}
            onvif_by_ip = {item["ip_address"]: item for item in multicast_data.get("onvif", [])}
            mdns_by_ip = {item["ip_address"]: item for item in multicast_data.get("mdns", [])}
            ssdp_by_ip = {item["ip_address"]: item for item in multicast_data.get("ssdp", [])}

            hosts_map: dict[str, dict[str, Any]] = dict(subnet_result.get("hosts", {}))
            # Merge any hosts found only via ONVIF/mDNS/SSDP on the same subnet
            import ipaddress
            net_obj = validate_authorized_subnet(subnet_cidr)
            for extra_ip in set(onvif_by_ip.keys()) | set(mdns_by_ip.keys()) | set(ssdp_by_ip.keys()):
                try:
                    if ipaddress.ip_address(extra_ip) in net_obj and extra_ip not in hosts_map:
                        hosts_map[extra_ip] = {
                            "ip_address": extra_ip,
                            "mac_address": None,
                            "latency_ms": 2.0,
                            "quick_open_ports": [],
                            "discovery_methods": [],
                        }
                except ValueError:
                    pass

            total_alive = len(hosts_map)
            await self._broadcast_progress(
                scan_id, 55.0, f"Fingerprinting and classifying {total_alive} active devices", total_alive
            )

            # Mark any previously discovered devices on this subnet that did not respond in this scan as offline
            with session_scope() as session:
                dev_repo = DeviceRepository(session)
                for existing_dev in dev_repo.get_all():
                    try:
                        if (
                            ipaddress.ip_address(existing_dev.ip_address) in net_obj
                            and existing_dev.ip_address not in hosts_map
                        ):
                            existing_dev.is_online = False
                            session.commit()
                    except ValueError:
                        pass

            fingerprints_collected: list[dict[str, Any]] = []
            processed = 0
            for ip_addr, host_base in sorted(hosts_map.items()):
                if self._scanner.is_cancelled:
                    break
                enriched = await enrich_and_classify_host(
                    ip_address=ip_addr,
                    host_base=host_base,
                    onvif_by_ip=onvif_by_ip,
                    mdns_by_ip=mdns_by_ip,
                    ssdp_by_ip=ssdp_by_ip,
                    scan_ports=scan_ports,
                )
                fingerprints_collected.append(enriched["fingerprint"])

                with session_scope() as session:
                    dev_repo = DeviceRepository(session)
                    cam_repo = CameraRepository(session)
                    nvr_repo = NVRRepository(session)
                    scan_repo = ScanRepository(session)

                    dev = dev_repo.upsert_discovered_device(enriched)
                    if enriched.get("camera_attributes"):
                        cam_repo.upsert_camera(dev.id, ip_addr, enriched["camera_attributes"])
                        self.cameras_found += 1
                    if enriched.get("nvr_attributes"):
                        nvr_repo.upsert_nvr(dev.id, ip_addr, enriched["nvr_attributes"])
                        self.nvrs_found += 1

                    scan_repo.add_scan_history_entry(
                        scan_id=scan_id,
                        device_id=dev.id,
                        ip_address=dev.ip_address,
                        mac_address=dev.mac_address,
                        manufacturer=dev.manufacturer,
                        category=dev.category,
                        confidence=dev.confidence,
                        open_ports=dev.open_ports,
                        discovery_evidence={"evidence": dev.classification_evidence},
                    )
                    dev_payload = {
                        "id": dev.id,
                        "ip_address": dev.ip_address,
                        "mac_address": dev.mac_address,
                        "manufacturer": dev.manufacturer,
                        "model": dev.model,
                        "hostname": dev.hostname,
                        "category": dev.category,
                        "confidence": dev.confidence,
                        "open_ports": dev.open_ports,
                        "onvif_available": dev.onvif_available,
                        "rtsp_available": dev.rtsp_available,
                        "is_online": dev.is_online,
                    }

                await event_manager.broadcast("device_discovered", dev_payload)
                processed += 1
                pct = 55.0 + (processed / max(1, total_alive)) * 42.0
                await self._broadcast_progress(
                    scan_id,
                    pct,
                    f"Classified {ip_addr} ({enriched['category']}) [{processed}/{total_alive}]",
                    total_alive,
                )

            discovery_state.fingerprints = fingerprints_collected

            if self._scanner.is_cancelled:
                with session_scope() as session:
                    ScanRepository(session).finalize_scan(scan_id, ScanStatus.CANCELLED)
                self.is_running = False
                return

            summary = {
                "subnet_cidr": subnet_cidr,
                "interface_name": interface_name,
                "total_hosts_probed": subnet_result.get("total_hosts_probed", 0),
                "devices_discovered": total_alive,
                "cameras_discovered": self.cameras_found,
                "nvrs_discovered": self.nvrs_found,
            }
            with session_scope() as session:
                scan_repo = ScanRepository(session)
                scan_repo.update_scan_progress(
                    scan_id=scan_id,
                    progress=100.0,
                    stage="Scan completed",
                    devices_discovered=total_alive,
                    cameras_discovered=self.cameras_found,
                    nvrs_discovered=self.nvrs_found,
                    total_hosts_probed=subnet_result.get("total_hosts_probed", 0),
                )
                scan_repo.finalize_scan(scan_id, ScanStatus.COMPLETED, summary=summary)
                scan_repo.log_activity(
                    event_type="network_scan_completed",
                    title="Network Scan Completed",
                    message=(
                        f"Discovered {total_alive} devices ({self.cameras_found} cameras, "
                        f"{self.nvrs_found} NVR/DVRs) on {subnet_cidr}."
                    ),
                    level="success",
                    metadata_json=summary,
                )

            self.progress = 100.0
            self.stage = "Scan completed"
            self.message = f"Completed scan of {subnet_cidr}: {total_alive} devices found."
            self.is_running = False

            await event_manager.broadcast(
                "scan_progress",
                {
                    "scan_id": scan_id,
                    "status": ScanStatus.COMPLETED.value,
                    "progress": 100.0,
                    "stage": "Scan completed",
                    "message": self.message,
                    "devices_found": total_alive,
                    "cameras_found": self.cameras_found,
                    "nvrs_found": self.nvrs_found,
                },
            )
        except Exception as exc:
            logger.error("Network scan pipeline failed: %s", exc)
            self.is_running = False
            self.stage = "Scan failed"
            self.message = str(exc)
            with session_scope() as session:
                ScanRepository(session).finalize_scan(
                    scan_id, ScanStatus.FAILED, error_message=str(exc)
                )
            await event_manager.broadcast(
                "scan_progress",
                {
                    "scan_id": scan_id,
                    "status": ScanStatus.FAILED.value,
                    "progress": self.progress,
                    "stage": "Scan failed",
                    "message": str(exc),
                    "devices_found": self.devices_found,
                    "cameras_found": self.cameras_found,
                },
            )


scan_worker_manager = ScanWorkerManager()

