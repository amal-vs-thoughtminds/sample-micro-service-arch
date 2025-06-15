FROM python:3.11-slim

WORKDIR /app

# Use a different mirror and add retry logic for apt-get
RUN echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80-retries && \
    echo 'Acquire::http::Timeout "120";' >> /etc/apt/apt.conf.d/80-retries && \
    echo 'Acquire::https::Timeout "120";' >> /etc/apt/apt.conf.d/80-retries && \
    sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
    apt-get clean && \
    apt-get update --allow-releaseinfo-change || \
    (sleep 2 && apt-get update --allow-releaseinfo-change) || \
    (sleep 5 && apt-get update --allow-releaseinfo-change)

# Install system dependencies with retry logic
RUN apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# Copy shared library first
COPY shared/setup.py ./shared/setup.py
COPY shared/README.md ./shared/README.md
COPY shared/ms_communicator ./shared/ms_communicator

# Install shared library first
RUN pip install --no-cache-dir -e ./shared[dev]

# Copy and install service requirements
COPY user/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY user/app ./app
COPY user/alembic ./alembic
COPY user/alembic.ini .

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 