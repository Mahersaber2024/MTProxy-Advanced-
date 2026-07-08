#!/usr/bin/env python3
# test_proxy.py - MTProto Proxy Tester (Real MTProto Test)

import os
import sys
import json
import subprocess
import socket
import time
import shutil
import tempfile
from pathlib import Path

# ========== Settings ==========
CONFIG_DIR = "/etc/mtpulse"
CONFIG_FILE = f"{CONFIG_DIR}/proxies.json"
TEST_CONFIG_FILE = f"{CONFIG_DIR}/test_config.json"
SETTINGS_FILE = f"{CONFIG_DIR}/settings.json"
VENV_DIR = "/tmp/mtproto_test_venv"
# ===============================

# Colors
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

def print_header():
    print(f"{Colors.CYAN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}     🔍 MTProto Proxy Tester (Real MTProto){Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print("")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"proxies": {}}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"proxies": {}}

def load_test_config():
    if not os.path.exists(TEST_CONFIG_FILE):
        return {}
    try:
        with open(TEST_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_test_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(TEST_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"default_server": "", "default_port": "443", "default_domain": "www.google.com"}
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"default_server": "", "default_port": "443", "default_domain": "www.google.com"}

def get_default_port():
    settings = load_settings()
    return settings.get('default_port', '443')

def get_public_ip():
    try:
        ip = subprocess.run(['curl', '-s', '--max-time', '2', 'https://api.ipify.org'],
                           capture_output=True, text=True).stdout.strip()
        if ip:
            return ip
    except:
        pass
    return "Unknown"

def get_api_credentials():
    config = load_test_config()
    if config.get('api_id') and config.get('api_hash'):
        print(f"{Colors.GREEN}✅ Using saved API credentials{Colors.NC}")
        return config['api_id'], config['api_hash']
    
    print(f"{Colors.YELLOW}⚠️ No API credentials found.{Colors.NC}")
    print(f"{Colors.CYAN}ℹ️  Get from https://my.telegram.org/apps{Colors.NC}")
    print("")
    
    api_id = input(f"{Colors.BOLD}{Colors.PURPLE}Enter API ID: {Colors.NC}").strip()
    api_hash = input(f"{Colors.BOLD}{Colors.PURPLE}Enter API Hash: {Colors.NC}").strip()
    
    if not api_id or not api_hash:
        print(f"{Colors.RED}❌ API ID and Hash are required.{Colors.NC}")
        return None, None
    
    save_test_config({"api_id": api_id, "api_hash": api_hash})
    print(f"{Colors.GREEN}✅ Credentials saved.{Colors.NC}")
    return api_id, api_hash

def ensure_pyrogram():
    """Ensure pyrogram is installed using virtual environment"""
    if os.path.exists(VENV_DIR):
        python_path = f"{VENV_DIR}/bin/python"
        try:
            result = subprocess.run(
                [python_path, "-c", "import pyrogram; print(pyrogram.__version__)"],
                capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                print(f"{Colors.GREEN}✅ Pyrogram {result.stdout.strip()} found in venv{Colors.NC}")
                return python_path
        except:
            pass
    
    print(f"{Colors.CYAN}📦 Creating virtual environment and installing pyrogram...{Colors.NC}")
    
    if os.path.exists(VENV_DIR):
        shutil.rmtree(VENV_DIR)
    
    try:
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True, capture_output=True)
        python_path = f"{VENV_DIR}/bin/python"
        pip_path = f"{VENV_DIR}/bin/pip"
        
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True, capture_output=True)
        print(f"{Colors.CYAN}   Installing pyrogram and tgcrypto...{Colors.NC}")
        subprocess.run([pip_path, "install", "pyrogram", "tgcrypto"], check=True, capture_output=True)
        
        print(f"{Colors.GREEN}✅ Pyrogram installed successfully in venv{Colors.NC}")
        return python_path
        
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ Failed to install pyrogram:{Colors.NC}")
        print(e.stderr.decode() if e.stderr else str(e))
        if os.path.exists(VENV_DIR):
            shutil.rmtree(VENV_DIR)
        return None

def test_proxy_with_pyrogram(python_path, proxy_data, api_id, api_hash):
    """Run real MTProto test using pyrogram in venv"""
    if not python_path or not os.path.exists(python_path):
        return False, "Pyrogram not available"
    
    # Use 'server' field (not 'ip')
    server = proxy_data.get('server')
    if not server:
        # fallback to default server if empty
        settings = load_settings()
        server = settings.get('default_server')
        if not server:
            server = get_public_ip()
        if not server:
            return False, "No server address found for proxy"
    
    # Get port, fallback to default if empty
    port_str = proxy_data.get('port', '')
    if port_str == '':
        default_port = get_default_port()
        port = int(default_port)
    else:
        try:
            port = int(port_str)
        except ValueError:
            print(f"{Colors.YELLOW}⚠️ Invalid port '{port_str}', using default port {get_default_port()}{Colors.NC}")
            port = int(get_default_port())
    
    secret = proxy_data.get('secret')
    if not secret:
        return False, "No secret found for proxy"
    
    name = proxy_data.get('name', 'Unnamed')
    
    print(f"{Colors.CYAN}🔄 Testing proxy: {Colors.WHITE}{name} ({server}:{port}){Colors.NC}")
    print(f"{Colors.CYAN}   Connecting to Telegram via MTProto...{Colors.NC}")
    
    test_script = f"""
import sys
import json
from pyrogram import Client
from pyrogram.errors import RPCError, Unauthorized, FloodWait

server = "{server}"
port = {port}
secret = "{secret}"
api_id = {int(api_id)}
api_hash = "{api_hash}"
name = "{name}"

proxy = {{
    "scheme": "mtproto",
    "hostname": server,
    "port": port,
    "secret": secret
}}

try:
    app = Client(
        "/tmp/test_session",
        api_id=api_id,
        api_hash=api_hash,
        proxy=proxy,
        workdir="/tmp"
    )
    app.connect()
    me = app.get_me()
    if me:
        result = {{
            "success": True,
            "message": f"Connected as {{me.first_name or me.username or me.id}}"
        }}
    else:
        result = {{"success": False, "message": "No user data received"}}
    app.disconnect()
except Unauthorized:
    result = {{"success": True, "message": "Connected (auth required)"}}
except FloodWait as e:
    result = {{"success": False, "message": f"Flood wait {{e.value}}s"}}
except RPCError as e:
    result = {{"success": False, "message": f"RPC Error: {{e}}"}}
except Exception as e:
    result = {{"success": False, "message": f"Error: {{str(e)[:100]}}"}}

print(json.dumps(result))
"""
    
    try:
        script_file = "/tmp/mtproto_test_script.py"
        with open(script_file, 'w') as f:
            f.write(test_script)
        
        result = subprocess.run(
            [python_path, script_file],
            capture_output=True, text=True, check=False
        )
        
        if result.returncode != 0:
            return False, f"Test script failed: {result.stderr[:200]}"
        
        try:
            data = json.loads(result.stdout.strip())
            return data.get('success', False), data.get('message', 'Unknown')
        except json.JSONDecodeError:
            return False, f"Invalid response: {result.stdout[:100]}"
            
    except Exception as e:
        return False, f"Test execution error: {str(e)[:100]}"

def test_proxy(proxy_id, proxy_data):
    """Main test function - only real MTProto test"""
    print_header()
    
    python_path = ensure_pyrogram()
    if not python_path:
        print(f"{Colors.RED}❌ Cannot proceed without pyrogram.{Colors.NC}")
        return False, "Pyrogram installation failed"
    
    api_id, api_hash = get_api_credentials()
    if not api_id or not api_hash:
        print(f"{Colors.RED}❌ API credentials required for real test.{Colors.NC}")
        return False, "API credentials missing"
    
    return test_proxy_with_pyrogram(python_path, proxy_data, api_id, api_hash)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_proxy.py <proxy_id>")
        print("  or:  python3 test_proxy.py --list")
        sys.exit(1)
    
    if sys.argv[1] == '--list':
        config = load_config()
        proxies = config.get('proxies', {})
        print("Available proxies:")
        for pid, p in proxies.items():
            print(f"  {pid}: {p.get('name')} ({p.get('server')}:{p.get('port')})")
        sys.exit(0)
    
    proxy_id = sys.argv[1]
    config = load_config()
    proxies = config.get('proxies', {})
    
    if proxy_id not in proxies:
        print(f"{Colors.RED}❌ Proxy '{proxy_id}' not found.{Colors.NC}")
        print("Available:", list(proxies.keys()))
        sys.exit(1)
    
    proxy_data = proxies[proxy_id]
    success, message = test_proxy(proxy_id, proxy_data)
    
    print("")
    print(f"{Colors.CYAN}════════════════════════════════════════════════════════════{Colors.NC}")
    if success:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ PROXY IS WORKING{Colors.NC}")
        print(f"Message: {message}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ PROXY IS NOT WORKING{Colors.NC}")
        print(f"Reason: {message}")
        print(f"{Colors.YELLOW}💡 Try checking firewall, ports, or proxy configuration.{Colors.NC}")
    print(f"{Colors.CYAN}════════════════════════════════════════════════════════════{Colors.NC}")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
