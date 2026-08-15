# Mekong CLI

**AI-powered business operations platform for solo entrepreneurs.**

Mekong CLI replaces your back-office team with AI agents -- accounting, tax filing, sales outreach, customer communication, all from your terminal.

## Features

- **Smart AI Routing** -- Route requests to the best model (Claude, fable-5, Gemini, DeepSeek) based on cost, speed, and capability
- **Multi-Agent Orchestration** -- Spawn specialized agents for different tasks (accounting, sales, support)
- **Real-time Streaming** -- SSE-based streaming for instant AI responses
- **Rate Limiting & Failover** -- Circuit breakers, exponential backoff, automatic provider switching
- **Plugin System** -- Extend with custom commands and skills
- **Vietnamese-first** -- Native Vietnamese language support for business operations

## Quick Start

```bash
# Install
npm install -g mekong-cli

# Initialize
mekong init

# Run
mekong start
```

## Architecture

```
mekong-cli/
├── src/          # Core CLI and engine
├── apps/         # Web dashboards and services
├── packages/     # Shared libraries
├── plugins/      # Official plugins
├── skills/       # AI agent skills
├── dna/          # Agent configurations
└── docs/         # Documentation
```

## Development

```bash
# Clone
git clone https://github.com/minhlongs/mekong-cli.git
cd mekong-cli

# Install dependencies
npm install

# Run tests
npm test

# Build
npm run build
```

## Configuration

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
# Edit .env with your keys
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT -- see [LICENSE](LICENSE) for details.

## Acknowledgments

Built with:
- [Cloudflare Workers](https://workers.cloudflare.com/) for edge computing
- [Drizzle ORM](https://orm.drizzle.team/) for database
- [Hono](https://hono.dev/) for HTTP framework
- [Anthropic Claude](https://www.nhà cung cấp dịch vụ AI.com/) for AI backbone
