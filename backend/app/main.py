"""FastAPI application initialization, CORS, security middleware, WebSocket, and SPA static hosting."""

from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.router import api_router
from backend.app.config import ROOT_DIR, get_settings
from backend.app.lifecycle import app_lifespan
from backend.core.events import event_manager
from backend.core.exceptions import register_exception_handlers
from backend.core.security import SecurityHeadersMiddleware


def create_application() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Production-grade local network CCTV camera, ONVIF, and NVR/DVR discovery, "
            "live RTSP/MJPEG streaming, availability monitoring, and authorized recovery assistant."
        ),
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        lifespan=app_lifespan,
    )

    # Register centralized exception handlers
    register_exception_handlers(app)

    # Attach HTTP security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # Configure CORS allowlist (with private LAN & mobile APK origin support)
    origin_regex = r"^(https?|capacitor|file)://.*$"
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_origin_regex=origin_regex,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Serve downloadable Android APK at /download/cctv-assistant.apk
    @app.get("/download/cctv-assistant.apk", include_in_schema=False)
    async def download_android_apk() -> FileResponse:
        apk_path = ROOT_DIR / "cctv-assistant.apk"
        return FileResponse(
            str(apk_path),
            media_type="application/vnd.android.package-archive",
            filename="cctv-assistant.apk",
        )

    # Register /api/v1 routes
    app.include_router(api_router)

    # Top-level WebSocket alias (/ws) in addition to /api/v1/ws
    @app.websocket("/ws")
    async def root_websocket_endpoint(websocket: WebSocket) -> None:
        await event_manager.connect(websocket)
        try:
            while True:
                msg = await websocket.receive_text()
                if msg == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            await event_manager.disconnect(websocket)
        except Exception:
            await event_manager.disconnect(websocket)

    # Serve compiled React frontend (frontend/dist) if built for single-port desktop/Android PWA access
    dist_dir = ROOT_DIR / "frontend" / "dist"
    if dist_dir.exists() and (dist_dir / "index.html").exists():
        assets_dir = dist_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str) -> FileResponse:
            candidate = (dist_dir / full_path).resolve()
            if full_path and candidate.is_file() and str(candidate).startswith(str(dist_dir.resolve())):
                return FileResponse(str(candidate))
            return FileResponse(str(dist_dir / "index.html"))

    return app


app = create_application()
