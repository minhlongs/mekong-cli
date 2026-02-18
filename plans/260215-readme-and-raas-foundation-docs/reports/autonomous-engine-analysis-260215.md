# Autonomous Engine Analysis for Open Source Readiness
Date: 2026-02-15
Scope: `apps/openclaw-worker/` and `src/core/`
Objective: Identify internal dependencies, hardcoded paths, and logic coupling that impede open-sourcing.

## 1. Executive Summary

The autonomous engine (codenamed "Tom Hum" / "OpenClaw") acts as a persistent daemon that orchestrates Claude CLI sessions. While the core logic is robust, it is currently heavily coupled to the internal `macbookprom1` environment, specific internal project structures, and a custom proxy infrastructure ("Antigravity Proxy").

To achieve open-source readiness, a significant refactoring of configuration management is required, specifically moving hardcoded values to environment variables or a `config.json` file, and abstracting the project routing logic.

## 2. Critical Security Findings 🚨

### Hardcoded API Keys
- **File**: `src/core/autonomous.py`
- **Issue**: A raw Gemini API key (`AIzaSy...`) is hardcoded in the `analyze_codebase` function.
- **Action**: MUST be removed immediately and replaced with `os.getenv('GEMINI_API_KEY')`.

## 3. Environment Specifics

### Hardcoded User Paths
The codebase assumes it is running on a specific machine (`macbookprom1`).

- **`apps/openclaw-worker/config.js`**:
  - `MEKONG_DIR`: `'/Users/macbookprom1/mekong-cli'`
  - `LOG_DIR`: `'/Users/macbookprom1/.mekong/logs'`
- **`apps/openclaw-worker/lib/brain-tmux.js`**:
  - `claudeConfigDir`: Hardcoded to `/Users/macbookprom1/.claude` (inferred from usage).
- **`src/core/llm_client.py`**:
  - Contains references to local paths for context loading.

**Recommendation**: Use `process.env.HOME` in Node.js and `os.path.expanduser("~")` in Python to dynamically resolve user directories.

### Infrastructure Dependencies
The engine assumes the existence of specific local services which may not exist for public users.

- **Antigravity Proxy**: `http://127.0.0.1:11436` (Hardcoded in `config.js` and `llm_client.py`)
- **Qwen Bridge**: `http://127.0.0.1:8081`
- **Local Ollama**: `http://127.0.0.1:11434`

**Recommendation**: Make these URLs configurable via `.env`. Provide a "Standard Mode" that defaults to direct API calls if the proxy is not available.

## 4. Logic Coupling & Internal Business Rules

### Project Routing
The daemon has internal project names hardcoded, which will be irrelevant to outside users.

- **File**: `apps/openclaw-worker/config.js`
- **Issue**: `PROJECTS` array contains `['84tea', 'wellnexus', 'anima119', 'apex-os', ...]`
- **File**: `apps/openclaw-worker/lib/mission-dispatcher.js`
- **Issue**: `getProjectDir` function contains `switch` statements mapping specific keywords (`tea`, `84tea`) to internal paths.

**Recommendation**:
1. Implement a dynamic project discovery mechanism (e.g., scanning a `projects/` directory).
2. Move project mapping to a `projects.json` configuration file.

### Binh Phap (Art of War) Strategy
The autonomous behavior is tightly coupled to the "Binh Phap" philosophy (Sun Tzu's Art of War mapping). While this is a unique feature, the terminology might be confusing for general users.

- **File**: `apps/openclaw-worker/lib/auto-cto-pilot.js`
- **Issue**: Generates tasks based on specific internal quality gates (e.g., `console_cleanup`, `type_safety`).
- **Recommendation**: Keep this as a "flavor" or "plugin" but allow users to define their own autonomous maintenance tasks.

## 5. Architecture Observations

### Dual-Stack Complexity
The engine runs on two distinct stacks:
1.  **Node.js (`apps/openclaw-worker`)**: Handles the file system watching, queue management, and tmux orchestration.
2.  **Python (`src/core`)**: Handles the "Cognitive" layer (AGI loop, consciousness score, complex planning).

This split makes installation and management harder for end-users (requires both Node and Python environments).

**Recommendation**: Create a unified `setup.sh` or `docker-compose` definition that bootstraps both environments easily.

## 6. Action Plan for Open Sourcing

1.  **Sanitize**: Remove the API key from `src/core/autonomous.py`.
2.  **Config Refactor**:
    - Create `apps/openclaw-worker/config.default.js` using dynamic paths.
    - Create `.env.example` for Python core.
3.  **Abstract Routing**:
    - Modify `mission-dispatcher.js` to accept a generic project map.
4.  **Documentation**:
    - Update `README.md` to explain the "Dual-Stack" architecture.
    - Document the "Antigravity Proxy" requirement or how to bypass it.

## 7. Conclusion

The "Autonomous Engine" is highly capable but currently treated as an internal tool. It is not "plug-and-play" for the open-source community in its current state. The primary blocker is the hardcoded configuration and specific infrastructure assumptions. Once these are abstracted, it will be a powerful tool for any developer wanting a "self-healing" repository.
