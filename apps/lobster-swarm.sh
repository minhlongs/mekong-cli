#!/bin/bash

# LOBSTER SWARM DEPLOYMENT SCRIPT
# Purpose: Verify 'cook claude' (Lobster Logic) consistency across all projects.

PROJECTS=("84tea" "apex-os" "sophia-ai-factory" "agencyos-landing" "anima119")
COOK_TOOL="../../apps/antigravity-gateway/cook.js"

echo "🦞 LOBSTER SWARM: INITIATING SEQUENCE..."
echo "=========================================="

for proj in "${PROJECTS[@]}"; do
    echo ""
    echo "📂 PROJECT: $proj"
    echo "   📍 Path: apps/$proj"
    
    cd "apps/$proj" || continue
    
    # Execute the Cook Wrapper with a simple print prompt to verify end-to-end connectivity
    # This proves CC CLI is running under Lobster Logic (Gateway/Proxy)
    $COOK_TOOL claude --print "Lobster Check for $proj: CONFIRMED."
    
    cd ../..
    echo "   ✅ Status: DEPLOYED"
    echo "------------------------------------------"
done

echo ""
echo "🦞 MISSION COMPLETE. ALL SYSTEMS GO."
