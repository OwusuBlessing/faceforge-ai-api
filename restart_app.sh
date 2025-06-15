#!/bin/bash

# Production-ready Gunicorn startup script with auto-scaling and optimizations
set -e  # Exit on any error

# Configuration variables
PORT=${PORT:-5120}
HOST=${HOST:-"0.0.0.0"}
APP_MODULE=${APP_MODULE:-"app:app"}
ENVIRONMENT=${ENVIRONMENT:-"production"}

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Calculate optimal worker count based on CPU cores
CPU_CORES=$(nproc)
WORKERS=$((2 * CPU_CORES + 1))  # Common formula: (2 x CPU cores) + 1
MAX_WORKERS=${MAX_WORKERS:-$WORKERS}

log_info "Detected $CPU_CORES CPU cores, setting workers to $MAX_WORKERS"

# Memory-based worker calculation (optional override)
TOTAL_RAM_GB=$(free -g | awk 'NR==2{print $2}')
if [ "$TOTAL_RAM_GB" -lt 4 ]; then
    MAX_WORKERS=$((MAX_WORKERS / 2))  # Reduce workers for low memory systems
    log_warning "Low memory detected (${TOTAL_RAM_GB}GB), reducing workers to $MAX_WORKERS"
fi

log_info "Checking for existing processes on port $PORT..."
PIDS=$(ss -tulnp | grep ":$PORT" | grep -oP '(?<=pid=)\d+' 2>/dev/null || true)

if [ -n "$PIDS" ]; then
    log_info "Stopping existing processes on port $PORT..."
    echo "$PIDS" | xargs -r kill -TERM  # Graceful shutdown first
    sleep 3
    
    # Check if processes are still running and force kill if necessary
    REMAINING_PIDS=$(ss -tulnp | grep ":$PORT" | grep -oP '(?<=pid=)\d+' 2>/dev/null || true)
    if [ -n "$REMAINING_PIDS" ]; then
        log_warning "Force killing remaining processes..."
        echo "$REMAINING_PIDS" | xargs -r kill -9
    fi
    log_success "Previous processes stopped."
else
    log_info "No existing processes found on port $PORT."
fi

# Create necessary directories
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/tmp"

# Create log files with proper permissions
touch "$SCRIPT_DIR/logs/access.log"
touch "$SCRIPT_DIR/logs/error.log"
chmod 644 "$SCRIPT_DIR/logs"/*.log

# Initialize conda environment
export PATH="$HOME/miniconda3/bin:$PATH"
if [ -f "$HOME/miniconda3/bin/activate" ]; then
    source "$HOME/miniconda3/bin/activate" python312
    log_success "Conda environment activated"
else
    log_error "Conda not found, using system Python"
fi

# Verify Python and required packages
log_info "Using Python: $(which python)"
log_info "Python version: $(python --version)"

# Check if required packages are installed
python -c "import gunicorn, uvicorn" 2>/dev/null || {
    log_error "Required packages (gunicorn, uvicorn) not found"
    exit 1
}

# Set resource limits
ulimit -n 65536  # Increase file descriptor limit

# Calculate timeouts based on expected request processing time
TIMEOUT=${TIMEOUT:-600}
GRACEFUL_TIMEOUT=${GRACEFUL_TIMEOUT:-30}
KEEPALIVE=${KEEPALIVE:-5}

# Production-optimized Gunicorn configuration
log_info "Starting Gunicorn with $MAX_WORKERS workers..."

python -m gunicorn "$APP_MODULE" \
    --bind "$HOST:$PORT" \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers "$MAX_WORKERS" \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout "$TIMEOUT" \
    --graceful-timeout "$GRACEFUL_TIMEOUT" \
    --keep-alive "$KEEPALIVE" \
    --preload \
    --daemon \
    --pid "$SCRIPT_DIR/tmp/gunicorn.pid" \
    --access-logfile "$SCRIPT_DIR/logs/access.log" \
    --error-logfile "$SCRIPT_DIR/logs/error.log" \
    --access-logformat '%h %l %u %t "%r" %s %b "%{Referer}i" "%{User-Agent}i" %D' \
    --log-level info \
    --capture-output \
    --enable-stdio-inheritance

# Check if the process started successfully
sleep 2
if [ -f "$SCRIPT_DIR/tmp/gunicorn.pid" ] && kill -0 "$(cat "$SCRIPT_DIR/tmp/gunicorn.pid")" 2>/dev/null; then
    PID=$(cat "$SCRIPT_DIR/tmp/gunicorn.pid")
    log_success "Gunicorn started successfully with PID: $PID"
    log_info "Application running on http://$HOST:$PORT"
    log_info "Workers: $MAX_WORKERS"
    log_info "Environment: $ENVIRONMENT"
    
    # Display process information
    log_info "Process details:"
    ps aux | grep gunicorn | grep -v grep | head -5
else
    log_error "Failed to start Gunicorn"
    exit 1
fi

# Function to show logs
show_logs() {
    log_info "Viewing logs (press Ctrl+C to exit):"
    tail -f "$SCRIPT_DIR/logs/access.log" "$SCRIPT_DIR/logs/error.log"
}

# Function to stop the application
stop_app() {
    if [ -f "$SCRIPT_DIR/tmp/gunicorn.pid" ]; then
        PID=$(cat "$SCRIPT_DIR/tmp/gunicorn.pid")
        log_info "Stopping Gunicorn (PID: $PID)..."
        kill -TERM "$PID"
        rm -f "$SCRIPT_DIR/tmp/gunicorn.pid"
        log_success "Application stopped"
    fi
    exit 0
}

# Set up signal handlers
trap stop_app SIGTERM SIGINT

# Show logs by default, but allow skipping with --no-logs flag
if [[ "$*" != *"--no-logs"* ]]; then
    show_logs
else
    log_info "Use 'tail -f $SCRIPT_DIR/logs/*.log' to view logs"
    log_info "Use 'kill -TERM $(cat $SCRIPT_DIR/tmp/gunicorn.pid)' to stop the application"
fi