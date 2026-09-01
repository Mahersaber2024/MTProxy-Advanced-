#!/bin/bash
# update.sh - Update MTProxy Manager to latest version

echo "🔄 Updating MTProxy Manager..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (sudo)"
    exit 1
fi

# Define paths
INSTALL_DIR="/usr/local/bin"
CONFIG_DIR="/etc/mtpulse"
BACKUP_DIR="/tmp/mtproxy_backup_$(date +%Y%m%d_%H%M%S)"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup current files
echo "📦 Backing up current files..."
if [ -f "$INSTALL_DIR/mtproxy.py" ]; then
    cp "$INSTALL_DIR/mtproxy.py" "$BACKUP_DIR/"
fi
for f in mtproxy_stats.py mtproxy_socks.py socks5_server.py; do
    [ -f "$INSTALL_DIR/$f" ] && cp "$INSTALL_DIR/$f" "$BACKUP_DIR/"
done
if [ -f "$INSTALL_DIR/mtproxy" ]; then
    cp "$INSTALL_DIR/mtproxy" "$BACKUP_DIR/"
fi

# Backup config
if [ -f "$CONFIG_DIR/proxies.json" ]; then
    echo "📦 Backing up configuration..."
    cp "$CONFIG_DIR/proxies.json" "$BACKUP_DIR/proxies.json.bak"
fi

# Clean stale bytecode cache (causes old code to run even after update)
echo "🧹 Clearing Python cache..."
rm -rf "$INSTALL_DIR/__pycache__"

# Download new files
echo "📥 Downloading new version..."
echo "  (this may take 10-30 seconds...)"

DOWNLOAD_OK=1

echo "  • mtproxy.py..."
curl -s --max-time 30 -w "\n" -o "$INSTALL_DIR/mtproxy.py" https://raw.githubusercontent.com/Mahersaber2024/MTProxy-Advanced-/main/mtproxy.py
if [ $? -ne 0 ] || [ ! -s "$INSTALL_DIR/mtproxy.py" ]; then
    echo "    ❌ FAILED (network timeout or file not in repo)"
    DOWNLOAD_OK=0
fi

if [ $DOWNLOAD_OK -eq 1 ]; then
  for f in mtproxy_stats.py mtproxy_socks.py socks5_server.py; do
    echo "  • $f..."
    curl -s --max-time 30 -w "\n" -o "$INSTALL_DIR/$f" "https://raw.githubusercontent.com/Mahersaber2024/MTProxy-Advanced-/main/$f"
    if [ $? -ne 0 ] || [ ! -s "$INSTALL_DIR/$f" ]; then
        echo "    ❌ FAILED"
        DOWNLOAD_OK=0
        break
    fi
    chmod +x "$INSTALL_DIR/$f"
  done
fi

if [ $DOWNLOAD_OK -eq 0 ]; then
    echo ""
    echo -e "${RED}❌ Download failed. Files not in GitHub yet?${NC}"
    echo "Possible causes:"
    echo "  1. Files haven't been pushed to GitHub repo"
    echo "  2. GitHub is slow or unreachable"
    echo "  3. Network/firewall blocking"
    echo ""
    echo "Solution: Use the offline installer instead:"
    echo "  sudo bash /root/mtproxy-3.5.0-offline-installer.sh"
    echo ""
    echo "🔄 Restoring old files from backup..."
    for f in mtproxy.py mtproxy_stats.py mtproxy_socks.py socks5_server.py; do
        [ -f "$BACKUP_DIR/$f" ] && cp "$BACKUP_DIR/$f" "$INSTALL_DIR/" 2>/dev/null || true
    done
    echo "Backup restored to $INSTALL_DIR"
    exit 1
fi

# Make executable
chmod +x "$INSTALL_DIR/mtproxy.py"

# Replace the main executable with the new Python script
echo "🔄 Updating main executable..."
if [ -f "$INSTALL_DIR/mtproxy" ]; then
    # Backup old version if not already backed up
    if [ ! -f "$BACKUP_DIR/mtproxy" ]; then
        cp "$INSTALL_DIR/mtproxy" "$BACKUP_DIR/"
    fi
fi
cp "$INSTALL_DIR/mtproxy.py" "$INSTALL_DIR/mtproxy"
chmod +x "$INSTALL_DIR/mtproxy"

# Restart SOCKS5 service if installed
if [ -f /etc/systemd/system/mtsocks.service ]; then
    echo "🔄 Restarting SOCKS5 service..."
    systemctl daemon-reload
    systemctl restart mtsocks 2>/dev/null
fi

# Restart service if running
if systemctl is-active --quiet mtprotoproxy; then
    echo "🔄 Restarting proxy service..."
    systemctl restart mtprotoproxy
    if [ $? -ne 0 ]; then
        echo "⚠️  Warning: Service restart failed. Please check manually."
    fi
fi

# Clean up old backups (keep last 5)
echo "🧹 Cleaning up old backups..."
ls -t /tmp/mtproxy_backup_* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null

echo ""
echo "✅ Update completed successfully!"
echo "📊 New in 3.5.0:"
echo "   • SOCKS5 proxy support (non-Telegram) - menu option 7"
echo "   • FIXED: traffic/usage now counted correctly and survives restarts"
echo "   • Online / Peak / Connects / Usage per proxy"
echo "   • Real-time connection monitoring"
echo "   • Bulk delete all proxies at once (menu option 8)"
echo "   • Built-in update checker"
echo ""
echo "📁 Backup saved to: $BACKUP_DIR"
echo "   (Keep this in case you need to rollback)"
echo ""
echo ""
echo -e "${GREEN}${BOLD}✅ All files downloaded successfully${NC}"
echo "🔄 Restarting program in 2 seconds..."
sleep 2
exec mtproxy