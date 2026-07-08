#!/usr/bin/env python3
# mtpulse.py - MTPulse MTProto Proxy Manager (Multi-Proxy Support) - Fixed Version

import os
import sys
import subprocess
import json
import time
import shutil
import re
from pathlib import Path

# ========== Settings ==========
VERSION = "2.2.2"  # Updated version
SPONSOR_NAME = "HeySolo"
SPONSOR_LINK = "https://t.me/HeySoloATM"
CONTACT = "@jadetunnel"
BINARY_PATH = "/usr/local/bin/mtproto-proxy"
CONFIG_DIR = "/etc/mtpulse"
CONFIG_FILE = f"{CONFIG_DIR}/proxies.json"
SECRET_FILE = f"{CONFIG_DIR}/proxy-secret"
MULTI_FILE = f"{CONFIG_DIR}/proxy-multi.conf"
TEST_SCRIPT = "/usr/local/bin/test_proxy.py"
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
    print(f"{Colors.CYAN}{Colors.BOLD}║              MTProto Proxy Manager  -  v{VERSION} (Multi-Proxy)      ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}╚═══════════════════════════════════════════════════════════════════════╝{Colors.NC}")
    print("")
    print(f"{Colors.PURPLE}{Colors.BOLD}🌟 Sponsored by: {SPONSOR_NAME}{Colors.NC}")
    print(f"{Colors.PURPLE}🔗 {SPONSOR_LINK}{Colors.NC}")
    print(f"{Colors.PURPLE}📩 Contact: {CONTACT}{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print("")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"proxies": {}}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"proxies": {}}

def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def generate_secret(domain="www.google.com"):
    """
    Generate a Fake TLS secret for MTProto proxy.
    """
    key_bytes = subprocess.run(['head', '-c', '16', '/dev/urandom'], capture_output=True).stdout
    key_hex = subprocess.run(['xxd', '-ps'], input=key_bytes, capture_output=True).stdout.decode().strip()
    
    domain_hex = domain.encode('utf-8').hex()
    secret = f"ee{key_hex}{domain_hex}"
    return secret

def get_public_ip():
    try:
        ip = subprocess.run(['curl', '-s', '--max-time', '3', 'https://api.ipify.org'], 
                           capture_output=True, text=True).stdout.strip()
        if ip:
            return ip
    except:
        pass
    return "Unknown"

def get_proxy_status(proxy_id):
    service_name = f"mtpulse-{proxy_id}"
    if not os.path.exists(f"/etc/systemd/system/{service_name}.service"):
        return "not_installed"
    result = subprocess.run(['systemctl', 'is-active', service_name], 
                           capture_output=True, text=True)
    return "active" if result.stdout.strip() == "active" else "inactive"

def get_proxy_link(proxy):
    ip = proxy.get('ip')
    port = proxy.get('port')
    secret = proxy.get('secret')
    return f"tg://proxy?server={ip}&port={port}&secret={secret}"

def list_proxies(config, show_status=True, show_links=False):
    proxies = config.get('proxies', {})
    if not proxies:
        print(f"{Colors.YELLOW}⚠️ No proxies configured.{Colors.NC}")
        return [], []
    
    print(f"{Colors.BLUE}📋 Available Proxies:{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    ids = []
    labels = []
    for idx, (proxy_id, proxy) in enumerate(proxies.items(), 1):
        ids.append(proxy_id)
        name = proxy.get('name', 'Unnamed')
        ip = proxy.get('ip', '?')
        port = proxy.get('port', '?')
        
        status = get_proxy_status(proxy_id)
        if status == "active":
            status_text = f"{Colors.GREEN}● Active{Colors.NC}"
        elif status == "inactive":
            status_text = f"{Colors.RED}● Inactive{Colors.NC}"
        else:
            status_text = f"{Colors.YELLOW}● Not installed{Colors.NC}"
        
        tag = proxy.get('tag')
        tag_text = f" 🏷️ {Colors.MAGENTA}{tag}{Colors.NC}" if tag else ""
        
        label = f"{idx}. {Colors.BOLD}{name}{Colors.NC} | {ip}:{port} | {status_text}{tag_text}"
        labels.append(label)
        print(f"  {label}")
        
        if show_links and status == "active":
            link = get_proxy_link(proxy)
            print(f"     {Colors.CYAN}🔗 {link}{Colors.NC}")
    
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    return ids, labels

def create_service_file(proxy_id, proxy):
    """Fixed: Use same port for internal and external listening"""
    ip = proxy.get('ip')
    port = proxy.get('port')
    secret = proxy.get('secret')
    tag = proxy.get('tag')
    name = proxy.get('name', proxy_id)
    
    # Extract key from Fake TLS secret
    if secret.startswith('ee') and len(secret) >= 34:
        key = secret[2:34]
    else:
        key = secret
    
    # Fixed command - same port for -p and -H
    exec_start = f"{BINARY_PATH} -u nobody -p {port} -H {port} -S {key} --aes-pwd {SECRET_FILE} {MULTI_FILE} -M 1"
    if tag:
        exec_start += f" -P {tag}"
    
    service_content = f"""[Unit]
Description=MTPulse MTProto Proxy - {name} ({ip}:{port})
After=network.target

[Service]
ExecStart={exec_start}
Restart=always
User=root
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
"""
    
    service_path = f"/etc/systemd/system/mtpulse-{proxy_id}.service"
    with open(service_path, 'w') as f:
        f.write(service_content)
    
    subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=False)

def ensure_binary_installed():
    if os.path.exists(BINARY_PATH):
        return True
    
    print(f"{Colors.CYAN}📥 MTProto Proxy binary not found. Compiling from source...{Colors.NC}")
    
    if os.path.exists("MTProxy"):
        shutil.rmtree("MTProxy")
    
    clone = subprocess.run(['git', 'clone', '--depth=1', 'https://github.com/TelegramMessenger/MTProxy.git'],
                          capture_output=True, text=True)
    if clone.returncode != 0:
        print(f"{Colors.RED}❌ Failed to clone repository.{Colors.NC}")
        return False
    
    os.chdir("MTProxy")
    
    if os.path.exists("common/pid.c"):
        subprocess.run(["sed", "-i", 's/assert (!(p & 0xffff0000));/\\/\\/ assert (!(p \\& 0xffff0000));/g', "common/pid.c"], check=False)
    
    print(f"{Colors.CYAN}Compiling...{Colors.NC}")
    compile_result = subprocess.run(['make'], capture_output=True, text=True)
    
    if compile_result.returncode != 0 or not os.path.exists("objs/bin/mtproto-proxy"):
        print(f"{Colors.RED}❌ Compilation failed.{Colors.NC}")
        print(compile_result.stderr[-500:])
        os.chdir("..")
        return False
    
    subprocess.run(['sudo', 'cp', 'objs/bin/mtproto-proxy', BINARY_PATH], check=False)
    subprocess.run(['sudo', 'chmod', '+x', BINARY_PATH], check=False)
    os.chdir("..")
    shutil.rmtree("MTProxy")
    
    os.makedirs(CONFIG_DIR, exist_ok=True)
    subprocess.run(['sudo', 'curl', '-s', 'https://core.telegram.org/getProxySecret', '-o', SECRET_FILE], check=False)
    subprocess.run(['sudo', 'curl', '-s', 'https://core.telegram.org/getProxyConfig', '-o', MULTI_FILE], check=False)
    
    print(f"{Colors.GREEN}✅ Binary installed successfully.{Colors.NC}")
    return True

def add_proxy():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}➕ Add New Proxy{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    if not ensure_binary_installed():
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    
    config = load_config()
    proxies = config.get('proxies', {})
    
    name = input(f"{Colors.BOLD}{Colors.PURPLE}Enter proxy name (e.g. Main, Backup): {Colors.NC}").strip()
    if not name:
        name = f"Proxy-{len(proxies)+1}"
    
    while True:
        ip = input(f"{Colors.BOLD}{Colors.PURPLE}Enter IP address or domain: {Colors.NC}").strip()
        if ip:
            break
        print(f"{Colors.RED}❌ IP/Domain cannot be empty.{Colors.NC}")
    
    while True:
        port = input(f"{Colors.BOLD}{Colors.PURPLE}Enter port (recommended 443): {Colors.NC}").strip()
        if not port:
            port = "443"
        if port.isdigit() and 1 <= int(port) <= 65535:
            # Check for existing port
            existing = [p for p in proxies if proxies[p].get('port') == port]
            if existing:
                print(f"{Colors.YELLOW}⚠️ Port {port} is already used.{Colors.NC}")
                cont = input(f"{Colors.PURPLE}Continue anyway? (y/N): {Colors.NC}").strip().lower()
                if cont != 'y':
                    continue
            break
        else:
            print(f"{Colors.RED}❌ Invalid port.{Colors.NC}")
    
    print(f"\n{Colors.CYAN}ℹ️  Fake TLS is recommended.{Colors.NC}")
    domain = input(f"{Colors.BOLD}{Colors.PURPLE}Enter domain for Fake TLS (default www.google.com): {Colors.NC}").strip()
    if not domain:
        domain = "www.google.com"
    
    secret = generate_secret(domain)
    print(f"{Colors.CYAN}Generated Secret: {Colors.WHITE}{secret}{Colors.NC}")
    
    proxy_id = f"p{str(len(proxies)+1)}"
    
    proxy = {
        "name": name,
        "ip": ip,
        "port": port,
        "secret": secret,
        "tag": None
    }
    
    proxies[proxy_id] = proxy
    config['proxies'] = proxies
    save_config(config)
    
    create_service_file(proxy_id, proxy)
    subprocess.run(['sudo', 'systemctl', 'enable', f'mtpulse-{proxy_id}'], check=False)
    subprocess.run(['sudo', 'systemctl', 'start', f'mtpulse-{proxy_id}'], check=False)
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"{Colors.GREEN}{Colors.BOLD}     🚀 Proxy Added Successfully!{Colors.NC}")
    print(f"{Colors.GREEN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"Name:   {Colors.WHITE}{name}{Colors.NC}")
    print(f"IP:     {Colors.WHITE}{ip}{Colors.NC}")
    print(f"Port:   {Colors.WHITE}{port}{Colors.NC}")
    print(f"Secret: {Colors.WHITE}{secret}{Colors.NC}")
    print(f"Domain: {Colors.WHITE}{domain}{Colors.NC}")
    print(f"\n{Colors.BOLD}{Colors.CYAN}tg://proxy?server={ip}&port={port}&secret={secret}{Colors.NC}\n")
    
    public_ip = get_public_ip()
    if public_ip and public_ip != ip:
        print(f"{Colors.YELLOW}💡 Your public IP: {public_ip}{Colors.NC}")
    
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")

# Other functions (remove_proxy, tag_proxy, service_menu, etc.) remain the same
# (برای صرفه‌جویی در فضا، بقیه توابع بدون تغییر نگه داشته شده‌اند)

def remove_proxy():
    # ... (same as original)
    pass  # Copy from your original code if needed

def tag_proxy():
    # ... (same)
    pass

def service_menu():
    # ... (same)
    pass

def test_proxy_menu():
    # ... (same)
    pass

def uninstall():
    # ... (same)
    pass

def main():
    while True:
        print_header()
        
        config = load_config()
        proxies = config.get('proxies', {})
        proxy_count = len(proxies)
        
        print(f"{Colors.BLUE}📊 Status:{Colors.NC}")
        if proxy_count == 0:
            print(f"  {Colors.YELLOW}●{Colors.NC} Proxies: {Colors.YELLOW}None configured{Colors.NC}")
        else:
            active = sum(1 for pid in proxies if get_proxy_status(pid) == "active")
            print(f"  {Colors.GREEN}●{Colors.NC} Proxies: {Colors.WHITE}{proxy_count}{Colors.NC} ({Colors.GREEN}{active}{Colors.NC} active, {Colors.RED}{proxy_count-active}{Colors.NC} inactive)")
            print("")
            list_proxies(config, show_status=True, show_links=True)
        
        print("")
        print(f"{Colors.BLUE}📋 Menu:{Colors.NC}")
        print(f"  {Colors.GREEN}1.{Colors.NC} ➕ Add Proxy")
        print(f"  {Colors.GREEN}2.{Colors.NC} ⚙️ Service Management")
        print(f"  {Colors.GREEN}3.{Colors.NC} 📝 Add Tag to Proxy")
        print(f"  {Colors.GREEN}4.{Colors.NC} ➖ Remove Proxy")
        print(f"  {Colors.GREEN}5.{Colors.NC} 🔍 Test Proxy")
        print(f"  {Colors.GREEN}6.{Colors.NC} 🗑️ Uninstall MTPulse")
        print(f"  {Colors.GREEN}0.{Colors.NC} 🚪 Exit")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        choice = input(f"{Colors.BOLD}{Colors.PURPLE}Select an option: {Colors.NC}").strip()
        
        if choice == '1':
            add_proxy()
        elif choice == '2':
            service_menu()
        elif choice == '3':
            tag_proxy()
        elif choice == '4':
            remove_proxy()
        elif choice == '5':
            test_proxy_menu()
        elif choice == '6':
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
