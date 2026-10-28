FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AUDIT_DATABASE_PATH=/app/data/audit.db \
    MCP_TRANSPORT=streamable-http

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY data ./data

EXPOSE 8000
CMD ["python", "-m", "app.server"]

