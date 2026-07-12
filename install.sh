#!/usr/bin/env bash
set -e

APP_DIR="/opt/mtproto-proxy-manager"
REPO_URL="https://github.com/Mahersaber2024/MTProxy-Advanced-.git"
SERVICE_USER="root"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'

echo -e "${BOLD}${CYAN}🚀 Installing MTProxy Manager...${NC}"
echo ""

# ============================================
# Install prerequisites
# ============================================
export DEBIAN_FRONTEND=noninteractive
apt update
apt install -y git python3 python3-pip curl wget xxd figlet

# ============================================
# Clone or update the project
# ============================================
if [ ! -d "$APP_DIR/.git" ]; then
  rm -rf "$APP_DIR"
  git clone --depth 1 "$REPO_URL" "$APP_DIR" || {
    echo -e "${RED}❌ Git clone failed. Check repository URL.${NC}"
    exit 1
  }
else
  cd "$APP_DIR"
  git pull || {
    echo -e "${RED}❌ Git pull failed.${NC}"
    exit 1
  }
fi

cd "$APP_DIR"

# ============================================
# Install Python dependencies
# ============================================
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"

if pip3 install --break-system-packages requests python-dotenv 2>/dev/null; then
  echo -e "${GREEN}✅ Installed with --break-system-packages${NC}"
else
  echo -e "${YELLOW}⚠️ --break-system-packages not supported, using --user...${NC}"
  pip3 install --user requests python-dotenv
fi

# ============================================
# Install management scripts
# ============================================
echo -e "${BLUE}📋 Installing management script...${NC}"

# کپی هر دو فایل اصلی و ماژول آمار
cp -f mtproxy.py /usr/local/bin/mtproxy
cp -f mtproxy_stats.py /usr/local/bin/mtproxy_stats.py

sed -i 's/\r$//' /usr/local/bin/mtproxy
sed -i 's/\r$//' /usr/local/bin/mtproxy_stats.py

chmod +x /usr/local/bin/mtproxy
chmod +x /usr/local/bin/mtproxy_stats.py

# اضافه کردن مسیر پروژه به PYTHONPATH برای اطمینان کامل
echo "export PYTHONPATH=\"\$PYTHONPATH:$APP_DIR\"" > /etc/profile.d/mtproxy.sh
chmod +x /etc/profile.d/mtproxy.sh

# ============================================
# Create config directory
# ============================================
mkdir -p /etc/mtpulse

# ============================================
# Run the script to install the proxy automatically
# ============================================
echo -e "${BLUE}🔧 Setting up MTProto Proxy...${NC}"
python3 /usr/local/bin/mtproxy --setup

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║         ${BOLD}✅ INSTALLATION COMPLETED SUCCESSFULLY${NC}${CYAN}         ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}${PURPLE}🎮 HOW TO RUN${NC}"
echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"
echo -e "  ${YELLOW}Just type:${NC} ${BOLD}${WHITE}mtproxy${NC}"
echo ""
echo -e "${GREEN}${BOLD}🎯 Quick Start:${NC} Just run ${BOLD}mtproxy${NC} to start managing your proxies!${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
