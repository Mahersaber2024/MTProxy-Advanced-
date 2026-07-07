#!/usr/bin/env bash
set -e

APP_DIR="/opt/mtpulse-proxy"
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
apt install -y git python3 python3-venv python3-pip curl wget xxd figlet make build-essential libssl-dev zlib1g-dev

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
# Create virtual environment
# ============================================
echo -e "${BLUE}🐍 Creating virtual environment...${NC}"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

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
echo -e "${BOLD}${GREEN}📋 Features:${NC}"
echo -e "  ${WHITE}•${NC} Add multiple proxies with custom IP/Domain and port"
echo -e "  ${WHITE}•${NC} Default port: 80"
echo -e "  ${WHITE}•${NC} Each proxy can have its own sponsor tag"
echo -e "  ${WHITE}•${NC} Manage each proxy individually"
echo ""
echo -e "${GREEN}${BOLD}🎯 Quick Start:${NC} Just run ${BOLD}mtpulse${NC} to start managing your proxies!${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
