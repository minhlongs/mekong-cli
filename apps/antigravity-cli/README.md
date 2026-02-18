# 🍳 COOK: The Anti-Gravity Wrapper for AI CLIs

> **"Don't let them cook your data. YOU cook."**

[![npm version](https://badge.fury.io/js/%40antigravity%2Fcook.svg)](https://badge.fury.io/js/%40antigravity%2Fcook)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Cook** is a privacy-first, stealth-mode wrapper for popular AI instruments like `claude-code`. It acts as a local interceptor that masks your sensitive data (PII, API Keys) *before* it leaves your machine, and routes your traffic through a resilient, specialized proxy network to avoid rate limits.

## 🚀 Why use Cook?

- **🕵️ Data Masking (Zero-Trust)**: Automatically redacts email addresses, passwords, and secret keys locally. The AI provider only sees `[REDACTED_SECRET]`.
- **⚡️ WAF Evasion**: Tired of `403 Forbidden` or `429 Too Many Requests`? Cook rotates your connection through a "Waterfall" of high-reputation IPs.
- **🔋 Battery Included**: Comes with a built-in "Brain" that optimizes latency.

## 📦 Installation

```bash
npm install -g @antigravity/cook
```

## 🔥 Usage

Simply replace `claude` with `cook claude`:

```bash
# Before (Unsafe, Rate-Limited)
claude --print "Fix this DB connection string: postgres://user:pass@localhost:5432"

# After (Masked, Resilient)
cook claude --print "Fix this DB connection string: postgres://user:pass@localhost:5432"
```

**Interactive Mode:**
```bash
cook claude
```

**Check Status:**
```bash
cook status
# 🦞 Antigravity Gateway: Online
```

## 🛠️ Configuration

Cook works out of the box with a Free Tier (Hacker Plan).
To unlock higher rate limits and Residential IPs:

```bash
cook login
# Opens browser to authenticate
```

## 🤝 Contributing

We believe in privacy as a human right. This client is open source. 
The backend infrastructure is proprietary to protect the network integrity.

## 📄 License

MIT © Antigravity DAO
