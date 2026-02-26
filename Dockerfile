# Stage 1: Builder
FROM python:3.12-alpine AS builder

WORKDIR /build

# Install build dependencies required for psycopg2 and others
RUN apk add --no-cache gcc musl-dev libpq-dev

# Create a virtual environment and install dependencies inside it
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final minimal image
FROM python:3.12-alpine

WORKDIR /app

# Install only the runtime dependencies (psycopg2 needs libpq)
RUN apk add --no-cache libpq

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV FLASK_APP=src.main:create_app

COPY src/ ./src/

EXPOSE 5000

# Run using a non-root user for better security
RUN adduser -D myuser
USER myuser

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]