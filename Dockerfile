# ---- FastAPI backend image (deployable to Render, Railway, Fly.io, etc.) ----
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ ./server/

ENV PORT=8000
EXPOSE 8000

CMD uvicorn server.main:app --host 0.0.0.0 --port ${PORT}
