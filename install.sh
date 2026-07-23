#!/usr/bin/env bash
set -e

echo "== Gmail Purger setup =="

if ! command -v docker &> /dev/null; then
    echo "Docker not found. Install it first: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

if [ ! -f .env ]; then
    echo ".env not found — copying from .env.example"
    cp .env.example .env
    echo "Edit .env now with your real Gmail address and app password, then rerun this script."
    exit 1
fi

if [ ! -f config/targets.json ]; then
    echo "config/targets.json not found — copying from example"
    cp config/targets.json.example config/targets.json
    echo "Edit config/targets.json with your real target addresses, then rerun this script."
    exit 1
fi

echo "Building and starting containers..."
docker compose up -d --build

echo ""
echo "Done. Check status with: docker compose ps"
echo "View worker logs with:   docker compose logs -f worker"
echo "Dashboard available at:  http://$(hostname):5005"