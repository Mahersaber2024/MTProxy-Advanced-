#!/bin/bash
# uninstall.sh - Uninstall MTProxy Manager

echo "🗑️ Uninstalling MTProxy Manager..."

# Stop and remove service
sudo systemctl stop mtprotoproxy 2>/dev/null
sudo systemctl disable mtprotoproxy 2>/dev/null
sudo rm -f /etc/systemd/system/mtprotoproxy.service
sudo systemctl daemon-reload

# Remove proxy directory and configs
sudo rm -rf /opt/mtprotoproxy
sudo rm -rf /etc/mtpulse
sudo rm -f /usr/local/bin/mtproxy
sudo rm -f /usr/local/bin/test_proxy.py

echo "✅ Uninstallation completed!"
