#!/usr/bin/env bash
set -e

APP_DIR="/opt/mtpulse-proxy"
REPO_URL="https://github.com/Mahersaber2024/MTProxy-Advanced-.git"
SERVICE_NAME="mtpulse"
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
# Create systemd service placeholder
# ============================================
cat > /etc/systemd/system/mtpulse.service <<EOF
[Unit]
Description=MTPulse MTProto Proxy Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/mtproto-proxy -u nobody -p 8888 -H 443 -S YOUR_SECRET --aes-pwd /etc/mtpulse/proxy-secret /etc/mtpulse/proxy-multi.conf -M 1
Restart=always
User=root
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

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
echo -e "${GREEN}${BOLD}🎯 Quick Start:${NC} Just run ${BOLD}mtpulse${NC} to start managing your MTProto proxy!${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
