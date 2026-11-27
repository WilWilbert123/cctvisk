#!/usr/bin/env bash
# ============================================================================
# macOS Setup Script — CCTV Network Discovery & Recovery Assistant
# Run from Terminal in project root: chmod +x scripts/*.sh && ./scripts/setup_macos.sh
# ============================================================================
set -euo pipefail

echo "=== Setting up CCTV Network Discovery & Recovery Assistant (macOS) ==="

mkdir -p data/database data/logs data/exports data/backups

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[OK] Created .env from .env.example"
fi

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
fi

echo "Installing Python dependencies..."
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/pip install -r requirements-dev.txt

echo "Installing Frontend dependencies..."
(cd frontend && npm install)

echo "=== Setup Complete! ==="
echo "Start backend:  ./.venv/bin/python scripts/start_backend.py"
echo "Start frontend: ./scripts/start_frontend.sh"
echo "Note: For raw ARP packet capture via Scapy on macOS (/dev/bpf*), run the backend with sudo or grant BPF read permissions."

