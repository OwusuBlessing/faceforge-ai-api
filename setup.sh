#!/bin/bash
# Verify Python 3.11 is installed
python3.11 --version

# Create symlinks so you can use 'python' command
sudo ln -sf /usr/bin/python3.11 /usr/local/bin/python
sudo ln -sf /usr/bin/python3.11 /usr/local/bin/python3

# Install pip for Python 3.11
sudo apt install python3.11-distutils
wget https://bootstrap.pypa.io/get-pip.py
python3.11 get-pip.py

# Test everything works
python --version
python -m pip --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Create logs directory if it doesn't exist
if [ ! -d "logs" ]; then
    echo "Creating logs directory..."
    mkdir logs
fi

echo "Setup completed successfully!" 