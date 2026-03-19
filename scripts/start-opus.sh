#!/bin/bash
# Start CC CLI with Opus chính hãng (Claude Max Auth)
# Unset all DashScope/Qwen vars to use Anthropic Auth

unset ANTHROPIC_BASE_URL
unset ANTHROPIC_API_KEY
unset ANTHROPIC_MODEL
unset ANTHROPIC_DEFAULT_OPUS_MODEL
unset ANTHROPIC_DEFAULT_SONNET_MODEL
unset ANTHROPIC_DEFAULT_HAIKU_MODEL
unset ANTHROPIC_AUTH_TOKEN
unset DASHSCOPE_API_KEY
unset DASHSCOPE_API_KEYS

cd ~/mekong-cli

echo "🚀 Starting Opus (Claude Max Auth) in mekong-cli..."
claude --dangerously-skip-permissions "$@"
