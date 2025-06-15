#!/bin/bash

set -e

echo "========================================="
echo "Installing Miniconda with Python 3.12"
echo "========================================="

# Download Miniconda
echo "Downloading Miniconda..."
cd /tmp
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh

# Install Miniconda
echo "Installing Miniconda..."
bash miniconda.sh -b -p $HOME/miniconda3

# Initialize conda
echo "Initializing conda..."
$HOME/miniconda3/bin/conda init bash

# Add conda to PATH for current session
export PATH="$HOME/miniconda3/bin:$PATH"

# Reload bashrc to make conda available
source ~/.bashrc 2>/dev/null || true

# Update conda
echo "Updating conda..."
conda update -y conda

# Create environment with Python 3.12
echo "Creating Python 3.12 environment..."
conda create -y -n python312 python=3.12

# Activate the environment
echo "Activating Python 3.12 environment..."
source $HOME/miniconda3/bin/activate python312

# Verify installation
echo "Verifying installation..."
python --version
python -c "from typing import override; print('✓ typing.override works!')"
pip --version

# Clean up
rm -f /tmp/miniconda.sh

echo "========================================="
echo "Miniconda installation completed!"
echo "========================================="
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"
echo ""
echo "To activate Python 3.12 environment in future sessions:"
echo "conda activate python312"
echo ""
echo "To deactivate:"
echo "conda deactivate"
echo ""
echo "Your environment is ready!"