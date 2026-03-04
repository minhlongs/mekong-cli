# Task Plan: Install Missing Dependencies (mem0ai, qdrant-client)

## Issue
Current Mekong CLI installation shows warnings:
- "mem0ai not installed. Mem0 memory provider unavailable."
- "qdrant-client not installed. Vector storage unavailable."

These dependencies are required for the advanced memory system with semantic vector search capabilities.

## Root Cause
The dependencies are defined in `packages/memory/pyproject.toml` but not in the main `pyproject.toml`, and there may be version compatibility issues with the Python environment.

## Solution Approach
1. Investigate the version compatibility issue
2. Add dependencies to main project with appropriate version constraints
3. Set up proper optional dependency structure
4. Test the installation and memory functionality

## Implementation Steps

### Step 1: Fix version constraint in main pyproject.toml
Currently, main pyproject.toml has `python = ">=3.9"` which should be compatible, but Poetry might be interpreting something differently.

### Step 2: Add optional dependencies
Add mem0ai and qdrant-client as optional dependencies to avoid forcing installation on all users.

### Step 3: Update package integration
Ensure the memory system integrates properly with the main application.

## Files to Modify
- `pyproject.toml` - Add optional dependencies
- `packages/memory/__init__.py` - Verify proper imports and initialization
- `src/core/llm_client.py` - Integrate with existing codebase if needed

## Expected Outcome
- No more dependency warnings in basic operation
- Vector memory system available when dependencies are installed
- YAML fallback still functional when dependencies are absent
- Backward compatibility maintained

## Verification
1. Run `mekong version` without dependency warnings (when optional deps not installed)
2. Install optional dependencies and verify memory system activation
3. Confirm graceful degradation to YAML storage when dependencies unavailable
4. Run existing test suite to ensure no regressions