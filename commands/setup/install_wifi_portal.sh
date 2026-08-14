#!/usr/bin/env bash
# Installs the WiFi onboarding portal (wifi_portal/) as a systemd service
# that runs at boot, before touch_point.py needs a network at all -- the
# two are independent, this just gets the Pi itself online.
#
# Run from the repo root, e.g.:
#   cd ~/touch_point && bash commands/setup/install_wifi_portal.sh
set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_PYTHON="$APP_DIR/venv/bin/python"

echo "=== Installing WiFi onboarding portal ==="

if [ ! -x "$VENV_PYTHON" ]; then
  echo "!!! ERROR: no venv found at $APP_DIR/venv -- run the main setup script first."
  exit 1
fi

echo ">>> Installing Flask into the existing venv..."
"$APP_DIR/venv/bin/pip" install flask

echo ">>> Installing captive-portal DNS redirect for NetworkManager's shared-mode dnsmasq..."
sudo mkdir -p /etc/NetworkManager/dnsmasq-shared.d
sudo cp "$APP_DIR/wifi_portal/dnsmasq-captive.conf" /etc/NetworkManager/dnsmasq-shared.d/captive.conf

echo ">>> Installing systemd service..."
sed "s|__APP_DIR__|$APP_DIR|g" "$APP_DIR/wifi_portal/wifi-portal.service.template" \
  | sudo tee /etc/systemd/system/wifi-portal.service > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable wifi-portal.service

echo "=== Done ==="
echo "The portal will run automatically on next boot if no known WiFi is found"
echo "within 45 seconds. To test it right now without rebooting:"
echo "  sudo systemctl start wifi-portal"
echo "  sudo journalctl -u wifi-portal -f     # watch what it's doing"
echo
echo "It looks for a network named 'Touch Point Setup' from your phone --"
echo "connect to that, and the setup page should open automatically."
echo
echo "To stop/disable it entirely:"
echo "  sudo systemctl disable --now wifi-portal"
