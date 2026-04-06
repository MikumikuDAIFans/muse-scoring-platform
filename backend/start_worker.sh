#!/bin/bash
# Redis Worker - runs inside the fastapi container alongside the main app
echo "Starting Redis Worker..."
exec python redis_worker.py
