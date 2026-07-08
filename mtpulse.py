#!/usr/bin/env python3
# mtpulse.py - MTPulse MTProto Proxy Manager (Python Version)

import os
import sys
import subprocess
import json
import time
import shutil
import re
from pathlib import Path

# ========== Settings ==========
VERSION = "3.2.0"
SPONSOR_NAME = "HeySolo"
SPONSOR_LINK = "https://t.me/HeySoloATM"
CONTACT = "@jadetunnel"
PROXY_DIR = "/opt/mtprotoproxy"
CONFIG_FILE = f"{PROXY_DIR}/config.py"
CONFIG_DIR = "/etc/mtpulse"
PROXIES_FILE = f"{CONFIG_DIR}/proxies.json"
SETTINGS_FILE = f"{CONFIG_DIR}/settings.json"
SERVICE_NAME = "mtprotoproxy"
# ===============================

# Colors (ANSI escape codes)
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    MAGENTA = PURPLE
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'
    BOLD = '\033[1m'

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_header():
    clear_screen()
    print(f"{Colors.CYAN}{Colors.BOLD}╔═══════════════════════════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ███╗   ███╗████████╗██████╗ ██╗   ██╗██╗     ███████╗███████╗  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ████╗ ████║╚══██╔══╝██╔══██╗╚██╗ ██╔╝██║     ██╔════╝██╔════╝  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ██╔████╔██║   ██║   ██████╔╝ ╚████╔╝ ██║     █████╗  ███████╗  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ██║╚██╔╝██║   ██║   ██╔═══╝   ╚██╔╝  ██║     ██╔══╝  ╚════██║  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ██║ ╚═╝ ██║   ██║   ██║        ██║   ███████╗███████╗███████║  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ╚═╝     ╚═╝   ╚═╝   ╚═╝        ╚═╝   ╚══════╝╚══════╝╚══════╝  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║                                                                     ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║              MTProto Proxy Manager  -  v{VERSION} (Python)           ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║                   (Multi-Proxy per IP/Domain)                      ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}╚═══════════════════════════════════════════════════════════════════════╝{Colors.NC}")
    print("")
    print(f"{Colors.PURPLE}{Colors.BOLD}🌟 Sponsored by: {SPONSOR_NAME}{Colors.NC}")
    print(f"{Colors.PURPLE}🔗 {SPONSOR_LINK}{Colors.NC}")
    print(f"{Colors.PURPLE}📩 Contact: {CONTACT}{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print("")

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"default_server": "", "default_port": "443", "default_domain": "www.google.com"}
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"default_server": "", "default_port": "443", "default_domain": "www.google.com"}

def save_settings(settings):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def get_default_server():
    settings = load_settings()
    return settings.get('default_server', '')

def get_default_port():
    settings = load_settings()
    return settings.get('default_port', '443')

def get_default_domain():
    settings = load_settings()
    return settings.get('default_domain', 'www.google.com')

def set_default_server(address):
    settings = load_settings()
    settings['default_server'] = address.strip()
    save_settings(settings)

def get_public_ip():
    try:
        ip = subprocess.run(['curl', '-s', '--max-time', '2', 'https://api.ipify.org'], 
                           capture_output=True, text=True).stdout.strip()
        if ip:
            return ip
    except:
        pass
    return "Unknown"

def load_proxies():
    if not os.path.exists(PROXIES_FILE):
        return {"proxies": {}}
    try:
        with open(PROXIES_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"proxies": {}}

def save_proxies(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(PROXIES_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def generate_secret():
    key_bytes = subprocess.run(['head', '-c', '16', '/dev/urandom'], capture_output=True).stdout
    return subprocess.run(['xxd', '-ps'], input=key_bytes, capture_output=True).stdout.decode().strip()

def get_proxy_status():
    if not os.path.exists(f"/etc/systemd/system/{SERVICE_NAME}.service"):
        return "not_installed"
    result = subprocess.run(['systemctl', 'is-active', SERVICE_NAME], 
                           capture_output=True, text=True)
    return "active" if result.stdout.strip() == "active" else "inactive"

def get_proxy_link(proxy):
    """Generate tg:// link using proxy's own server/port or defaults"""
    server = proxy.get('server', '')
    if not server:
        server = get_default_server()
        if not server:
            server = get_public_ip()
    
    port = proxy.get('port', '')
    if not port:
        port = get_default_port()
    
    domain = proxy.get('domain', '')
    if not domain:
        domain = get_default_domain()
    
    secret = proxy.get('secret')
    full_secret = f"ee{secret}{domain.encode().hex()}"
    return f"tg://proxy?server={server}&port={port}&secret={full_secret}"

def list_proxies():
    config = load_proxies()
    proxies = config.get('proxies', {})
    if not proxies:
        print(f"{Colors.YELLOW}⚠️ No proxies configured.{Colors.NC}")
        return [], []
    
    print(f"{Colors.BLUE}📋 Available Proxies:{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    ids = []
    labels = []
    status = get_proxy_status()
    for idx, (proxy_id, proxy) in enumerate(proxies.items(), 1):
        ids.append(proxy_id)
        name = proxy.get('name', 'Unnamed')
        server = proxy.get('server', 'default')
        port = proxy.get('port', 'default')
        secret = proxy.get('secret', '?')
        tag = proxy.get('tag')
        
        status_text = f"{Colors.GREEN}● Active{Colors.NC}" if status == "active" else f"{Colors.RED}● Inactive{Colors.NC}"
        tag_text = f" 🏷️ {Colors.MAGENTA}{tag}{Colors.NC}" if tag else ""
        server_text = f"@ {server}:{port}" if server != 'default' else ""
        
        secret_short = secret[:8] + "..." if len(secret) > 8 else secret
        label = f"{idx}. {Colors.BOLD}{name}{Colors.NC} | {server_text} | Secret: {secret_short} | {status_text}{tag_text}"
        labels.append(label)
        print(f"  {label}")
        
        if status == "active":
            link = get_proxy_link(proxy)
            print(f"     {Colors.CYAN}🔗 {link}{Colors.NC}")
    
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    return ids, labels

def install_proxy():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}📥 Install MTProto Proxy (Python){Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print("")
    
    print(f"{Colors.CYAN}📦 Installing dependencies...{Colors.NC}")
    subprocess.run(['apt-get', 'update', '-qq'], check=False)
    subprocess.run(['apt-get', 'install', '-y', 'python3', 'python3-pip', 'git', 'curl', 'jq', 'ca-certificates'], check=False)
    subprocess.run(['pip3', 'install', 'cryptography', 'uvloop'], check=False)
    
    if os.path.exists(PROXY_DIR):
        shutil.rmtree(PROXY_DIR)
    
    print(f"{Colors.CYAN}📥 Cloning mtprotoproxy...{Colors.NC}")
    clone = subprocess.run(['git', 'clone', 'https://github.com/alexbers/mtprotoproxy.git', PROXY_DIR],
                          capture_output=True, text=True)
    if clone.returncode != 0:
        print(f"{Colors.RED}❌ Failed to clone repository.{Colors.NC}")
        return False
    
    # Get default config
    port = input(f"{Colors.BOLD}{Colors.PURPLE}Enter default port (default 443): {Colors.NC}").strip()
    if not port:
        port = "443"
    set_default_port(port)
    
    domain = input(f"{Colors.BOLD}{Colors.PURPLE}Enter default TLS domain (default www.google.com): {Colors.NC}").strip()
    if not domain:
        domain = "www.google.com"
    set_default_domain(domain)
    
    server_addr = input(f"{Colors.BOLD}{Colors.PURPLE}Enter default server IP/domain (leave empty for auto-detect): {Colors.NC}").strip()
    if server_addr:
        set_default_server(server_addr)
        print(f"{Colors.GREEN}✅ Default server set to: {server_addr}{Colors.NC}")
    else:
        public_ip = get_public_ip()
        set_default_server(public_ip)
        print(f"{Colors.GREEN}✅ Auto-detected public IP: {public_ip}{Colors.NC}")
    
    # Create config
    config_py = f"""PORT = {port}
USERS = {{}}
TLS_DOMAIN = "{domain}"
MODES = {{ "classic": False, "secure": False, "tls": True }}
"""
    with open(f"{PROXY_DIR}/config.py", 'w') as f:
        f.write(config_py)
    
    # Create systemd service
    service_content = f"""[Unit]
Description=MTProto Proxy Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {PROXY_DIR}/mtprotoproxy.py
Restart=always
User=root
StartLimitBurst=0

[Install]
WantedBy=multi-user.target
"""
    with open("/etc/systemd/system/mtprotoproxy.service", 'w') as f:
        f.write(service_content)
    
    subprocess.run(['systemctl', 'daemon-reload'], check=False)
    subprocess.run(['systemctl', 'enable', SERVICE_NAME], check=False)
    subprocess.run(['systemctl', 'start', SERVICE_NAME], check=False)
    
    print(f"{Colors.GREEN}✅ MTProto Proxy installed successfully!{Colors.NC}")
    return True

def add_proxy():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}➕ Add New Proxy{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print("")
    
    if not os.path.exists(PROXY_DIR):
        print(f"{Colors.RED}❌ MTProto Proxy not installed. Please install first (option 1).{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    
    config = load_proxies()
    proxies = config.get('proxies', {})
    
    name = input(f"{Colors.BOLD}{Colors.PURPLE}Enter proxy name (e.g. US, EU, Main): {Colors.NC}").strip()
    if not name:
        name = f"Proxy-{len(proxies)+1}"
    
    # Server address (optional)
    print("")
    print(f"{Colors.CYAN}ℹ️  Leave empty to use default server address{Colors.NC}")
    server = input(f"{Colors.BOLD}{Colors.PURPLE}Enter server IP/domain for this proxy: {Colors.NC}").strip()
    
    # Port (optional)
    if server:
        port = input(f"{Colors.BOLD}{Colors.PURPLE}Enter port for this proxy (default: {get_default_port()}): {Colors.NC}").strip()
        if not port:
            port = ""
    else:
        port = ""
    
    # Domain (optional)
    domain = input(f"{Colors.BOLD}{Colors.PURPLE}Enter TLS domain for this proxy (default: {get_default_domain()}): {Colors.NC}").strip()
    if not domain:
        domain = ""
    
    secret = generate_secret()
    print(f"{Colors.CYAN}Generated Secret: {Colors.WHITE}{secret}{Colors.NC}")
    
    tag = input(f"{Colors.BOLD}{Colors.PURPLE}Enter AD Tag (optional, press Enter to skip): {Colors.NC}").strip()
    
    proxy_id = f"p{str(len(proxies)+1)}"
    proxy = {
        "name": name,
        "secret": secret,
        "server": server,
        "port": port,
        "domain": domain,
        "tag": tag if tag else None
    }
    proxies[proxy_id] = proxy
    config['proxies'] = proxies
    save_proxies(config)
    
    # Update config.py
    with open(f"{PROXY_DIR}/config.py", 'r') as f:
        content = f.read()
    
    users_match = re.search(r'USERS\s*=\s*\{([^}]*)\}', content, re.DOTALL)
    if users_match:
        users_str = users_match.group(1).strip()
        if users_str and not users_str.endswith(','):
            users_str += ','
        new_users = f'{users_str}"{name}": "{secret}"'
    else:
        new_users = f'"{name}": "{secret}"'
    
    tag_line = f'\nAD_TAG = "{tag}"' if tag else ''
    
    new_content = re.sub(r'USERS\s*=\s*\{[^}]*\}', f'USERS = {{{new_users}}}', content)
    if tag and 'AD_TAG' not in new_content:
        new_content = new_content.replace('MODES', f'{tag_line}\nMODES')
    elif tag and 'AD_TAG' in new_content:
        new_content = re.sub(r'AD_TAG\s*=\s*"[^"]*"', f'AD_TAG = "{tag}"', new_content)
    
    with open(f"{PROXY_DIR}/config.py", 'w') as f:
        f.write(new_content)
    
    subprocess.run(['systemctl', 'restart', SERVICE_NAME], check=False)
    
    link = get_proxy_link(proxy)
    
    print("")
    print(f"{Colors.GREEN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"{Colors.GREEN}{Colors.BOLD}     🚀 Proxy Added Successfully!{Colors.NC}")
    print(f"{Colors.GREEN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"Name:   {Colors.WHITE}{name}{Colors.NC}")
    print(f"Server: {Colors.WHITE}{server if server else '(default)'}{Colors.NC}")
    print(f"Port:   {Colors.WHITE}{port if port else '(default)'}{Colors.NC}")
    print(f"Secret: {Colors.WHITE}{secret}{Colors.NC}")
    if tag:
        print(f"Tag:    {Colors.WHITE}{tag}{Colors.NC}")
    print("")
    print(f"{Colors.BOLD}{Colors.CYAN}{link}{Colors.NC}")
    print("")
    
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")

def remove_proxy():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.RED}➖ Remove Proxy{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    config = load_proxies()
    proxies = config.get('proxies', {})
    
    if not proxies:
        print(f"{Colors.YELLOW}⚠️ No proxies configured.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    
    ids, labels = list_proxies()
    print("")
    print(f"{Colors.RED}⚠️ Select a proxy to REMOVE:{Colors.NC}")
    
    try:
        choice = int(input(f"{Colors.BOLD}{Colors.PURPLE}Enter number (1-{len(ids)}): {Colors.NC}").strip())
        if choice < 1 or choice > len(ids):
            print(f"{Colors.RED}❌ Invalid selection.{Colors.NC}")
            input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
            return
    except ValueError:
        print(f"{Colors.RED}❌ Invalid input.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    
    proxy_id = ids[choice - 1]
    proxy = proxies[proxy_id]
    name = proxy.get('name')
    
    confirm = input(f"{Colors.RED}Remove '{name}'? (y/N): {Colors.NC}")
    if confirm.lower() != 'y':
        print(f"{Colors.YELLOW}Cancelled.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    
    with open(f"{PROXY_DIR}/config.py", 'r') as f:
        content = f.read()
    
    new_content = re.sub(rf'"{name}"\s*:\s*"[^"]*",?\s*', '', content)
    new_content = re.sub(r'USERS\s*=\s*\{\s*,?\s*\}', 'USERS = {}', new_content)
    
    with open(f"{PROXY_DIR}/config.py", 'w') as f:
        f.write(new_content)
    
    del proxies[proxy_id]
    config['proxies'] = proxies
    save_proxies(config)
    
    subprocess.run(['systemctl', 'restart', SERVICE_NAME], check=False)
    
    print(f"{Colors.GREEN}✅ Proxy '{name}' removed successfully!{Colors.NC}")
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")

def tag_proxy():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}📝 Add Tag to Proxy{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print(f"{Colors.YELLOW}ℹ️  Get AD Tag from @MTProxybot on Telegram{Colors.NC}")
    print("")
    
    config = load_proxies()
    proxies = config.get('proxies', {})
    
    if not proxies:
        print(f"{Colors.YELLOW}⚠️ No proxies configured.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    
    ids, labels = list_proxies()
    print("")
    
    try:
        choice = int(input(f"{Colors.BOLD}{Colors.PURPLE}Select proxy (1-{len(ids)}): {Colors.NC}").strip())
        if choice < 1 or choice > len(ids):
            print(f"{Colors.RED}❌ Invalid selection.{Colors.NC}")
            input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
            return
    except ValueError:
        print(f"{Colors.RED}❌ Invalid input.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    
    proxy_id = ids[choice - 1]
    proxy = proxies[proxy_id]
    
    current_tag = proxy.get('tag')
    if current_tag:
        print(f"{Colors.YELLOW}Current Tag: {Colors.WHITE}{current_tag}{Colors.NC}")
        response = input(f"{Colors.BOLD}{Colors.PURPLE}Remove and set new one? (y/N): {Colors.NC}")
        if response.lower() not in ['y', 'yes']:
            return
    
    new_tag = input(f"{Colors.BOLD}{Colors.PURPLE}Enter new AD Tag (leave empty to remove): {Colors.NC}").strip()
    
    if new_tag:
        proxy['tag'] = new_tag
        with open(f"{PROXY_DIR}/config.py", 'r') as f:
            content = f.read()
        if 'AD_TAG' in content:
            content = re.sub(r'AD_TAG\s*=\s*"[^"]*"', f'AD_TAG = "{new_tag}"', content)
        else:
            content = content.replace('MODES', f'AD_TAG = "{new_tag}"\nMODES')
        with open(f"{PROXY_DIR}/config.py", 'w') as f:
            f.write(content)
        print(f"{Colors.GREEN}✅ Tag updated to: {new_tag}{Colors.NC}")
    else:
        proxy['tag'] = None
        with open(f"{PROXY_DIR}/config.py", 'r') as f:
            content = f.read()
        content = re.sub(r'AD_TAG\s*=\s*"[^"]*"\s*', '', content)
        with open(f"{PROXY_DIR}/config.py", 'w') as f:
            f.write(content)
        print(f"{Colors.GREEN}✅ Tag removed.{Colors.NC}")
    
    proxies[proxy_id] = proxy
    save_proxies(load_proxies())
    
    subprocess.run(['systemctl', 'restart', SERVICE_NAME], check=False)
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")

def set_default_server_menu():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}🌐 Set Default Server Address{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print("")
    
    current = get_default_server()
    if current:
        print(f"{Colors.YELLOW}Current default: {Colors.WHITE}{current}{Colors.NC}")
    else:
        public_ip = get_public_ip()
        print(f"{Colors.YELLOW}Auto-detected public IP: {Colors.WHITE}{public_ip}{Colors.NC}")
    
    print(f"{Colors.CYAN}Default port: {Colors.WHITE}{get_default_port()}{Colors.NC}")
    print(f"{Colors.CYAN}Default domain: {Colors.WHITE}{get_default_domain()}{Colors.NC}")
    print("")
    print(f"{Colors.CYAN}ℹ️  This is used when a proxy doesn't have its own server/port/domain.{Colors.NC}")
    print("")
    
    new_addr = input(f"{Colors.BOLD}{Colors.PURPLE}Enter default server IP/domain (leave empty to auto-detect): {Colors.NC}").strip()
    if new_addr:
        set_default_server(new_addr)
        print(f"{Colors.GREEN}✅ Default server set to: {new_addr}{Colors.NC}")
    else:
        public_ip = get_public_ip()
        set_default_server(public_ip)
        print(f"{Colors.GREEN}✅ Switched to auto-detected IP: {public_ip}{Colors.NC}")
    
    # Also allow changing default port/domain
    new_port = input(f"{Colors.BOLD}{Colors.PURPLE}Enter default port (current: {get_default_port()}): {Colors.NC}").strip()
    if new_port:
        settings = load_settings()
        settings['default_port'] = new_port
        save_settings(settings)
        print(f"{Colors.GREEN}✅ Default port set to: {new_port}{Colors.NC}")
    
    new_domain = input(f"{Colors.BOLD}{Colors.PURPLE}Enter default TLS domain (current: {get_default_domain()}): {Colors.NC}").strip()
    if new_domain:
        settings = load_settings()
        settings['default_domain'] = new_domain
        save_settings(settings)
        print(f"{Colors.GREEN}✅ Default domain set to: {new_domain}{Colors.NC}")
    
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")

def service_menu():
    while True:
        clear_screen()
        print(f"{Colors.BOLD}{Colors.GREEN}⚙️ Service Management{Colors.NC}")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        status = get_proxy_status()
        status_text = f"{Colors.GREEN}Active{Colors.NC}" if status == "active" else f"{Colors.RED}Inactive{Colors.NC}" if status == "inactive" else f"{Colors.YELLOW}Not installed{Colors.NC}"
        print(f"  Status: {status_text}")
        print("")
        print(f"  {Colors.GREEN}1.{Colors.NC} Start")
        print(f"  {Colors.GREEN}2.{Colors.NC} Stop")
        print(f"  {Colors.GREEN}3.{Colors.NC} Restart")
        print(f"  {Colors.GREEN}4.{Colors.NC} Status")
        print(f"  {Colors.GREEN}5.{Colors.NC} View Logs")
        print(f"  {Colors.GREEN}0.{Colors.NC} Back")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        choice = input(f"{Colors.BOLD}{Colors.PURPLE}Select option: {Colors.NC}").strip()
        
        if choice == '1':
            subprocess.run(['systemctl', 'start', SERVICE_NAME], check=False)
            print(f"{Colors.GREEN}✅ Started{Colors.NC}")
            time.sleep(1)
        elif choice == '2':
            subprocess.run(['systemctl', 'stop', SERVICE_NAME], check=False)
            print(f"{Colors.GREEN}✅ Stopped{Colors.NC}")
            time.sleep(1)
        elif choice == '3':
            subprocess.run(['systemctl', 'restart', SERVICE_NAME], check=False)
            print(f"{Colors.GREEN}✅ Restarted{Colors.NC}")
            time.sleep(1)
        elif choice == '4':
            subprocess.run(['systemctl', 'status', SERVICE_NAME], check=False)
            input(f"{Colors.YELLOW}Press Enter...{Colors.NC}")
        elif choice == '5':
            subprocess.run(['journalctl', '-u', SERVICE_NAME, '-n', '30', '--no-pager'], check=False)
            input(f"{Colors.YELLOW}Press Enter...{Colors.NC}")
        elif choice == '0':
            break
        else:
            print(f"{Colors.RED}❌ Invalid option{Colors.NC}")
            time.sleep(1)

def uninstall():
    clear_screen()
    print(f"{Colors.RED}⚠️ Are you sure you want to uninstall MTPulse? (y/N){Colors.NC}")
    confirm = input().strip().lower()
    if confirm != 'y':
        print(f"{Colors.YELLOW}Cancelled.{Colors.NC}")
        time.sleep(1)
        return
    
    subprocess.run(['systemctl', 'stop', SERVICE_NAME], check=False)
    subprocess.run(['systemctl', 'disable', SERVICE_NAME], check=False)
    subprocess.run(['rm', '-f', f'/etc/systemd/system/{SERVICE_NAME}.service'], check=False)
    subprocess.run(['systemctl', 'daemon-reload'], check=False)
    
    subprocess.run(['rm', '-rf', PROXY_DIR], check=False)
    subprocess.run(['rm', '-rf', CONFIG_DIR], check=False)
    subprocess.run(['rm', '-f', '/usr/local/bin/mtpulse'], check=False)
    
    print(f"{Colors.GREEN}✅ Uninstallation completed!{Colors.NC}")
    time.sleep(1)

def main():
    while True:
        print_header()
        
        status = get_proxy_status()
        config = load_proxies()
        proxy_count = len(config.get('proxies', {}))
        default_server = get_default_server()
        default_port = get_default_port()
        
        print(f"{Colors.BLUE}📊 Status:{Colors.NC}")
        if not os.path.exists(PROXY_DIR):
            print(f"  {Colors.YELLOW}●{Colors.NC} Proxy: {Colors.YELLOW}Not installed{Colors.NC}")
        elif status == "active":
            print(f"  {Colors.GREEN}●{Colors.NC} Proxy: {Colors.GREEN}Active{Colors.NC}")
            print(f"  {Colors.BLUE}●{Colors.NC} Default: {Colors.WHITE}{default_server if default_server else 'auto-detect'}:{default_port}{Colors.NC}")
        else:
            print(f"  {Colors.RED}●{Colors.NC} Proxy: {Colors.RED}Inactive{Colors.NC}")
        
        print(f"  {Colors.BLUE}●{Colors.NC} Proxies: {Colors.WHITE}{proxy_count}{Colors.NC}")
        
        if proxy_count > 0 and status == "active":
            print("")
            list_proxies()
        
        print("")
        print(f"{Colors.BLUE}📋 Menu:{Colors.NC}")
        print(f"  {Colors.GREEN}1.{Colors.NC} 📥 Install MTProto Proxy")
        print(f"  {Colors.GREEN}2.{Colors.NC} ➕ Add Proxy (with custom IP/domain)")
        print(f"  {Colors.GREEN}3.{Colors.NC} ⚙️ Service Management")
        print(f"  {Colors.GREEN}4.{Colors.NC} 📝 Add Tag to Proxy")
        print(f"  {Colors.GREEN}5.{Colors.NC} ➖ Remove Proxy")
        print(f"  {Colors.GREEN}6.{Colors.NC} 🌐 Set Default Server Settings")
        print(f"  {Colors.GREEN}7.{Colors.NC} 🗑️ Uninstall MTPulse")
        print(f"  {Colors.GREEN}0.{Colors.NC} 🚪 Exit")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        choice = input(f"{Colors.BOLD}{Colors.PURPLE}Select an option: {Colors.NC}").strip()
        
        if choice == '1':
            install_proxy()
        elif choice == '2':
            add_proxy()
        elif choice == '3':
            service_menu()
        elif choice == '4':
            tag_proxy()
        elif choice == '5':
            remove_proxy()
        elif choice == '6':
            set_default_server_menu()
        elif choice == '7':
            uninstall()
        elif choice == '0':
            print(f"{Colors.GREEN}👋 Goodbye!{Colors.NC}")
            sys.exit(0)
        else:
            print(f"{Colors.RED}❌ Invalid option{Colors.NC}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}👋 Goodbye!{Colors.NC}")
        sys.exit(0)
