"""ARP discovery using both Scapy (when Npcap/BPF permissions allow) and OS ARP table resolution."""

from __future__ import annotations

import platform
import re
import subprocess
from backend.core.logging import get_logger
from backend.core.permissions import check_admin_privileges, check_external_binaries
from backend.utils.ip_utils import is_authorized_private_ip, validate_authorized_subnet
from backend.utils.mac_utils import normalize_mac

logger = get_logger("arp")


def read_os_arp_table() -> dict[str, str]:
    """
    Read the operating system's ARP cache (`arp -a`) and return a mapping of {ip_address: mac_address}.
    Works without elevated privileges on Windows, macOS, and Linux.
    """
    ip_to_mac: dict[str, str] = {}
    try:
        proc = subprocess.run(
            ["arp", "-a"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        output = proc.stdout or ""
    except Exception as exc:
        logger.debug("OS arp -a execution failed: %s", exc)
        return ip_to_mac

    # Matches Windows (`192.168.1.10   00-11-22-33-44-55   dynamic`)
    # and macOS/Linux (`? (192.168.1.10) at 0:11:22:33:44:55 on en0`)
    pattern = re.compile(
        r"\(?(\d{1,3}(?:\.\d{1,3}){3})\)?\s+(?:at\s+)?([0-9A-Fa-f]{1,2}(?:[:-][0-9A-Fa-f]{1,2}){5})"
    )
    for match in pattern.finditer(output):
        ip_str, raw_mac = match.group(1), match.group(2)
        if not is_authorized_private_ip(ip_str):
            continue
        mac = normalize_mac(raw_mac)
        if mac:
            ip_to_mac[ip_str] = mac

    return ip_to_mac


def scapy_arp_scan(subnet_cidr: str, timeout: float = 1.5) -> dict[str, str]:
    """
    Perform an active Layer-2 Ethernet ARP broadcast scan via Scapy if the OS has
    root/Administrator permissions and packet capture driver support.
    Falls back cleanly to {} if unavailable.
    """
    validate_authorized_subnet(subnet_cidr)
    if not check_admin_privileges():
        return {}

    if platform.system().lower() == "windows":
        binaries = check_external_binaries()
        if not binaries.get("npcap_installed"):
            return {}

    try:
        from scapy.layers.l2 import ARP, Ether
        from scapy.sendrecv import srp

        packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet_cidr)
        answered, _ = srp(packet, timeout=timeout, verbose=0)
        results: dict[str, str] = {}
        for _sent, received in answered:
            ip_str = getattr(received, "psrc", None)
            hw_src = getattr(received, "hwsrc", None)
            if ip_str and is_authorized_private_ip(ip_str):
                mac = normalize_mac(hw_src)
                if mac:
                    results[ip_str] = mac
        return results
    except Exception as exc:
        logger.debug("Scapy Layer-2 ARP scan unavailable (%s); using OS ARP table.", exc)
        return {}


def discover_arp_neighbors(subnet_cidr: str) -> dict[str, str]:
    """Combine active Scapy ARP scan (if available) with OS ARP cache inspection."""
    network = validate_authorized_subnet(subnet_cidr)
    combined: dict[str, str] = {}

    scapy_results = scapy_arp_scan(str(network))
    combined.update(scapy_results)

    os_arp = read_os_arp_table()
    for ip_str, mac in os_arp.items():
        try:
            import ipaddress
            if ipaddress.ip_address(ip_str) in network:
                combined.setdefault(ip_str, mac)
        except ValueError:
            continue

    return combined

