"""Application-wide constants and enumerations."""

from enum import Enum


class DeviceCategory(str, Enum):
    CAMERA = "CAMERA"
    ONVIF_CAMERA = "ONVIF_CAMERA"
    NVR = "NVR"
    DVR = "DVR"
    ROUTER = "ROUTER"
    PRINTER = "PRINTER"
    COMPUTER = "COMPUTER"
    NAS = "NAS"
    NETWORK_DEVICE = "NETWORK_DEVICE"
    UNKNOWN = "UNKNOWN"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class ScanStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class RecoveryStatus(str, Enum):
    INITIATED = "INITIATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REQUIRES_SUPPORT = "REQUIRES_SUPPORT"
    FAILED = "FAILED"


DEFAULT_COMMON_PORTS: list[int] = [
    80,
    443,
    554,
    3702,
    5000,
    8000,
    8080,
    8443,
    8554,
    8899,
    9000,
    34567,
    37777,
    53,
    445,
    631,
    9100,
]

CCTV_SPECIFIC_PORTS: set[int] = {554, 3702, 8000, 8554, 8899, 9000, 34567, 37777}
WEB_ADMIN_PORTS: set[int] = {80, 443, 8000, 8080, 8443, 8899}
PRINTER_PORTS: set[int] = {631, 9100}

ONVIF_MULTICAST_IP = "239.255.255.250"
ONVIF_MULTICAST_PORT = 3702

SSDP_MULTICAST_IP = "239.255.255.250"
SSDP_MULTICAST_PORT = 1900

API_V1_PREFIX = "/api/v1"

