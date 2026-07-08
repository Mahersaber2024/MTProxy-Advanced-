#!/bin/bash
# uninstall.sh - Uninstall MTPulse Proxy Manager

echo "🗑️ Uninstalling MTPulse Proxy Manager..."

# Stop and remove all proxy services
for service in $(ls /etc/systemd/system/mtpulse-*.service 2>/dev/null | xargs -n1 basename); do
  sudo systemctl stop "$service" 2>/dev/null
  sudo systemctl disable "$service" 2>/dev/null
  sudo rm -f "/etc/systemd/system/$service"
done

sudo systemctl daemon-reload

# Remove binary and configs
sudo rm -f /usr/local/bin/mtproto-proxy
sudo rm -rf /etc/mtpulse
sudo rm -f /usr/local/bin/mtpulse
sudo rm -f /usr/local/bin/test_proxy.py
sudo rm -rf /opt/mtpulse-proxy
sudo rm -rf /var/lib/mtpulse

echo "✅ Uninstallation completed!"
