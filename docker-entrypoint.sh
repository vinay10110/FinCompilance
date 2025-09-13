#!/bin/bash
set -e

# Wait for database to be ready (if using external database)
echo "🔄 Waiting for database connection..."

# Start the FastAPI application
echo "🚀 Starting FinCompliance Backend..."
exec python -m uvicorn app:app --host 0.0.0.0 --port 5000
