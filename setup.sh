#!/bin/bash

set -e

echo "Setting up project with conda environment..."

# Initialize conda for this session
export PATH="$HOME/miniconda3/bin:$PATH"
source $HOME/miniconda3/bin/activate python312

# Verify we're in the right environment
echo "Current Python version: $(python --version)"
echo "Current environment: $CONDA_DEFAULT_ENV"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements if file exists
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    echo "No requirements.txt found, skipping package installation."
fi

# Create logs directory if it doesn't exist
echo "Creating logs directory..."
mkdir -p logs

# Test typing.override
echo "Testing typing.override..."
python -c "from typing import override; print('✓ typing.override works!')"

echo "========================================="
echo "Project setup completed!"
echo "========================================="
echo "To run your project:"
echo "1. conda activate python312"
echo "2. python app.py"
echo ""