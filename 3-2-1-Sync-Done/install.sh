#!/bin/bash

cd "$(dirname "$0")"
echo "Creating virtual environment for 3-2-1 Sync Done..."
python3 -m venv .venv

if [ $? -ne 0 ]; then
    echo "Failed to create the virtual environment."
    echo "Please make sure Python 3 is installed."
    exit 1
fi

echo "Installing dependencies for 3-2-1 Sync Done..."
.venv/bin/python -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Failed to install dependencies."
    exit 1
fi

echo "Installation complete!"
echo "3-2-1 Sync-Done! will now launch..."
.venv/bin/python "main-control.py"