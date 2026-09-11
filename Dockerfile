FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src/ /app/src/

RUN pip install --no-cache-dir .

ENTRYPOINT ["releasecraft"]
CMD ["--help"]
