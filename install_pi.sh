#!/bin/bash
# Raspberry Pi Installation Script for AI Attendance System
# This script installs necessary dependencies to run face_recognition and OpenCV on a Raspberry Pi.

echo "==================================================="
echo "  AI Attendance System - Raspberry Pi Setup Script"
echo "==================================================="

# 1. Update system
echo "[1/4] Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install required system dependencies for dlib, opencv, and tkinter
echo "[2/4] Installing C++ build tools and system dependencies..."
sudo apt-get install -y build-essential cmake pkg-config
sudo apt-get install -y libx11-dev libatlas-base-dev
sudo apt-get install -y libgtk-3-dev libboost-python-dev
sudo apt-get install -y python3-dev python3-pip python3-venv

# 3. Increase swap size temporarily to compile dlib
# Note: Compiling dlib on a Pi requires >2GB of RAM/Swap. 
echo "[3/4] Increasing SWAP size to 2048MB for dlib compilation..."
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=2048/g' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# 4. Create virtual environment and install python packages
echo "[4/4] Setting up Python virtual environment and installing packages..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install dependencies from requirements.txt
echo "Installing Python dependencies (This might take a while for dlib)..."
pip install -r requirements.txt

# Reset swap size to avoid SD card wear
echo "Reverting SWAP size back to 100MB..."
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=2048/CONF_SWAPSIZE=100/g' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

echo "==================================================="
echo "Setup Complete! You can now run the system using:"
echo "source venv/bin/activate"
echo "python main.py"
echo "==================================================="
