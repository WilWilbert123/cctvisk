#!/usr/bin/env python3
"""Startup entrypoint for the CCTV Network Discovery & Recovery Assistant backend."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure project root and backend directory are on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    import uvicorn
except ModuleNotFoundError:
    venv_python = (
        ROOT_DIR / ".venv" / "Scripts" / "python.exe"
        if sys.platform == "win32"
        else ROOT_DIR / ".venv" / "bin" / "python"
    )
    if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
        import subprocess

        sys.exit(subprocess.call([str(venv_python), __file__, *sys.argv[1:]]))
    raise

from backend.app.config import get_settings


def main() -> None:
    os.chdir(ROOT_DIR)
    settings = get_settings()

    host = settings.HOST
    if host == "0.0.0.0" and not settings.ALLOW_LAN_ACCESS:
        print(
            "[SECURITY NOTICE] HOST=0.0.0.0 requested without ALLOW_LAN_ACCESS=true. "
            "Binding to 127.0.0.1 for safety. Set ALLOW_LAN_ACCESS=true to enable LAN access."
        )
        host = "127.0.0.1"

    print(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION} on http://{host}:{settings.PORT}"
    )
    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=settings.PORT,
        reload=bool(settings.DEBUG or settings.APP_ENV == "development"),
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()

