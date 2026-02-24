# Forge API Server
# Builds the Forge runtime and starts the API server on port 8626.

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY forge/ forge/
COPY pyproject.toml .
COPY README.md .
RUN pip install --no-cache-dir -e .

RUN mkdir -p forge_workspace .forge

EXPOSE 8626

CMD ["forge", "server", "--port", "8626"]
