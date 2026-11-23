"""Operating system permission and packet capture capability checks."""

from __future__ import annotations

import os
import platform
import shutil
import socket
from typing import Any


def check_admin_privileges() -> bool:
    """Return True if the current Python process has elevated/root privileges."""
    system = platform.system().lower()
    if system == "windows":
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    else:
        try:
            return os.geteuid() == 0  # type: ignore[attr-defined]
        except AttributeError:
            return False


def check_raw_socket_permission() -> bool:
    """Check if raw ICMP sockets can be opened by the current user."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        sock.close()
        return True
    except PermissionError:
        return False
    except OSError:
        return False


def check_external_binaries() -> dict[str, Any]:
    """Detect availability of optional helper binaries (ffmpeg, nmap, ping, arp)."""
    ffmpeg_path = shutil.which("ffmpeg")
    nmap_path = shutil.which("nmap")
    ping_path = shutil.which("ping")
    arp_path = shutil.which("arp")

    npcap_installed = False
    if platform.system().lower() == "windows":
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        npcap_dir = os.path.join(system_root, "System32", "Npcap")
        npcap_installed = os.path.isdir(npcap_dir)

    return {
        "ffmpeg_available": ffmpeg_path is not None,
        "ffmpeg_path": ffmpeg_path,
        "nmap_available": nmap_path is not None,
        "nmap_path": nmap_path,
        "ping_available": ping_path is not None,
        "arp_available": arp_path is not None,
        "npcap_installed": npcap_installed,
    }


def get_permission_summary() -> dict[str, Any]:
    """Build a complete summary of host permissions and network discovery capabilities."""
    system = platform.system()
    is_admin = check_admin_privileges()
    raw_socket = check_raw_socket_permission()
    binaries = check_external_binaries()

    guidance: list[str] = []
    if system == "Windows":
        if not is_admin:
            guidance.append(
                "Running as standard Windows user. Standard ARP table inspection, TCP probing, "
                "ONVIF WS-Discovery, mDNS, and SSDP work normally. For raw Scapy Layer-2 ARP "
                "packet injection, run PowerShell as Administrator with Npcap installed."
            )
        if not binaries["npcap_installed"]:
            guidance.append(
                "Npcap was not detected in System32\\Npcap. The scanner will automatically use "
                "OS ARP table resolution, ICMP ping, and asynchronous TCP/UDP discovery."
            )
    elif system == "Darwin":
        if not is_admin:
            guidance.append(
                "Running on macOS without root privileges. Raw BPF (/dev/bpf*) packet capture "
                "requires sudo; fallback ARP cache, ICMP, ONVIF, mDNS, and SSDP are active."
            )

    return {
        "os_name": system,
        "os_release": platform.release(),
        "is_admin": is_admin,
        "raw_socket_permitted": raw_socket,
        **binaries,
        "guidance": guidance,
    }

