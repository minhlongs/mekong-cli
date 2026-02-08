---
name: Code Review
description: Run linting, check git diff, and generate a review summary
author: Mekong CLI
tags: review,lint,git,quality
---

# Code Review

Automated code review: lint check, git diff inspection, and summary report.

## Step 1: Check for syntax errors

python3 -m py_compile src/main.py && echo "Syntax OK"

## Step 2: Show uncommitted changes

git diff --stat

## Step 3: Generate review summary

echo "=== Code Review Summary ===" && echo "Modified files:" && git diff --name-only && echo "---" && echo "Lines changed:" && git diff --shortstat && echo "Review complete."
