# ---- Builder stage ----
FROM python:3.10-slim AS builder

WORKDIR /build

RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt constraints-ci.txt ./
RUN pip install --no-cache-dir --prefix=/install \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    --constraint constraints-ci.txt \
    setuptools==82.0.1 \
    wheel==0.47.0 \
    -r requirements.txt

# ---- Runtime stage ----
FROM python:3.10-slim

WORKDIR /app

RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip uninstall --yes setuptools wheel

COPY --from=builder /install /usr/local

COPY . .

RUN groupadd --system appuser && useradd --system --gid appuser --create-home --home-dir /home/appuser appuser && \
    mkdir -p /app/logs && chown -R appuser:appuser /app /home/appuser

USER appuser

EXPOSE 8088

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8088/health/live || exit 1

CMD ["python", "run.py"]
