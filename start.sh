#!/usr/bin/env bash
# Quick start script — builds and runs the full stack (API + MySQL).
set -e

echo "🚀 Starting Cloud Monitoring & Auto-Healing System..."

if [ ! -f .env ]; then
  echo "📄 No .env found — copying .env.example to .env"
  cp .env.example .env
fi

docker-compose up --build -d

echo ""
echo "✅ System is starting up."
echo "   API:      http://localhost:5000/api/health"
echo "   Metrics:  http://localhost:5000/api/metrics"
echo "   Alerts:   http://localhost:5000/api/alerts"
echo ""
echo "View logs with: docker-compose logs -f"
echo "Stop with:      docker-compose down"
