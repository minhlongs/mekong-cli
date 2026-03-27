# ==============================================================================
# Mekong CLI — Containerized AI Agent Workstation
# Based on HolyClaude patterns (github.com/CoderLuii/HolyClaude)
# Adapted for Mekong CLI PEV pipeline + CTO daemon
#
# Build:
#   docker build -t mekong-dev -f docker/Dockerfile .
#   docker build --build-arg VARIANT=slim -t mekong-dev:slim -f docker/Dockerfile .
# ==============================================================================

FROM node:22-bookworm-slim

LABEL org.opencontainers.image.source=https://github.com/longtho638-jpg/mekong-cli

# ---------- Build args ----------
ARG S6_OVERLAY_VERSION=3.2.0.2
ARG TARGETARCH
ARG VARIANT=full

# ---------- Environment ----------
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    DISPLAY=:99 \
    DBUS_SESSION_BUS_ADDRESS=disabled: \
    CHROMIUM_FLAGS="--no-sandbox --disable-gpu --disable-dev-shm-usage" \
    CHROME_PATH=/usr/bin/chromium \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    MEKONG_HOME=/workspace \
    MEKONG_VERSION=3.2.0

# ---------- s6-overlay v3 ----------
RUN apt-get update && apt-get install -y --no-install-recommends xz-utils curl ca-certificates && rm -rf /var/lib/apt/lists/*
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp/
RUN S6_ARCH=$(case "$TARGETARCH" in arm64) echo "aarch64";; *) echo "x86_64";; esac) && \
    curl -fsSL -o /tmp/s6-overlay-arch.tar.xz \
      "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_ARCH}.tar.xz" && \
    tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz && \
    tar -C / -Jxpf /tmp/s6-overlay-arch.tar.xz && \
    rm /tmp/s6-overlay-*.tar.xz

# ---------- System packages ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl wget jq ripgrep fd-find unzip zip tree tmux fzf bat \
    build-essential pkg-config python3 python3-pip python3-venv \
    chromium fonts-liberation2 fonts-dejavu-core fonts-noto-core fonts-noto-color-emoji \
    locales strace lsof iproute2 procps htop \
    postgresql-client redis-tools sqlite3 \
    openssh-client xvfb imagemagick sudo \
    && rm -rf /var/lib/apt/lists/*

# ---------- Full-only packages ----------
RUN if [ "$VARIANT" = "full" ]; then \
    apt-get update && apt-get install -y --no-install-recommends \
      pandoc ffmpeg libvips-dev \
    && rm -rf /var/lib/apt/lists/*; \
    fi

# ---------- GitHub CLI ----------
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg 2>/dev/null && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list && \
    apt-get update && apt-get install -y gh && rm -rf /var/lib/apt/lists/*

# ---------- bat symlink ----------
RUN ln -sf /usr/bin/batcat /usr/local/bin/bat 2>/dev/null || true

# ---------- Locale ----------
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

# ---------- Create claude user ----------
RUN usermod -l claude -d /home/claude -m node && \
    groupmod -n claude node && \
    echo "claude ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/claude && \
    chmod 0440 /etc/sudoers.d/claude

# ---------- Claude Code CLI ----------
WORKDIR /workspace
USER claude
RUN curl -fsSL https://claude.ai/install.sh | bash
USER root
ENV PATH="/home/claude/.local/bin:${PATH}"

# ---------- npm global packages ----------
RUN npm i -g \
    typescript tsx pnpm \
    vite esbuild eslint prettier \
    serve nodemon concurrently dotenv-cli

RUN if [ "$VARIANT" = "full" ]; then \
    npm i -g \
      wrangler prisma drizzle-kit pm2 \
      sharp-cli json-server http-server \
      @cloudflare/next-on-pages; \
    fi

# ---------- Python packages ----------
RUN pip install --no-cache-dir --break-system-packages \
    requests httpx beautifulsoup4 lxml Pillow \
    pandas numpy openpyxl python-docx \
    jinja2 pyyaml python-dotenv markdown \
    rich click tqdm playwright apprise

RUN if [ "$VARIANT" = "full" ]; then \
    pip install --no-cache-dir --break-system-packages \
      reportlab weasyprint fpdf2 PyMuPDF \
      matplotlib seaborn python-pptx \
      fastapi uvicorn httpie; \
    fi

# ---------- Mekong CLI ----------
USER claude
RUN pip install --break-system-packages mekong-cli || true
USER root

# ---------- AI CLI providers ----------
RUN npm i -g @google/gemini-cli @openai/codex task-master-ai

# ---------- CloudCLI web UI ----------
RUN npm i -g @siteboon/claude-code-ui && \
    touch /usr/local/lib/node_modules/@siteboon/claude-code-ui/.env

# ---------- CloudCLI plugins ----------
USER claude
RUN mkdir -p /home/claude/.claude-code-ui/plugins && \
    git clone --depth 1 https://github.com/cloudcli-ai/cloudcli-plugin-starter.git \
      /home/claude/.claude-code-ui/plugins/project-stats && \
    cd /home/claude/.claude-code-ui/plugins/project-stats && npm install && npm run build && \
    git clone --depth 1 https://github.com/cloudcli-ai/cloudcli-plugin-terminal.git \
      /home/claude/.claude-code-ui/plugins/web-terminal && \
    cd /home/claude/.claude-code-ui/plugins/web-terminal && npm install && npm run build && \
    echo '{"project-stats":{"name":"project-stats","source":"local","enabled":true},"web-terminal":{"name":"web-terminal","source":"local","enabled":true}}' \
      > /home/claude/.claude-code-ui/plugins.json
USER root

# ---------- Store variant ----------
RUN echo "${VARIANT}" > /etc/mekong-variant

# ---------- Copy config ----------
COPY docker/scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY docker/scripts/bootstrap.sh /usr/local/bin/bootstrap.sh
COPY docker/scripts/notify.py /usr/local/bin/notify.py
COPY docker/config/claude-memory.md /usr/local/share/mekong/claude-memory.md
COPY docker/config/settings.json /usr/local/share/mekong/settings.json
RUN chmod +x /usr/local/bin/entrypoint.sh \
    /usr/local/bin/bootstrap.sh \
    /usr/local/bin/notify.py

# ---------- s6 service definitions ----------
COPY docker/s6-overlay/ /etc/s6-overlay/
RUN chmod +x /etc/s6-overlay/s6-rc.d/cloudcli/run \
    /etc/s6-overlay/s6-rc.d/xvfb/run \
    /etc/s6-overlay/s6-rc.d/mekong-gateway/run && \
    touch /etc/s6-overlay/s6-rc.d/user/contents.d/cloudcli && \
    touch /etc/s6-overlay/s6-rc.d/user/contents.d/xvfb && \
    touch /etc/s6-overlay/s6-rc.d/user/contents.d/mekong-gateway

WORKDIR /workspace
EXPOSE 3001 8000
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
