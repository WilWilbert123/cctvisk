"""Integration tests for FastAPI /api/v1 endpoints including Live Camera Connection & Snapshot."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_dashboard_and_empty_state(client: TestClient) -> None:
    resp = client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["counts"]["total_devices"] == 0
    assert data["counts"]["cameras_count"] == 0


def test_camera_registration_live_connect_and_snapshot(client: TestClient) -> None:
    # 1. Register a camera
    create_resp = client.post(
        "/api/v1/cameras",
        json={
            "ip_address": "192.168.1.120",
            "label": "Front Entrance Cam",
            "manufacturer": "Hikvision",
            "model": "DS-2CD2043G0-I",
            "rtsp_port": 554,
            "http_port": 80,
            "onvif_port": 80,
            "rtsp_path": "/Streaming/Channels/101",
            "username": "admin",
            "password": "CamPassword2026!",
            "save_credentials": True,
        },
    )
    assert create_resp.status_code == 201
    cam = create_resp.json()
    cam_id = cam["id"]
    assert cam["ip_address"] == "192.168.1.120"
    assert cam["has_saved_credentials"] is True
    assert "CamPassword2026!" not in str(cam)

    # 2. Negotiate Live View connection
    conn_resp = client.post(
        f"/api/v1/cameras/{cam_id}/connect",
        json={"channel": 1, "subtype": 0, "protocol": "auto"},
    )
    assert conn_resp.status_code == 200
    conn_data = conn_resp.json()
    assert conn_data["connected"] is True
    assert f"/api/v1/cameras/{cam_id}/stream.mjpg" in conn_data["stream_url"]
    assert "CamPassword2026!" not in str(conn_data)

    # 3. Fetch live snapshot JPEG
    snap_resp = client.get(f"/api/v1/cameras/{cam_id}/snapshot.jpg")
    assert snap_resp.status_code == 200
    assert snap_resp.headers["content-type"] == "image/jpeg"
    assert snap_resp.content.startswith(b"\xff\xd8")

    # 4. Check stream status & stop stream
    st_resp = client.get(f"/api/v1/cameras/{cam_id}/stream/status")
    assert st_resp.status_code == 200
    stop_resp = client.post(f"/api/v1/cameras/{cam_id}/stream/stop")
    assert stop_resp.status_code == 200


def test_settings_backup_and_system_health(client: TestClient) -> None:
    health = client.get("/api/v1/system/health")
    assert health.status_code == 200
    assert "status" in health.json()

    settings_resp = client.get("/api/v1/settings")
    assert settings_resp.status_code == 200
    assert "settings" in settings_resp.json()

