# Multi-stage Dockerfile for CCTV Network Discovery & Recovery Assistant
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    iputils-ping \
    net-tools \
    nmap \
    libpcap0.8 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

RUN mkdir -p data/database data/logs data/exports data/backups

ENV PYTHONPATH=/app:/app/backend
ENV HOST=0.0.0.0
ENV PORT=8000
ENV ALLOW_LAN_ACCESS=true

EXPOSE 8000

CMD ["python", "scripts/start_backend.py"]

