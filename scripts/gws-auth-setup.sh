#!/bin/bash
echo "🔐 Setting up Google Workspace auth..."
npx -y @googleworkspace/cli auth setup
echo "✅ Auth configured. Test: gws drive about get"
