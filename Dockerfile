# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install deps into a separate prefix so we can copy them cleanly
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app.py bot.py models.py import_csv.py ./
COPY templates/ templates/
COPY static/ static/
COPY my_food_reels.csv .

# Startup script — strip Windows CRLF line endings before chmod
COPY start.sh .
RUN sed -i 's/\r//' start.sh && chmod +x start.sh

# Data directory — mount a Railway volume here for persistent SQLite
RUN mkdir -p /data

EXPOSE 8000

CMD ["./start.sh"]
