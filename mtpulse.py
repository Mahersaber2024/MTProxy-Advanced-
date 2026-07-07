#!/usr/bin/env python3
# mtpulse.py - MTPulse MTProto Proxy Manager (Python version)

import os
import sys
import subprocess
import json
import time
import shutil
from pathlib import Path

# ========== Settings ==========
VERSION = "1.0.0"
SPONSOR_NAME = "HeySolo"
SPONSOR_LINK = "https://t.me/HeySoloATM"
CONTACT = "@jadetunnel"
SERVICE_NAME = "mtpulse"
CONFIG_DIR = "/etc/mtpulse"
BINARY_PATH = "/usr/local/bin/mtproto-proxy"
# ===============================

# Colors (ANSI escape codes)
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'
    BOLD = '\033[1m'

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def print_header():
    """Display header with logo"""
    clear_screen()
    print(f"{Colors.CYAN}{Colors.BOLD}╔═══════════════════════════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ███╗   ███╗████████╗██████╗ ██╗   ██╗██╗     ███████╗███████╗  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ████╗ ████║╚══██╔══╝██╔══██╗╚██╗ ██╔╝██║     ██╔════╝██╔════╝  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ██╔████╔██║   ██║   ██████╔╝ ╚████╔╝ ██║     █████╗  ███████╗  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ██║╚██╔╝██║   ██║   ██╔═══╝   ╚██╔╝  ██║     ██╔══╝  ╚════██║  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ██║ ╚═╝ ██║   ██║   ██║        ██║   ███████╗███████╗███████║  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ╚═╝     ╚═╝   ╚═╝   ╚═╝        ╚═╝   ╚══════╝╚══════╝╚══════╝  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║                                                                     ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║                  MTProto Proxy Manager  -  v{VERSION}                 ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}╚═══════════════════════════════════════════════════════════════════════╝{Colors.NC}")
    print("")
    print(f"{Colors.PURPLE}{Colors.BOLD}🌟 Sponsored by: {SPONSOR_NAME}{Colors.NC}")
    print(f"{Colors.PURPLE}🔗 {SPONSOR_LINK}{Colors.NC}")
    print(f"{Colors.PURPLE}📩 Contact: {CONTACT}{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print("")

def get_proxy_status():
    """Check if proxy service is active and get details"""
    if not os.path.exists("/etc/systemd/system/mtpulse.service"):
        return {"status": "not_installed"}
    
    result = subprocess.run(
        ['systemctl', 'is-active', SERVICE_NAME],
        capture_output=True, text=True
    )
    active = result.stdout.strip() == "active"
    
    info = {"status": "active" if active else "inactive"}
    
    if active:
        # Get details from service file
        try:
            with open("/etc/systemd/system/mtpulse.service", 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if 'ExecStart=' in line:
                        # Extract port, secret, tag
                        import re
                        port_match = re.search(r'-H\s+(\d+)', line)
                        secret_match = re.search(r'-S\s+([a-f0-9]+)', line)
                        tag_match = re.search(r'-P\s+([a-f0-9]+)', line)
                        if port_match:
                            info['port'] = port_match.group(1)
                        if secret_match:
                            info['secret'] = secret_match.group(1)
                        if tag_match:
                            info['tag'] = tag_match.group(1)
        except:
            pass
        
        # Get public IP
        try:
            public_ip = subprocess.run(
                ['curl', '-s', '--max-time', '2', 'https://api.ipify.org'],
                capture_output=True, text=True
            ).stdout.strip()
            if public_ip:
                info['ip'] = public_ip
        except:
            pass
    
    return info

def install_proxy():
    """Install MTProto Proxy from official source"""
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}📥 Install MTProto Proxy (Official){Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print("")
    
    # Check if binary already exists
    if os.path.exists(BINARY_PATH):
        print(f"{Colors.YELLOW}Existing MTProxy binary found.{Colors.NC}")
        response = input(f"{Colors.BOLD}{Colors.PURPLE}Do you want to use existing binary? (Y/n): {Colors.NC}")
        if response.lower() in ['', 'y', 'yes']:
            print(f"{Colors.GREEN}✅ Skipping compilation.{Colors.NC}")
            skip_compile = True
        else:
            skip_compile = False
    else:
        skip_compile = False
    
    if not skip_compile:
        print(f"{Colors.CYAN}Cloning official MTProxy repository...{Colors.NC}")
        if os.path.exists("MTProxy"):
            shutil.rmtree("MTProxy")
        
        clone_result = subprocess.run(
            ['git', 'clone', 'https://github.com/TelegramMessenger/MTProxy.git'],
            capture_output=True, text=True
        )
        if clone_result.returncode != 0:
            print(f"{Colors.RED}❌ Failed to clone repository.{Colors.NC}")
            print(clone_result.stderr)
            input(f"{Colors.BOLD}{Colors.MAGENTA}Press Enter to return...{Colors.NC}")
            return
        
        os.chdir("MTProxy")
        
        # Patch for large PIDs
        if os.path.exists("common/pid.c"):
            subprocess.run(
                ["sed", "-i", 's/assert (!(p & 0xffff0000));/\\/\\/ assert (!(p \\& 0xffff0000));/g', "common/pid.c"],
                check=False
            )
        
        print(f"{Colors.CYAN}Compiling source code...{Colors.NC}")
        compile_result = subprocess.run(
            ['make'], capture_output=True, text=True
        )
        
        if compile_result.returncode != 0 or not os.path.exists("objs/bin/mtproto-proxy"):
            print(f"{Colors.RED}❌ Compilation failed. Check dependencies.{Colors.NC}")
            print(f"{Colors.YELLOW}--- Error Log ---{Colors.NC}")
            print(compile_result.stderr[-500:])
            os.chdir("..")
            input(f"{Colors.BOLD}{Colors.MAGENTA}Press Enter to return...{Colors.NC}")
            return
        
        print(f"{Colors.CYAN}Installing binary...{Colors.NC}")
        subprocess.run(['sudo', 'cp', 'objs/bin/mtproto-proxy', BINARY_PATH], check=False)
        subprocess.run(['sudo', 'chmod', '+x', BINARY_PATH], check=False)
        os.chdir("..")
        shutil.rmtree("MTProxy")
        print(f"{Colors.GREEN}✅ MTProxy installed to {BINARY_PATH}{Colors.NC}")
    
    # Create config directory
    subprocess.run(['sudo', 'mkdir', '-p', CONFIG_DIR], check=False)
    
    # Download proxy-secret and proxy-multi.conf
    print(f"{Colors.CYAN}Downloading configuration files...{Colors.NC}")
    subprocess.run(['sudo', 'curl', '-s', 'https://core.telegram.org/getProxySecret', '-o', f'{CONFIG_DIR}/proxy-secret'], check=False)
    subprocess.run(['sudo', 'curl', '-s', 'https://core.telegram.org/getProxyConfig', '-o', f'{CONFIG_DIR}/proxy-multi.conf'], check=False)
    
    # Get port from user
    print("")
    print(f"{Colors.CYAN}--- Configuration ---{Colors.NC}")
    while True:
        port = input(f"{Colors.BOLD}{Colors.PURPLE}Enter port (default 443): {Colors.NC}").strip()
        if not port:
            port = "443"
        if port.isdigit() and 1 <= int(port) <= 65535:
            break
        else:
            print(f"{Colors.RED}❌ Invalid port.{Colors.NC}")
    
    # Generate secret
    secret = subprocess.run(
        ['head', '-c', '16', '/dev/urandom'], capture_output=True
    ).stdout
    secret = subprocess.run(['xxd', '-ps'], input=secret, capture_output=True).stdout.decode().strip()
    print(f"{Colors.CYAN}Generated Secret: {Colors.WHITE}{secret}{Colors.NC}")
    
    # Create service file
    exec_start = f"{BINARY_PATH} -u nobody -p 8888 -H {port} -S {secret} --aes-pwd {CONFIG_DIR}/proxy-secret {CONFIG_DIR}/proxy-multi.conf -M 1"
    
    service_content = f"""[Unit]
Description=MTPulse MTProto Proxy (Official)
After=network.target

[Service]
ExecStart={exec_start}
Restart=always
User=root
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
"""
    
    with open("/tmp/mtpulse.service", 'w') as f:
        f.write(service_content)
    subprocess.run(['sudo', 'mv', '/tmp/mtpulse.service', f'/etc/systemd/system/{SERVICE_NAME}.service'], check=False)
    
    subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=False)
    subprocess.run(['sudo', 'systemctl', 'enable', SERVICE_NAME], check=False)
    subprocess.run(['sudo', 'systemctl', 'start', SERVICE_NAME], check=False)
    
    print(f"{Colors.GREEN}✅ MTPulse service started!{Colors.NC}")
    
    # Show proxy details
    public_ip = subprocess.run(
        ['curl', '-s', 'https://api.ipify.org'], capture_output=True, text=True
    ).stdout.strip()
    
    print("")
    print(f"{Colors.GREEN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"{Colors.GREEN}{Colors.BOLD}     🚀 Proxy Details{Colors.NC}")
    print(f"{Colors.GREEN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"IP:     {Colors.WHITE}{public_ip}{Colors.NC}")
    print(f"Port:   {Colors.WHITE}{port}{Colors.NC}")
    print(f"Secret: {Colors.WHITE}{secret}{Colors.NC}")
    print("")
    print(f"{Colors.BOLD}{Colors.CYAN}tg://proxy?server={public_ip}&port={port}&secret={secret}{Colors.NC}")
    print("")
    input(f"{Colors.BOLD}{Colors.MAGENTA}Press Enter to return...{Colors.NC}")

def service_menu():
    """Service management submenu"""
    while True:
        clear_screen()
        print(f"{Colors.BOLD}{Colors.GREEN}⚙️ Service Management{Colors.NC}")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        print(f"  {Colors.GREEN}1.{Colors.NC} Status")
        print(f"  {Colors.GREEN}2.{Colors.NC} Start")
        print(f"  {Colors.GREEN}3.{Colors.NC} Stop")
        print(f"  {Colors.GREEN}4.{Colors.NC} Restart")
        print(f"  {Colors.GREEN}5.{Colors.NC} Logs")
        print(f"  {Colors.GREEN}0.{Colors.NC} Back")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        choice = input(f"{Colors.BOLD}{Colors.PURPLE}Select an option: {Colors.NC}").strip()
        
        if choice == '1':
            subprocess.run(['sudo', 'systemctl', 'status', SERVICE_NAME], check=False)
            input(f"{Colors.YELLOW}Press Enter...{Colors.NC}")
        elif choice == '2':
            subprocess.run(['sudo', 'systemctl', 'start', SERVICE_NAME], check=False)
            print(f"{Colors.GREEN}✅ Started{Colors.NC}")
            time.sleep(1)
        elif choice == '3':
            subprocess.run(['sudo', 'systemctl', 'stop', SERVICE_NAME], check=False)
            print(f"{Colors.GREEN}✅ Stopped{Colors.NC}")
            time.sleep(1)
        elif choice == '4':
            subprocess.run(['sudo', 'systemctl', 'restart', SERVICE_NAME], check=False)
            print(f"{Colors.GREEN}✅ Restarted{Colors.NC}")
            time.sleep(1)
        elif choice == '5':
            subprocess.run(['sudo', 'journalctl', '-u', SERVICE_NAME, '-n', '50', '--no-pager'], check=False)
            input(f"{Colors.YELLOW}Press Enter...{Colors.NC}")
        elif choice == '0':
            break
        else:
            print(f"{Colors.RED}❌ Invalid option{Colors.NC}")
            time.sleep(1)

def add_sponsor():
    """Add or remove sponsor tag"""
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}📝 Add Tag to Your Proxy{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    if not os.path.exists("/etc/systemd/system/mtpulse.service"):
        print(f"{Colors.RED}❌ Proxy is NOT installed. Please install first.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.MAGENTA}Press Enter to return...{Colors.NC}")
        return
    
    # Read current service file
    with open("/etc/systemd/system/mtpulse.service", 'r') as f:
        content = f.read()
    
    # Extract current tag
    import re
    current_tag = None
    for line in content.split('\n'):
        if 'ExecStart=' in line:
            match = re.search(r'-P\s+([a-f0-9]+)', line)
            if match:
                current_tag = match.group(1)
                break
    
    if current_tag:
        print(f"{Colors.YELLOW}Current Tag: {Colors.BOLD}{Colors.MAGENTA}{current_tag}{Colors.NC}")
        print("")
        response = input(f"{Colors.BOLD}{Colors.PURPLE}Do you want to remove it and set a new one? (y/N): {Colors.NC}")
        if response.lower() not in ['y', 'yes']:
            return
    else:
        print(f"{Colors.YELLOW}Current Tag: {Colors.WHITE}None{Colors.NC}")
        print("")
    
    print(f"{Colors.YELLOW}ℹ️  To get an AD Tag, you must use the official Telegram bot:{Colors.NC} {Colors.BOLD}{Colors.BLUE}@MTProxybot{Colors.NC}")
    print(f"{Colors.YELLOW}    Register your proxy there and it will give you a 32-character hex tag.{Colors.NC}")
    print("")
    
    new_tag = input(f"{Colors.BOLD}{Colors.PURPLE}Enter new AD Tag (leave empty to remove): {Colors.NC}").strip()
    
    # Remove existing -P flag
    new_content = re.sub(r' -P [a-f0-9]+', '', content)
    
    # Add new tag if provided
    if new_tag:
        new_content = re.sub(r'(ExecStart=[^\n]+)', rf'\1 -P {new_tag}', new_content)
        print(f"{Colors.GREEN}✅ Sponsor tag updated to: {new_tag}{Colors.NC}")
    else:
        print(f"{Colors.GREEN}✅ Sponsor tag removed.{Colors.NC}")
    
    # Write new service file
    with open("/tmp/mtpulse.service", 'w') as f:
        f.write(new_content)
    subprocess.run(['sudo', 'mv', '/tmp/mtpulse.service', '/etc/systemd/system/mtpulse.service'], check=False)
    
    subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=False)
    subprocess.run(['sudo', 'systemctl', 'restart', SERVICE_NAME], check=False)
    
    input(f"{Colors.BOLD}{Colors.MAGENTA}Press Enter to return...{Colors.NC}")

def uninstall():
    """Uninstall the service"""
    clear_screen()
    print(f"{Colors.RED}⚠️ Are you sure you want to uninstall MTPulse? (y/N){Colors.NC}")
    confirm = input().strip().lower()
    if confirm == 'y':
        subprocess.run(['sudo', 'systemctl', 'stop', SERVICE_NAME], check=False)
        subprocess.run(['sudo', 'systemctl', 'disable', SERVICE_NAME], check=False)
        subprocess.run(['sudo', 'rm', '-f', f'/etc/systemd/system/{SERVICE_NAME}.service'], check=False)
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=False)
        
        subprocess.run(['sudo', 'rm', '-f', BINARY_PATH], check=False)
        subprocess.run(['sudo', 'rm', '-rf', CONFIG_DIR], check=False)
        subprocess.run(['sudo', 'rm', '-f', '/usr/local/bin/mtpulse'], check=False)
        subprocess.run(['sudo', 'rm', '-rf', '/opt/mtpulse-proxy'], check=False)
        subprocess.run(['sudo', 'rm', '-rf', '/var/lib/mtpulse'], check=False)
        
        print(f"{Colors.GREEN}✅ Uninstallation completed!{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}Cancelled.{Colors.NC}")
    time.sleep(1)

def main():
    """Main menu loop"""
    while True:
        print_header()
        
        # Show status
        status_info = get_proxy_status()
        
        print(f"{Colors.BLUE}📊 Status:{Colors.NC}")
        if status_info['status'] == 'not_installed':
            print(f"  {Colors.RED}●{Colors.NC} Proxy Status: {Colors.RED}Not Installed{Colors.NC}")
        elif status_info['status'] == 'active':
            print(f"  {Colors.GREEN}●{Colors.NC} Proxy Status: {Colors.GREEN}Active{Colors.NC}")
            if 'ip' in status_info and 'port' in status_info and 'secret' in status_info:
                link = f"tg://proxy?server={status_info['ip']}&port={status_info['port']}&secret={status_info['secret']}"
                print(f"  {Colors.BLUE}●{Colors.NC} Link: {Colors.BOLD}{Colors.CYAN}{link}{Colors.NC}")
            if 'tag' in status_info:
                print(f"  {Colors.BLUE}●{Colors.NC} Sponsor Tag: {Colors.BOLD}{Colors.MAGENTA}{status_info['tag']}{Colors.NC}")
        else:
            print(f"  {Colors.RED}●{Colors.NC} Proxy Status: {Colors.RED}Inactive{Colors.NC}")
        
        print("")
        
        print(f"{Colors.BLUE}📋 Menu:{Colors.NC}")
        print(f"  {Colors.GREEN}1.{Colors.NC} 📥 Install MTProto Proxy")
        print(f"  {Colors.GREEN}2.{Colors.NC} ⚙️ Service Management")
        print(f"  {Colors.GREEN}3.{Colors.NC} 📝 Add Tag to Your Proxy")
        print(f"  {Colors.GREEN}4.{Colors.NC} 🗑️ Uninstall MTPulse")
        print(f"  {Colors.GREEN}0.{Colors.NC} 🚪 Exit")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        choice = input(f"{Colors.BOLD}{Colors.PURPLE}Select an option: {Colors.NC}").strip()
        
        if choice == '1':
            install_proxy()
        elif choice == '2':
            service_menu()
        elif choice == '3':
            add_sponsor()
        elif choice == '4':
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
