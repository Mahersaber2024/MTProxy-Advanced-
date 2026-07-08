#!/usr/bin/env python3
# mtpulse.py - MTPulse MTProto Proxy Manager (Multi-Proxy Support)

import os
import sys
import subprocess
import json
import time
import shutil
import re
from pathlib import Path

# ========== Settings ==========
VERSION = "2.2.1"
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

def generate_secret(domain="google.com"):
    """
    Generate a Fake TLS secret for MTProto proxy.
    Format: ee + 16-byte random key (hex) + domain (hex)
    Example: ee2fbc0721b217c4b96ae56ca47ccc5b8a676f6f676c652e636f6d
    """
    # 1. Generate 16-byte random key (32 hex chars)
    key_bytes = subprocess.run(['head', '-c', '16', '/dev/urandom'], capture_output=True).stdout
    key_hex = subprocess.run(['xxd', '-ps'], input=key_bytes, capture_output=True).stdout.decode().strip()
    
    # 2. Encode domain to hex
    domain_hex = domain.encode('utf-8').hex()
    
    # 3. Build Fake TLS secret: ee + key + domain_hex
    secret = f"ee{key_hex}{domain_hex}"
    return secret

def get_public_ip():
    try:
        ip = subprocess.run(['curl', '-s', '--max-time', '2', 'https://api.ipify.org'], 
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
    ip = proxy.get('ip')
    port = proxy.get('port')
    secret = proxy.get('secret')          # Full secret (ee + key + domain_hex)
    tag = proxy.get('tag')
    name = proxy.get('name', proxy_id)
    
    # Extract the 16-byte key (32 hex chars) from the secret.
    # Format: ee + 32-char key + domain_hex
    if secret.startswith('ee') and len(secret) >= 34:
        key = secret[2:34]   # 32 characters: the actual secret key
    else:
        key = secret          # Fallback for plain secret (no domain)
    
    # Build the command line for mtproto-proxy
    exec_start = f"{BINARY_PATH} -u nobody -p 8888 -H {port} -S {key} --aes-pwd {SECRET_FILE} {MULTI_FILE} -M 1"
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
    print("")
    
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
        port = input(f"{Colors.BOLD}{Colors.PURPLE}Enter port (default 80): {Colors.NC}").strip()
        if not port:
            port = "80"
        if port.isdigit() and 1 <= int(port) <= 65535:
            existing = [p for p in proxies if proxies[p].get('port') == port]
            if existing:
                print(f"{Colors.YELLOW}⚠️ Port {port} is already used by proxy '{proxies[existing[0]].get('name', existing[0])}'.{Colors.NC}")
                cont = input(f"{Colors.PURPLE}Use another port? (Y/n): {Colors.NC}").strip()
                if cont.lower() in ['n', 'no']:
                    continue
            break
        else:
            print(f"{Colors.RED}❌ Invalid port.{Colors.NC}")
    
    print("")
    print(f"{Colors.CYAN}ℹ️  Fake TLS is recommended for better compatibility with Telegram clients.{Colors.NC}")
    domain = input(f"{Colors.BOLD}{Colors.PURPLE}Enter domain for Fake TLS (default google.com): {Colors.NC}").strip()
    if not domain:
        domain = "google.com"
    
    secret = generate_secret(domain)
    print(f"{Colors.CYAN}Generated Secret (Fake TLS): {Colors.WHITE}{secret}{Colors.NC}")
    print(f"{Colors.CYAN}   Using domain: {Colors.WHITE}{domain}{Colors.NC}")
    
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
    
    print("")
    print(f"{Colors.GREEN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"{Colors.GREEN}{Colors.BOLD}     🚀 Proxy Added Successfully!{Colors.NC}")
    print(f"{Colors.GREEN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"Name:   {Colors.WHITE}{name}{Colors.NC}")
    print(f"IP:     {Colors.WHITE}{ip}{Colors.NC}")
    print(f"Port:   {Colors.WHITE}{port}{Colors.NC}")
    print(f"Secret: {Colors.WHITE}{secret}{Colors.NC}")
    print(f"Domain: {Colors.WHITE}{domain}{Colors.NC}")
    print("")
    print(f"{Colors.BOLD}{Colors.CYAN}tg://proxy?server={ip}&port={port}&secret={secret}{Colors.NC}")
    print("")
    
    public_ip = get_public_ip()
    if public_ip and public_ip != ip:
        print(f"{Colors.YELLOW}💡 Your public IP is: {public_ip}{Colors.NC}")
        print(f"{Colors.YELLOW}   Use this if your server is behind NAT.{Colors.NC}")
        print("")
    
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")

def remove_proxy():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.RED}➖ Remove Proxy{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    config = load_config()
    proxies = config.get('proxies', {})
    
    if not proxies:
        print(f"{Colors.YELLOW}⚠️ No proxies configured.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    
    ids, labels = list_proxies(config, show_status=False)
    print("")
    print(f"{Colors.RED}⚠️ Select a proxy to REMOVE:{Colors.NC}")
    print(f"{Colors.YELLOW}   (This will stop the service and delete it){Colors.NC}")
    
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
    
    confirm = input(f"{Colors.RED}Are you sure you want to remove '{proxy.get('name', proxy_id)}'? (y/N): {Colors.NC}")
    if confirm.lower() != 'y':
        print(f"{Colors.YELLOW}Cancelled.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    
    service_name = f"mtpulse-{proxy_id}"
    subprocess.run(['sudo', 'systemctl', 'stop', service_name], check=False)
    subprocess.run(['sudo', 'systemctl', 'disable', service_name], check=False)
    subprocess.run(['sudo', 'rm', '-f', f'/etc/systemd/system/{service_name}.service'], check=False)
    subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=False)
    
    del proxies[proxy_id]
    config['proxies'] = proxies
    save_config(config)
    
    print(f"{Colors.GREEN}✅ Proxy '{proxy.get('name', proxy_id)}' removed successfully!{Colors.NC}")
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")

def tag_proxy():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}📝 Add Tag to Proxy{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    config = load_config()
    proxies = config.get('proxies', {})
    
    if not proxies:
        print(f"{Colors.YELLOW}⚠️ No proxies configured. Please add a proxy first.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    
    ids, labels = list_proxies(config, show_status=False)
    print("")
    
    try:
        choice = int(input(f"{Colors.BOLD}{Colors.PURPLE}Select proxy to tag (1-{len(ids)}): {Colors.NC}").strip())
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
        print(f"{Colors.YELLOW}Current Tag: {Colors.BOLD}{Colors.MAGENTA}{current_tag}{Colors.NC}")
        print("")
        response = input(f"{Colors.BOLD}{Colors.PURPLE}Remove current tag and set new one? (y/N): {Colors.NC}")
        if response.lower() not in ['y', 'yes']:
            return
    else:
        print(f"{Colors.YELLOW}Current Tag: {Colors.WHITE}None{Colors.NC}")
        print("")
    
    print(f"{Colors.YELLOW}ℹ️  To get an AD Tag, use the official Telegram bot:{Colors.NC} {Colors.BOLD}{Colors.BLUE}@MTProxybot{Colors.NC}")
    print(f"{Colors.YELLOW}    Register your proxy there and it will give you a 32-character hex tag.{Colors.NC}")
    print("")
    
    new_tag = input(f"{Colors.BOLD}{Colors.PURPLE}Enter new AD Tag (leave empty to remove): {Colors.NC}").strip()
    
    if new_tag:
        proxy['tag'] = new_tag
        print(f"{Colors.GREEN}✅ Tag updated to: {new_tag}{Colors.NC}")
    else:
        proxy['tag'] = None
        print(f"{Colors.GREEN}✅ Tag removed.{Colors.NC}")
    
    proxies[proxy_id] = proxy
    config['proxies'] = proxies
    save_config(config)
    
    create_service_file(proxy_id, proxy)
    subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=False)
    subprocess.run(['sudo', 'systemctl', 'restart', f'mtpulse-{proxy_id}'], check=False)
    
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")

def service_menu():
    while True:
        clear_screen()
        print(f"{Colors.BOLD}{Colors.GREEN}⚙️ Service Management{Colors.NC}")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        config = load_config()
        proxies = config.get('proxies', {})
        
        if not proxies:
            print(f"{Colors.YELLOW}⚠️ No proxies configured.{Colors.NC}")
            input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
            return
        
        ids, labels = list_proxies(config, show_status=True)
        print("")
        print(f"  {Colors.GREEN}0.{Colors.NC} Back")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        try:
            choice = int(input(f"{Colors.BOLD}{Colors.PURPLE}Select proxy (0-{len(ids)}): {Colors.NC}").strip())
            if choice == 0:
                break
            if choice < 1 or choice > len(ids):
                print(f"{Colors.RED}❌ Invalid selection.{Colors.NC}")
                time.sleep(1)
                continue
        except ValueError:
            print(f"{Colors.RED}❌ Invalid input.{Colors.NC}")
            time.sleep(1)
            continue
        
        proxy_id = ids[choice - 1]
        proxy = proxies[proxy_id]
        service_name = f"mtpulse-{proxy_id}"
        
        while True:
            clear_screen()
            print(f"{Colors.BOLD}{Colors.GREEN}⚙️ Managing: {proxy.get('name', proxy_id)} ({proxy.get('ip')}:{proxy.get('port')}){Colors.NC}")
            print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
            
            status = get_proxy_status(proxy_id)
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
            
            svc_choice = input(f"{Colors.BOLD}{Colors.PURPLE}Select option: {Colors.NC}").strip()
            
            if svc_choice == '1':
                subprocess.run(['sudo', 'systemctl', 'start', service_name], check=False)
                print(f"{Colors.GREEN}✅ Started{Colors.NC}")
                time.sleep(1)
            elif svc_choice == '2':
                subprocess.run(['sudo', 'systemctl', 'stop', service_name], check=False)
                print(f"{Colors.GREEN}✅ Stopped{Colors.NC}")
                time.sleep(1)
            elif svc_choice == '3':
                subprocess.run(['sudo', 'systemctl', 'restart', service_name], check=False)
                print(f"{Colors.GREEN}✅ Restarted{Colors.NC}")
                time.sleep(1)
            elif svc_choice == '4':
                subprocess.run(['sudo', 'systemctl', 'status', service_name], check=False)
                input(f"{Colors.YELLOW}Press Enter...{Colors.NC}")
            elif svc_choice == '5':
                subprocess.run(['sudo', 'journalctl', '-u', service_name, '-n', '30', '--no-pager'], check=False)
                input(f"{Colors.YELLOW}Press Enter...{Colors.NC}")
            elif svc_choice == '0':
                break
            else:
                print(f"{Colors.RED}❌ Invalid option{Colors.NC}")
                time.sleep(1)

def test_proxy_menu():
    """Test a proxy using the real MTProto test"""
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}🔍 Test Proxy (Real MTProto){Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print(f"{Colors.YELLOW}ℹ️  This test uses pyrogram to connect to Telegram via your proxy.{Colors.NC}")
    print(f"{Colors.YELLOW}   You need Telegram API credentials from https://my.telegram.org/apps{Colors.NC}")
    print("")
    
    config = load_config()
    proxies = config.get('proxies', {})
    
    if not proxies:
        print(f"{Colors.RED}❌ No proxies configured.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    
    ids, labels = list_proxies(config, show_status=True)
    print("")
    print(f"  {Colors.GREEN}0.{Colors.NC} Back")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    try:
        choice = int(input(f"{Colors.BOLD}{Colors.PURPLE}Select proxy to test (0-{len(ids)}): {Colors.NC}").strip())
        if choice == 0:
            return
        if choice < 1 or choice > len(ids):
            print(f"{Colors.RED}❌ Invalid selection.{Colors.NC}")
            time.sleep(1)
            return
    except ValueError:
        print(f"{Colors.RED}❌ Invalid input.{Colors.NC}")
        time.sleep(1)
        return
    
    proxy_id = ids[choice - 1]
    
    print("")
    print(f"{Colors.CYAN}🔍 Testing proxy with REAL MTProto connection...{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print("")
    
    # Run the real test (no fallback)
    cmd = [sys.executable, "/usr/local/bin/test_proxy.py", proxy_id]
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print(f"{Colors.RED}❌ Test failed.{Colors.NC}")
    else:
        print(f"{Colors.GREEN}✅ Test completed.{Colors.NC}")
    
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")

def uninstall():
    clear_screen()
    print(f"{Colors.RED}⚠️ Are you sure you want to uninstall MTPulse? (y/N){Colors.NC}")
    confirm = input().strip().lower()
    if confirm != 'y':
        print(f"{Colors.YELLOW}Cancelled.{Colors.NC}")
        time.sleep(1)
        return
    
    config = load_config()
    proxies = config.get('proxies', {})
    
    for proxy_id in proxies:
        service_name = f"mtpulse-{proxy_id}"
        subprocess.run(['sudo', 'systemctl', 'stop', service_name], check=False)
        subprocess.run(['sudo', 'systemctl', 'disable', service_name], check=False)
        subprocess.run(['sudo', 'rm', '-f', f'/etc/systemd/system/{service_name}.service'], check=False)
    
    subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=False)
    
    subprocess.run(['sudo', 'rm', '-f', BINARY_PATH], check=False)
    subprocess.run(['sudo', 'rm', '-rf', CONFIG_DIR], check=False)
    subprocess.run(['sudo', 'rm', '-f', '/usr/local/bin/mtpulse'], check=False)
    subprocess.run(['sudo', 'rm', '-f', TEST_SCRIPT], check=False)
    subprocess.run(['sudo', 'rm', '-rf', '/opt/mtpulse-proxy'], check=False)
    
    print(f"{Colors.GREEN}✅ Uninstallation completed!{Colors.NC}")
    time.sleep(1)

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
            active = 0
            for pid in proxies:
                if get_proxy_status(pid) == "active":
                    active += 1
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
