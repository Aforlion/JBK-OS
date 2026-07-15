# ============================================================
# JBK-OS — Production Container Image
# Target: Google Cloud Run (europe-west1)
# Base:   Python 3.13 slim (matches CI matrix ceiling)
# ============================================================

FROM python:3.13-slim

# ── Metadata ────────────────────────────────────────────────
LABEL maintainer="devops@jbk.technologies"
LABEL project="JBK-OS"
LABEL version="1.0.0"

# ── System Hardening ────────────────────────────────────────
# Run as non-root user for security
RUN groupadd --gid 1001 jbkos \
 && useradd  --uid 1001 --gid jbkos --no-create-home jbkos

# ── Working Directory ───────────────────────────────────────
WORKDIR /app

# ── Dependencies ────────────────────────────────────────────
# Copy only the manifest first for layer-cache efficiency
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ── Application Source ──────────────────────────────────────
# Copy all application source (respects .dockerignore)
COPY . .

# ── Ownership ───────────────────────────────────────────────
RUN chown -R jbkos:jbkos /app

# ── Runtime User ────────────────────────────────────────────
USER jbkos

# ── Port ────────────────────────────────────────────────────
# Cloud Run injects PORT env variable (default 8080)
EXPOSE 8080

# ── Health Check ────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python scripts/health_check.py || exit 1

# ── Entry Point ─────────────────────────────────────────────
# main.py bootstraps JBK-OS and starts the web server.
# The PORT environment variable is read at runtime.
CMD ["python", "main.py"]
