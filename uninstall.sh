#!/bin/bash
# uninstall.sh - Uninstall MTPulse Proxy Manager

echo "🗑️ Uninstalling MTPulse Proxy Manager..."

# Stop and disable service
sudo systemctl stop mtpulse 2>/dev/null
sudo systemctl disable mtpulse 2>/dev/null
sudo rm -f /etc/systemd/system/mtpulse.service
sudo systemctl daemon-reload

# Remove binary and configs
sudo rm -f /usr/local/bin/mtproto-proxy
sudo rm -rf /etc/mtpulse
sudo rm -f /usr/local/bin/mtpulse

# Remove app directory
sudo rm -rf /opt/mtpulse-proxy

# Remove marker files
sudo rm -rf /var/lib/mtpulse

echo "✅ Uninstallation completed!"
