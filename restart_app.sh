#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Checking for existing Gunicorn processes on port 5120..."
PIDS=$(ss -tulnp | grep ":5120" | grep -oP '(?<=pid=)\d+' || true)

if [ -n "$PIDS" ]; then
    echo "Stopping Gunicorn processes..."
    echo "$PIDS" | xargs -r kill -9
    echo "Gunicorn processes stopped."
else
    echo "No Gunicorn processes found on port 5120."
fi

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Create log files if they don't exist
touch "$SCRIPT_DIR/logs/cpu-access.log"
touch "$SCRIPT_DIR/logs/cpu-error.log"

# Initialize conda and activate environment
export PATH="$HOME/miniconda3/bin:$PATH"
source $HOME/miniconda3/bin/activate python312

# Verify we're using the right Python
echo "Using Python: $(which python)"
echo "Python version: $(python --version)"

# Run with uvicorn workers for FastAPI
python -m gunicorn --bind 0.0.0.0:5120 app:app \
  --worker-class uvicorn.workers.UvicornWorker --workers 1 \
  --timeout 300 --graceful-timeout 300 --daemon \
  --access-logfile "$SCRIPT_DIR/logs/cpu-access.log" \
  --error-logfile "$SCRIPT_DIR/logs/cpu-error.log"

echo "APP STARTED SUCCESSFULLY"

# Show the logs
echo -e "\nViewing logs (press Ctrl+C to exit):"
tail -f "$SCRIPT_DIR/logs/cpu-access.log" "$SCRIPT_DIR/logs/cpu-error.log"