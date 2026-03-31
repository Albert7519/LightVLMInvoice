#!/bin/bash

# LocalllmOcrMK2 Cleanup Script
# Removes background processes, logs, and cache files

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"

echo "🧹 Cleaning up LocalllmOcrMK2..."

# Kill any lingering processes
echo "Stopping services..."
for f in redis.pid vllm.pid celery.pid; do
    if [ -f "$BACKEND_DIR/$f" ]; then
        PID=$(cat "$BACKEND_DIR/$f")
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            echo "  ✓ Killed process $f (PID: $PID)"
        fi
        rm "$BACKEND_DIR/$f"
    fi
done

# Shutdown Redis gracefully
redis-cli shutdown 2>/dev/null || true

# Clean temporary files
echo "Removing temporary files..."
rm -f "$BACKEND_DIR"/*.log
rm -rf "$BACKEND_DIR/__pycache__"
rm -rf "$BACKEND_DIR/.pytest_cache"
find "$BACKEND_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Clean uploads (optional)
read -p "Remove uploads directory? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$BACKEND_DIR/uploads"
    echo "  ✓ Removed uploads directory"
fi

echo "✅ Cleanup complete"
