#!/usr/bin/env bash
# ============================================================================
# macOS Production Build Script — CCTV Network Discovery & Recovery Assistant
# ============================================================================
set -euo pipefail

echo "=== Building CCTV Network Discovery & Recovery Assistant (macOS) ==="
(cd frontend && npm run build)

echo "=== Running Backend Test Suite ==="
if [ -x "./.venv/bin/pytest" ]; then
    ./.venv/bin/pytest -q
else
    pytest -q
fi

echo "[OK] Production build and verification succeeded! Static assets output to frontend/dist"

