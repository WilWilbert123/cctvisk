"""Active local network interface and Wi-Fi/Ethernet adapter detection using psutil and OS tools."""

from __future__ import annotations

import platform
import re
import socket
import subprocess
from typing import Any
import psutil
from backend.utils.ip_utils import is_authorized_private_ip, netmask_to_cidr
from backend.utils.mac_utils import normalize_mac


def _get_default_route_ip() -> str | None:
    """Determine the preferred outbound local IPv4 address via UDP socket routing table lookup."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Does not send any packets; only inspects the OS routing table
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
            if is_authorized_private_ip(ip):
                return ip
    except OSError:
        pass
    return None


def _detect_default_gateway() -> str | None:
    """Detect the default IPv4 gateway on Windows, macOS, or Linux."""
    system = platform.system().lower()
    try:
        if system == "windows":
            out = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            ).stdout
            matches = re.findall(r"Default Gateway[ .\s]*:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", out)
            for gw in matches:
                if is_authorized_private_ip(gw):
                    return gw
        elif system == "darwin":
            out = subprocess.run(
                ["route", "-n", "get", "default"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            ).stdout
            m = re.search(r"gateway:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", out)
            if m and is_authorized_private_ip(m.group(1)):
                return m.group(1)
        else:
            out = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            ).stdout
            m = re.search(r"default via ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", out)
            if m and is_authorized_private_ip(m.group(1)):
                return m.group(1)
    except Exception:
        pass
    return None


def _detect_wifi_ssid() -> str | None:
    """Attempt to read the connected Wi-Fi SSID on Windows or macOS."""
    system = platform.system().lower()
    try:
        if system == "windows":
            out = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            ).stdout
            for line in out.splitlines():
                if "SSID" in line and "BSSID" not in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2 and parts[1].strip():
                        return parts[1].strip()
        elif system == "darwin":
            out = subprocess.run(
                ["networksetup", "-getairportnetwork", "en0"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            ).stdout
            if "Current Wi-Fi Network:" in out:
                return out.split("Current Wi-Fi Network:", 1)[1].strip()
    except Exception:
        pass
    return None


def list_network_interfaces() -> list[dict[str, Any]]:
    """Return all active local IPv4 private network interfaces on the host."""
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    default_ip = _get_default_route_ip()
    gateway = _detect_default_gateway()
    ssid = _detect_wifi_ssid()

    interfaces: list[dict[str, Any]] = []
    for iface_name, snic_list in addrs.items():
        iface_stat = stats.get(iface_name)
        is_up = bool(iface_stat.isup) if iface_stat else True
        if not is_up:
            continue

        lower_name = iface_name.lower()
        if any(
            skip in lower_name
            for skip in ("loopback", "vethernet", "wsl", "docker", "vmware", "virtualbox", "utun")
        ):
            continue

        ipv4_addr: str | None = None
        netmask: str | None = None
        mac_addr: str | None = None

        for snic in snic_list:
            if snic.family == socket.AF_INET and is_authorized_private_ip(snic.address):
                ipv4_addr = snic.address
                netmask = snic.netmask or "255.255.255.0"
            elif snic.family in ( getattr(psutil, "AF_LINK", -1), getattr(socket, "AF_LINK", -1) ):
                mac_addr = normalize_mac(snic.address)

        if not ipv4_addr or not netmask:
            continue

        conn_type = "Wi-Fi" if any(w in lower_name for w in ("wi-fi", "wifi", "wlan", "en0", "wireless")) else "Ethernet"
        subnet_cidr = netmask_to_cidr(ipv4_addr, netmask)

        interfaces.append(
            {
                "interface_name": iface_name,
                "ip_address": ipv4_addr,
                "netmask": netmask,
                "subnet_cidr": subnet_cidr,
                "gateway": gateway if ipv4_addr == default_ip or len(interfaces) == 0 else None,
                "mac_address": mac_addr,
                "is_up": is_up,
                "is_primary": ipv4_addr == default_ip,
                "connection_type": conn_type,
                "ssid": ssid if conn_type == "Wi-Fi" else None,
                "speed_mbps": iface_stat.speed if iface_stat and iface_stat.speed > 0 else None,
            }
        )

    # Sort so primary default-route interface appears first
    interfaces.sort(key=lambda x: (not x.get("is_primary", False), x["interface_name"]))
    return interfaces


def get_active_interface(preferred_name: str | None = None) -> dict[str, Any]:
    """Return the primary active network interface or a safe disconnected state if offline."""
    interfaces = list_network_interfaces()
    if preferred_name:
        for iface in interfaces:
            if iface["interface_name"].lower() == preferred_name.lower():
                return iface

    if interfaces:
        return interfaces[0]

    # Fallback when no Wi-Fi/Ethernet interface is currently connected
    return {
        "interface_name": "Disconnected",
        "ip_address": "127.0.0.1",
        "netmask": "255.255.255.0",
        "subnet_cidr": "192.168.1.0/24",
        "gateway": None,
        "mac_address": None,
        "is_up": False,
        "is_primary": False,
        "connection_type": "Disconnected",
        "ssid": None,
        "speed_mbps": None,
    }

