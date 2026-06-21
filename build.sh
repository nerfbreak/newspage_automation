#!/usr/bin/env bash
# Render build script - installs dependencies including Playwright Chromium
set -e

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "Installing Playwright Chromium browser..."
playwright install chromium
playwright install-deps chromium

echo "Build complete."
