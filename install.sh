#!/bin/bash

echo "==================================="
echo "Watch Marker - Installation Script"
echo "==================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install it first."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check if VLC is installed
if ! command -v vlc &> /dev/null; then
    echo "❌ VLC is not installed."
    echo ""
    echo "Please install VLC Media Player:"
    echo "  Ubuntu/Debian: sudo apt install vlc"
    echo "  Fedora:        sudo dnf install vlc"
    echo "  Arch Linux:    sudo pacman -S vlc"
    exit 1
fi

echo "✓ VLC found: $(vlc --version | head -n 1)"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Installation complete!"
    echo ""
    echo "Run the application with:"
    echo "  python3 main.py"
else
    echo ""
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi

