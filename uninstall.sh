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

echo -e "${BOLD}${CYAN}🚀 Installing MTPulse Proxy Manager...${NC}"
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
# Install Python dependencies with --break-system-packages
# ============================================
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip3 install --break-system-packages requests python-dotenv

# ============================================
# Install management script
# ============================================
echo -e "${BLUE}📋 Installing management script...${NC}"
cp -f mtpulse.py /usr/local/bin/mtpulse
chmod +x /usr/local/bin/mtpulse

# ============================================
# Create config directory
# ============================================
mkdir -p /etc/mtpulse

# ============================================
# Run the script to install the proxy automatically
# ============================================
echo -e "${BLUE}🔧 Setting up MTProto Proxy...${NC}"
python3 /usr/local/bin/mtpulse --setup

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║         ${BOLD}✅ INSTALLATION COMPLETED SUCCESSFULLY${NC}${CYAN}         ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}${PURPLE}🎮 HOW TO RUN${NC}"
echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"
echo -e "  ${YELLOW}Just type:${NC} ${BOLD}${WHITE}mtpulse${NC}"
echo ""
echo -e "${GREEN}${BOLD}🎯 Quick Start:${NC} Just run ${BOLD}mtpulse${NC} to start managing your proxies!${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
