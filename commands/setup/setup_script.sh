#!/usr/bin/env bash
set -e

### ==============================
### USER SETTINGS – EDIT THESE
### ==============================

# Your GitHub repo URL (HTTPS recommended)
REPO_URL="https://github.com/BenLBurke/touch_point.git"

# Directory where the app should live
APP_DIR="/home/pi/touch_point"

# Name of the Python virtual environment folder
VENV_DIR="venv"

# Entry point for your app (relative to APP_DIR)
# e.g. "main.py" or "src/app.py"
APP_ENTRY="touch_point.py"

# Name PM2 will use for the process
PM2_APP_NAME="touch_point"

### ==============================
### NO NEED TO EDIT BELOW (usually)
### ==============================

echo "=== Magic Orb setup starting ==="

# Ensure we are not root but have sudo
if [ "$EUID" -eq 0 ]; then
  echo "Please run this script as the 'pi' user, not root."
  echo "Example:  sudo -u pi bash $0"
  exit 1
fi

# Update & install packages
echo ">>> Updating apt and installing dependencies..."
sudo apt update
sudo apt install -y \
  git \
  python3 \
  python3-venv \
  python3-pip \
  nodejs \
  npm \
  raspi-config

# Enable SPI (for RC522)
echo ">>> Enabling SPI..."
sudo raspi-config nonint do_spi 0

# (Optional) You can disable I2C here if you want to avoid conflicts:
# sudo raspi-config nonint do_i2c 1

# Create app directory if it doesn't exist
echo ">>> Preparing app directory at: $APP_DIR"
mkdir -p "$APP_DIR"

# Clone or update repo
if [ ! -d "$APP_DIR/.git" ]; then
  echo ">>> Cloning repo from $REPO_URL ..."
  git clone "$REPO_URL" "$APP_DIR"
else
  echo ">>> Repo already exists, pulling latest changes..."
  cd "$APP_DIR"
  git pull
fi

cd "$APP_DIR"

# Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
  echo ">>> Creating virtual environment: $VENV_DIR"
  python3 -m venv "$VENV_DIR"
else
  echo ">>> Virtual environment already exists: $VENV_DIR"
fi

# Activate venv and upgrade pip
echo ">>> Activating virtual environment and installing Python deps..."
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

pip install --upgrade pip wheel

# Install requirements if present
if [ -f "requirements.txt" ]; then
  echo ">>> Installing requirements.txt..."
  pip install -r requirements.txt
else
  echo ">>> No requirements.txt found. Skipping Python deps install."
fi

deactivate

# Install PM2 globally (if not already)
echo ">>> Installing PM2 (if needed)..."
sudo npm install -g pm2

# Start app with PM2 using venv Python
FULL_APP_PATH="$APP_DIR/$APP_ENTRY"
VENV_PYTHON="$APP_DIR/$VENV_DIR/bin/python"

if [ ! -f "$FULL_APP_PATH" ]; then
  echo "!!! ERROR: App entry file not found: $FULL_APP_PATH"
  echo "    Please update APP_ENTRY in this script to the correct path."
  exit 1
fi

echo ">>> Starting $PM2_APP_NAME with PM2 using interpreter: $VENV_PYTHON"
pm2 start "$FULL_APP_PATH" \
  --name "$PM2_APP_NAME" \
  --interpreter "$VENV_PYTHON"

# Save PM2 process list and enable startup
echo ">>> Saving PM2 process list and enabling startup..."
pm2 save
# This generates a startup command for systemd and runs it
pm2 startup systemd -u "$USER" --hp "/home/$USER" | sudo bash

echo "=== Setup complete! ==="
echo "Repo:      $REPO_URL"
echo "App dir:   $APP_DIR"
echo "Venv:      $APP_DIR/$VENV_DIR"
echo "Entry:     $FULL_APP_PATH"
echo "PM2 name:  $PM2_APP_NAME"
echo
echo "You can check logs with:"
echo "  pm2 logs $PM2_APP_NAME"
echo
echo "To update code later:"
echo "  cd $APP_DIR"
echo "  git pull"
echo "  source $VENV_DIR/bin/activate && pip install -r requirements.txt && deactivate"
echo "  pm2 restart $PM2_APP_NAME"
