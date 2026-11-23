"""Operating system, CPU, memory, and Python runtime information."""

from __future__ import annotations

import platform
import sys
import time
from typing import Any
import psutil

_PROCESS_START_TIME = time.time()


def get_platform_information() -> dict[str, Any]:
    """Return host operating system, hardware usage, and runtime metadata."""
    vm = psutil.virtual_memory()
    uptime_sec = round(time.time() - _PROCESS_START_TIME, 1)
    return {
        "os_system": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "hostname": platform.node(),
        "python_version": sys.version.split()[0],
        "cpu_cores": psutil.cpu_count(logical=True) or 1,
        "memory_total_mb": round(vm.total / (1024 * 1024), 1),
        "memory_used_percent": vm.percent,
        "uptime_seconds": uptime_sec,
    }

