#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Checking for existing Gunicorn processes on port 5120..."
PIDS=$(ss -tulnp | grep ":5120" | grep -oP '(?<=pid=)\d+')

if [ -n "$PIDS" ]; then
    echo "Stopping Gunicorn processes..."
    echo "$PIDS" | xargs -r kill -9
    echo "Gunicorn processes stopped."
else
    echo "No Gunicorn processes found on port 5120."
fi

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Run with eventlet
"$SCRIPT_DIR/venv/bin/gunicorn" --bind 0.0.0.0:5120 app:app \
  --worker-class eventlet --workers 1 \
  --timeout 300 --graceful-timeout 300 --daemon \
  --access-logfile "$SCRIPT_DIR/logs/cpu-access.log" \
  --error-logfile "$SCRIPT_DIR/logs/cpu-error.log"

echo "All OCR services started (CPU) with eventlet"

# Show the logs
echo -e "\nViewing logs (press Ctrl+C to exit):"
tail -f "$SCRIPT_DIR/logs/cpu-access.log" "$SCRIPT_DIR/logs/cpu-error.log"
