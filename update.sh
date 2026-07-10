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

# Backup current config
if [ -f "$CONFIG_DIR/proxies.json" ]; then
    echo "📦 Backing up configuration..."
    cp "$CONFIG_DIR/proxies.json" "$CONFIG_DIR/proxies.json.bak"
fi

# Download new files
echo "📥 Downloading new version..."
curl -s -o "$INSTALL_DIR/mtproxy.py" https://raw.githubusercontent.com/Mahersaber2024/MTProxy-Advanced-/main/mtproxy.py
curl -s -o "$INSTALL_DIR/mtproxy_stats.py" https://raw.githubusercontent.com/Mahersaber2024/MTProxy-Advanced-/main/mtproxy_stats.py

# Make executable
chmod +x "$INSTALL_DIR/mtproxy.py"
chmod +x "$INSTALL_DIR/mtproxy_stats.py"

if [ -f "$INSTALL_DIR/mtproxy" ]; then
    echo "🔄 Updating main executable..."
    sudo cp "$INSTALL_DIR/mtproxy.py" "$INSTALL_DIR/mtproxy"
    sudo chmod +x "$INSTALL_DIR/mtproxy"
fi

# Create symlink if needed
if [ ! -f "/usr/local/bin/mtproxy" ]; then
    ln -sf "$INSTALL_DIR/mtproxy.py" "/usr/local/bin/mtproxy"
fi

# Restart service if running
if systemctl is-active --quiet mtprotoproxy; then
    echo "🔄 Restarting proxy service..."
    systemctl restart mtprotoproxy
fi

echo "✅ Update completed successfully!"
echo "📊 New features:"
echo "   • Online/offline user statistics"
echo "   • Real-time connection monitoring"
echo ""
echo "Run 'mtproxy' to see the new features!"
