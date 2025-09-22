#!/usr/bin/env bash
set -e
# keep memory usage low on free tiers
export OMP_NUM_THREADS=1
PORT=${PORT:-8000}
exec uvicorn fastapp.main:app --host 0.0.0.0 --port "$PORT"
