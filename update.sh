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
if [ -f "$INSTALL_DIR/mtproxy_stats.py" ]; then
    cp "$INSTALL_DIR/mtproxy_stats.py" "$BACKUP_DIR/"
fi
if [ -f "$INSTALL_DIR/mtproxy" ]; then
    cp "$INSTALL_DIR/mtproxy" "$BACKUP_DIR/"
fi

# Backup config
if [ -f "$CONFIG_DIR/proxies.json" ]; then
    echo "📦 Backing up configuration..."
    cp "$CONFIG_DIR/proxies.json" "$BACKUP_DIR/proxies.json.bak"
fi

# Download new files
echo "📥 Downloading new version..."
curl -s -o "$INSTALL_DIR/mtproxy.py" https://raw.githubusercontent.com/Mahersaber2024/MTProxy-Advanced-/main/mtproxy.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to download mtproxy.py"
    echo "🔄 Restoring from backup..."
    cp "$BACKUP_DIR/mtproxy.py" "$INSTALL_DIR/" 2>/dev/null
    exit 1
fi

curl -s -o "$INSTALL_DIR/mtproxy_stats.py" https://raw.githubusercontent.com/Mahersaber2024/MTProxy-Advanced-/main/mtproxy_stats.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to download mtproxy_stats.py"
    echo "🔄 Restoring from backup..."
    cp "$BACKUP_DIR/mtproxy_stats.py" "$INSTALL_DIR/" 2>/dev/null
    exit 1
fi

# Make executable
chmod +x "$INSTALL_DIR/mtproxy.py"
chmod +x "$INSTALL_DIR/mtproxy_stats.py"

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
echo "📊 New features:"
echo "   • Online/offline user statistics per proxy"
echo "   • Traffic usage per proxy"
echo "   • Real-time connection monitoring"
echo "   • Built-in update checker"
echo ""
echo "📁 Backup saved to: $BACKUP_DIR"
echo "   (Keep this in case you need to rollback)"
echo ""
echo "Run 'mtproxy' to see the new features!"