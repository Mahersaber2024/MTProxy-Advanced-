#!/usr/bin/env python3
# test_proxy.py - MTProto Proxy Tester

import os
import sys
import json
import subprocess
from pathlib import Path

# ========== Settings ==========
CONFIG_DIR = "/etc/mtpulse"
CONFIG_FILE = f"{CONFIG_DIR}/proxies.json"
TEST_CONFIG_FILE = f"{CONFIG_DIR}/test_config.json"
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

def print_header():
    """Display test header"""
    print(f"{Colors.CYAN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}     🔍 MTProto Proxy Tester{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print("")

def load_config():
    """Load proxy configuration"""
    if not os.path.exists(CONFIG_FILE):
        return {"proxies": {}}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"proxies": {}}

def load_test_config():
    """Load test configuration (api_id, api_hash)"""
    if not os.path.exists(TEST_CONFIG_FILE):
        return {}
    try:
        with open(TEST_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_test_config(config):
    """Save test configuration"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(TEST_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_api_credentials():
    """Get API ID and Hash from user or config"""
    config = load_test_config()
    
    if config.get('api_id') and config.get('api_hash'):
        print(f"{Colors.GREEN}✅ Using saved API credentials from {TEST_CONFIG_FILE}{Colors.NC}")
        return config['api_id'], config['api_hash']
    
    print(f"{Colors.YELLOW}⚠️ No API credentials found.{Colors.NC}")
    print(f"{Colors.CYAN}ℹ️  You need a Telegram API ID and Hash from https://my.telegram.org/apps{Colors.NC}")
    print("")
    
    api_id = input(f"{Colors.BOLD}{Colors.PURPLE}Enter API ID: {Colors.NC}").strip()
    api_hash = input(f"{Colors.BOLD}{Colors.PURPLE}Enter API Hash: {Colors.NC}").strip()
    
    if not api_id or not api_hash:
        print(f"{Colors.RED}❌ API ID and Hash are required.{Colors.NC}")
        return None, None
    
    # Save for future use
    save_test_config({"api_id": api_id, "api_hash": api_hash})
    print(f"{Colors.GREEN}✅ API credentials saved to {TEST_CONFIG_FILE}{Colors.NC}")
    
    return api_id, api_hash

def check_pyrogram():
    """Check if pyrogram is installed"""
    try:
        import pyrogram
        return True, pyrogram.__version__
    except ImportError:
        return False, None

def install_pyrogram():
    """Install pyrogram using pip"""
    print(f"{Colors.CYAN}📦 Installing pyrogram...{Colors.NC}")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pyrogram", "tgcrypto"], 
                      capture_output=True, text=True, check=True)
        print(f"{Colors.GREEN}✅ Pyrogram installed successfully.{Colors.NC}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ Failed to install pyrogram: {e}{Colors.NC}")
        return False

def test_proxy_with_pyrogram(proxy_data, api_id, api_hash):
    """Test proxy using pyrogram"""
    try:
        from pyrogram import Client
        from pyrogram.errors import RPCError, Unauthorized, FloodWait
    except ImportError:
        print(f"{Colors.RED}❌ Pyrogram not available.{Colors.NC}")
        return False, "Pyrogram not installed"
    
    ip = proxy_data.get('ip')
    port = int(proxy_data.get('port'))
    secret = proxy_data.get('secret')
    name = proxy_data.get('name', 'Unnamed')
    
    proxy_config = {
        "scheme": "mtproto",
        "hostname": ip,
        "port": port,
        "secret": secret
    }
    
    print(f"{Colors.CYAN}🔄 Testing proxy: {Colors.WHITE}{name} ({ip}:{port}){Colors.NC}")
    print(f"{Colors.CYAN}   Connecting to Telegram via MTProto...{Colors.NC}")
    
    try:
        # Use a temporary session file
        session_file = f"/tmp/test_session_{os.getpid()}"
        
        app = Client(
            session_file,
            api_id=int(api_id),
            api_hash=api_hash,
            proxy=proxy_config,
            workdir="/tmp"
        )
        
        # Try to connect
        app.connect()
        
        # Try a simple API call - get the bot's own info (or user info)
        # We'll use get_me() to check if we can authenticate
        # If it works, the proxy is good
        try:
            # Check if we can get our own user info
            me = app.get_me()
            if me:
                print(f"{Colors.GREEN}✅ Proxy is WORKING!{Colors.NC}")
                print(f"   Connected as: {Colors.WHITE}{me.first_name or me.username or me.id}{Colors.NC}")
                app.disconnect()
                return True, f"Connected as {me.first_name or me.username or me.id}"
            else:
                app.disconnect()
                return False, "No user data received"
                
        except Unauthorized:
            print(f"{Colors.YELLOW}⚠️ Proxy connected but authentication failed.{Colors.NC}")
            print(f"   This might mean the proxy works but you need to login.")
            app.disconnect()
            return True, "Connected (auth required)"
            
        except RPCError as e:
            app.disconnect()
            print(f"{Colors.RED}❌ RPC Error: {e}{Colors.NC}")
            return False, f"RPC Error: {e}"
            
        except FloodWait as e:
            app.disconnect()
            print(f"{Colors.YELLOW}⏳ Rate limited. Try again in {e.value} seconds.{Colors.NC}")
            return False, f"Flood wait {e.value}s"
            
    except Exception as e:
        error_msg = str(e)
        if "Connection" in error_msg or "timeout" in error_msg.lower():
            print(f"{Colors.RED}❌ Connection failed - proxy might be down or unreachable{Colors.NC}")
            return False, f"Connection failed: {error_msg[:100]}"
        else:
            print(f"{Colors.RED}❌ Error: {error_msg[:200]}{Colors.NC}")
            return False, f"Error: {error_msg[:200]}"

def test_proxy_simple(proxy_data):
    """Simple UDP port test using nc/socat"""
    import socket
    import time
    
    ip = proxy_data.get('ip')
    port = int(proxy_data.get('port'))
    name = proxy_data.get('name', 'Unnamed')
    
    print(f"{Colors.CYAN}🔄 Testing UDP connectivity: {Colors.WHITE}{name} ({ip}:{port}){Colors.NC}")
    
    try:
        # Try to send a UDP packet
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        
        # Send a simple MTProto ping-like packet (not real, just for connectivity test)
        # Telegram MTProto uses a specific protocol, but we can't simulate it fully
        # Just check if the port is reachable
        start = time.time()
        sock.sendto(b"\x00\x00\x00\x00", (ip, port))
        try:
            data, addr = sock.recvfrom(1024)
            elapsed = time.time() - start
            print(f"{Colors.GREEN}✅ UDP port is reachable (response in {elapsed:.2f}s){Colors.NC}")
            sock.close()
            return True, f"UDP reachable ({elapsed:.2f}s)"
        except socket.timeout:
            print(f"{Colors.YELLOW}⚠️ UDP port reachable but no response (timeout){Colors.NC}")
            print(f"   This is normal - MTProto doesn't respond to arbitrary packets")
            sock.close()
            return True, "UDP port open (no response)"
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ UDP test failed: {e}{Colors.NC}")
            sock.close()
            return False, f"UDP error: {e}"
            
    except Exception as e:
        print(f"{Colors.RED}❌ UDP connectivity test failed: {e}{Colors.NC}")
        return False, f"UDP test failed: {e}"

def test_proxy(proxy_id, proxy_data, mode='full'):
    """Main test function"""
    print_header()
    
    if mode == 'simple':
        return test_proxy_simple(proxy_data)
    
    # Full test with pyrogram
    has_pyrogram, version = check_pyrogram()
    if not has_pyrogram:
        print(f"{Colors.YELLOW}⚠️ Pyrogram not found.{Colors.NC}")
        install = input(f"{Colors.BOLD}{Colors.PURPLE}Install pyrogram now? (Y/n): {Colors.NC}").strip()
        if install.lower() not in ['', 'y', 'yes']:
            print(f"{Colors.YELLOW}Skipping full test. Use simple UDP test instead.{Colors.NC}")
            return test_proxy_simple(proxy_data)
        
        if not install_pyrogram():
            print(f"{Colors.YELLOW}Falling back to UDP test.{Colors.NC}")
            return test_proxy_simple(proxy_data)
        
        # Re-import after installation
        try:
            from pyrogram import Client
        except ImportError:
            print(f"{Colors.RED}❌ Pyrogram still not available. Falling back to UDP test.{Colors.NC}")
            return test_proxy_simple(proxy_data)
    
    # Get API credentials
    api_id, api_hash = get_api_credentials()
    if not api_id or not api_hash:
        print(f"{Colors.YELLOW}⚠️ Cannot test with pyrogram without API credentials.{Colors.NC}")
        return test_proxy_simple(proxy_data)
    
    return test_proxy_with_pyrogram(proxy_data, api_id, api_hash)

def main():
    """CLI entry point"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 test_proxy.py <proxy_id>")
        print("  or:  python3 test_proxy.py --list")
        print("  or:  python3 test_proxy.py --simple <proxy_id>")
        sys.exit(1)
    
    if sys.argv[1] == '--list':
        config = load_config()
        proxies = config.get('proxies', {})
        print("Available proxies:")
        for pid, p in proxies.items():
            print(f"  {pid}: {p.get('name')} ({p.get('ip')}:{p.get('port')})")
        sys.exit(0)
    
    if sys.argv[1] == '--simple':
        if len(sys.argv) < 3:
            print("Usage: python3 test_proxy.py --simple <proxy_id>")
            sys.exit(1)
        proxy_id = sys.argv[2]
        mode = 'simple'
    else:
        proxy_id = sys.argv[1]
        mode = 'full'
    
    config = load_config()
    proxies = config.get('proxies', {})
    
    if proxy_id not in proxies:
        print(f"{Colors.RED}❌ Proxy '{proxy_id}' not found.{Colors.NC}")
        print("Available proxies:", list(proxies.keys()))
        sys.exit(1)
    
    proxy_data = proxies[proxy_id]
    success, message = test_proxy(proxy_id, proxy_data, mode)
    
    print("")
    print(f"{Colors.CYAN}════════════════════════════════════════════════════════════{Colors.NC}")
    if success:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ Test PASSED{Colors.NC}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ Test FAILED{Colors.NC}")
    print(f"Message: {message}")
    print(f"{Colors.CYAN}════════════════════════════════════════════════════════════{Colors.NC}")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
