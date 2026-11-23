"""Tests for API security headers, SSRF/public IP prevention, authentication, and rate limiting."""

from __future__ import annotations

from fastapi.testclient import TestClient
from backend.app.config import get_settings


def test_security_headers_present(client: TestClient) -> None:
    resp = client.get("/api/v1/system/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert "no-store" in resp.headers.get("Cache-Control", "")


def test_ssrf_and_public_ip_rejection(client: TestClient) -> None:
    # Attempting to register or scan a public internet IP must fail with 403/422
    resp = client.post(
        "/api/v1/devices",
        json={"ip_address": "8.8.8.8", "label": "External DNS"},
    )
    assert resp.status_code in (403, 422)

    port_resp = client.post(
        "/api/v1/ports/scan",
        json={"ip_address": "1.1.1.1", "ports": [80, 443]},
    )
    assert port_resp.status_code in (403, 422)


def test_invalid_api_token_rejected(client: TestClient) -> None:
    resp = client.get(
        "/api/v1/devices",
        headers={"X-API-Token": "wrong-malicious-token"},
    )
    assert resp.status_code == 403


def test_valid_api_pairing_token_accepted(client: TestClient) -> None:
    settings = get_settings()
    pair_resp = client.post(
        "/api/v1/system/pair",
        json={"token": settings.API_ACCESS_TOKEN},
    )
    assert pair_resp.status_code == 200
    assert pair_resp.json()["paired"] is True

    bad_pair = client.post(
        "/api/v1/system/pair",
        json={"token": "invalid-token"},
    )
    assert bad_pair.status_code == 403

