#!/bin/bash

# ⚡ BLITZKRIEG CLEANUP SCRIPT
# Deep optimization for MacBook M1 VibeCoding Hub
# Author: Antigravity

echo "🚀 Starting Blitzkrieg Cleanup..."

# 1. System Maintenance (Safe)
echo "🧹 Purging RAM..."
sudo purge

# 2. Browser Cache (Heavy memory consumers)
echo "🧹 Cleaning Browser Caches..."
rm -rf ~/Library/Caches/Google/Chrome/Default/Cache/* 2>/dev/null
rm -rf ~/Library/Caches/Google/Chrome/Default/Code\ Cache/* 2>/dev/null
rm -rf ~/Library/Caches/com.apple.Safari/Cache.db* 2>/dev/null

# 3. Development Caches (Safe to delete)
echo "🧹 Cleaning Project Caches..."
# Only clear caches of non-active projects or known safe paths
rm -rf ~/.npm/_cacache 2>/dev/null
rm -rf ~/.cache/uv 2>/dev/null

# 4. App-specific Caches
echo "🧹 Cleaning App Caches..."
rm -rf ~/Library/Caches/com.spotify.client 2>/dev/null
rm -rf ~/Library/Caches/com.mentalfaculty.cursor.ShipIt 2>/dev/null
rm -rf ~/Library/Caches/com.todesktop.230313m707u9p9s 2>/dev/null # Cursor

# 5. Build Artifacts (Only non-active)
# Assuming mekong-cli/frontend is not the one running on 3005
# rm -rf ~/mekong-cli/frontend/.next/cache 2>/dev/null 

echo "✅ Blitzkrieg Complete! System optimized."
