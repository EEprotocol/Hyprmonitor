#!/usr/bin/env bash
# Build a standalone binary: ./dist/hyprmonitor
set -euo pipefail
cd "$(dirname "$0")"

uv run --extra build pyinstaller \
    --noconfirm --clean --onefile \
    --name hyprmonitor \
    --distpath dist --workpath build/pyinstaller --specpath build \
    --paths . \
    packaging/entry.py
