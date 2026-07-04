# agent-core container image for Forest DinD executor.
# Non-root (uid 1000), entrypoint: python -m agent_core.cli
FROM python:3.11-slim

WORKDIR /app

# Install build deps, copy package, install, then clean up.
COPY pyproject.toml ./
COPY src/ ./src/

RUN pip install --no-cache-dir . \
    && rm -rf /root/.cache

# Create non-root user + outputs directory.
RUN useradd -u 1000 -m agent \
    && mkdir -p /outputs \
    && chown -R 1000:1000 /outputs /app

USER 1000:1000

# Default output path — overridden by executor env passthrough.
ENV AGENT_CORE_OUTPUTS=/outputs

ENTRYPOINT ["python", "-m", "agent_core.cli"]
