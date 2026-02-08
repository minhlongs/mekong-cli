---
name: Python Dev Setup
description: Set up Python development environment with venv, dependencies, and test validation
author: Mekong CLI
tags: python,setup,dev,venv
---

# Python Dev Setup

Bootstrap a Python development environment: create virtualenv, install dependencies, and validate with tests.

## Step 1: Create virtual environment

python3 -m venv .venv

## Step 2: Install dependencies

.venv/bin/pip install -r requirements.txt

## Step 3: Run test suite

.venv/bin/python -m pytest tests/ -v --tb=short
