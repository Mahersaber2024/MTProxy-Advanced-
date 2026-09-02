#!/usr/bin/env python3
# mtproxy.py - MTProxy Manager for MTProto Proxy (Python Version)

import os
import sys
import subprocess
import json
import time
import shutil
import re
from pathlib import Path
import mtproxy_stats
import mtproxy_socks

# ========== Settings ==========
VERSION = "3.5.0"
SPONSOR_NAME = "JadeTunnel"
SPONSOR_LINK = "https://t.me/jadetunnell"
CONTACT = "@jadetunnel"
PROXY_DIR = "/opt/mtprotoproxy"
CONFIG_FILE = f"{PROXY_DIR}/config.py"
CONFIG_DIR = "/etc/mtpulse"
PROXIES_FILE = f"{CONFIG_DIR}/proxies.json"
SETTINGS_FILE = f"{CONFIG_DIR}/settings.json"
SERVICE_NAME = "mtprotoproxy"
# Per-proxy port support: every distinct bind-IP:port pair runs as its own
# systemd instance, because one mtprotoproxy process = one listening port.
INSTANCE_DIR = f"{CONFIG_DIR}/instances"
INSTANCE_UNIT = "mtproxy-inst"                      # mtproxy-inst@<key>.service
INSTANCE_UNIT_FILE = f"/etc/systemd/system/{INSTANCE_UNIT}@.service"
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
    print(f"{Colors.CYAN}{Colors.BOLD}╔═════════════════════════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ██╗  █████╗  ██████╗  ███████╗                                ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ██║ ██╔══██╗ ██╔══██╗ ██╔════╝                                ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ██║ ███████║ ██║  ██║ █████╗                                  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║  ██   ██║ ██╔══██║ ██║  ██║ ██╔══╝                                  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║  ╚█████╔╝ ██║  ██║ ██████╔╝ ███████╗                                ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║   ╚════╝  ╚═╝  ╚═╝ ╚═════╝  ╚══════╝                                ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║                                                                     ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║   ████████╗ ██╗   ██╗ ███╗   ██╗ ███╗   ██╗ ███████╗ ██╗            ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║   ╚══██╔══╝ ██║   ██║ ████╗  ██║ ████╗  ██║ ██╔════╝ ██║            ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║      ██║    ██║   ██║ ██╔██╗ ██║ ██╔██╗ ██║ █████╗   ██║            ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║      ██║    ██║   ██║ ██║╚██╗██║ ██║╚██╗██║ ██╔══╝   ██║            ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║      ██║    ╚██████╔╝ ██║ ╚████║ ██║ ╚████║ ███████╗ ███████╗       ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║      ╚═╝     ╚═════╝  ╚═╝  ╚═══╝ ╚═╝  ╚═══╝ ╚══════╝ ╚══════╝       ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║                                                                     ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║                MTProxy Manager  -  v{VERSION} (Python)               ║{Colors.NC}")
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

def set_default_port(port):
    settings = load_settings()
    settings['default_port'] = port.strip()
    save_settings(settings)

def set_default_domain(domain):
    settings = load_settings()
    settings['default_domain'] = domain.strip()
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

def restart_service(config=None):
    """Rewrite every per-port instance config and restart the instances.

    Usage counters are persisted BEFORE restarting - mtprotoproxy zeroes its
    in-memory stats on every restart, which is why usage kept showing 0 B."""
    sync_instances(config, force_restart=True)


def get_proxy_status():
    """Active when at least one per-port instance is running."""
    keys = list(group_instances(load_proxies()))
    if keys:
        for key in keys:
            if instance_status(key) == "active":
                return "active"
        return "inactive"
    if not os.path.exists(f"/etc/systemd/system/{SERVICE_NAME}.service"):
        return "not_installed"
    result = subprocess.run(['systemctl', 'is-active', SERVICE_NAME],
                           capture_output=True, text=True)
    return "active" if result.stdout.strip() == "active" else "inactive"

def get_proxy_link(proxy):
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

def list_proxies(config, show_status=True, show_links=False):
    """Display list of proxies with online/offline user statistics and traffic"""
    proxies = config.get('proxies', {})
    if not proxies:
        print(f"{Colors.YELLOW}⚠️ No proxies configured.{Colors.NC}")
        return [], []
    
    print(f"{Colors.BLUE}📋 Available Proxies:{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    ids = []
    labels = []
    # status is per port now, cached per instance key
    status_cache = {}
    # unique-client online count is also per instance key (same port = same
    # kernel connections, regardless of which named proxy shares it)
    online_cache = {}
    # Single cached journal pass for ALL proxies (was: 3 journalctl runs each)
    all_stats = mtproxy_stats.get_all_stats()
    
    for idx, (proxy_id, proxy) in enumerate(proxies.items(), 1):
        ids.append(proxy_id)
        name = proxy.get('name', 'Unnamed')
        server = proxy.get('server', '')
        port = proxy.get('port', '')
        tag = proxy.get('tag')
        
        # Get stats
        if not port:
            port = get_default_port()
        if not server:
            server = get_default_server()
            if not server:
                server = get_public_ip()
        
        # Stats: cumulative and restart-proof (persisted in /etc/mtpulse/usage.json)
        st = all_stats.get(name, {})
        connects = st.get('total_connects', 0)
        traffic_display = mtproxy_stats.format_bytes(st.get('total_bytes', 0))
        
        # Status indicators (status of the instance serving this port)
        inst_key = proxy_instance_key(proxy)
        if inst_key not in status_cache:
            status_cache[inst_key] = "active" if instance_status(inst_key) == "active" else "inactive"
        status = status_cache[inst_key]
        
        # "Online": real distinct clients (deduped by IP via `ss`), not the
        # raw open-socket count mtprotoproxy's own log reports - one client
        # can hold several parallel connections, which used to be counted
        # as several separate "online" users.
        if inst_key not in online_cache:
            online_cache[inst_key] = len(mtproxy_stats.get_established_ips(
                proxy_port(proxy), proxy_bind(proxy)))
        online = online_cache[inst_key]
        peak = mtproxy_stats.record_unique_peak(name, online)
        if status == "active":
            status_text = f"{Colors.GREEN}● Active{Colors.NC}"
        else:
            status_text = f"{Colors.RED}● Inactive{Colors.NC}"
        
        # Color coding for online/offline
        online_color = Colors.GREEN if online > 0 else Colors.YELLOW
        peak_color = Colors.WHITE
        
        server_text = f"@ {server}:{port}" if server else f"port {port}"
        bind_ip = proxy_bind(proxy)
        if bind_ip:
            server_text += f" (bind {bind_ip})"
        
        # Display tag
        if tag:
            tag_display = f"🏷️ {Colors.MAGENTA}{tag}{Colors.NC}"
        else:
            tag_display = f"{Colors.YELLOW}No Tag{Colors.NC}"
        
        # Show all stats
        label = (f"{idx}. {Colors.BOLD}{name}{Colors.NC} | {server_text} | {tag_display} | "
                f"{status_text} | {Colors.BLUE}● Online: {online_color}{online}{Colors.NC} | "
                f"{Colors.BLUE}● Peak: {peak_color}{peak}{Colors.NC} | "
                f"{Colors.BLUE}● Connects: {Colors.WHITE}{connects}{Colors.NC} | "
                f"{Colors.BLUE}● Usage: {Colors.WHITE}{traffic_display}{Colors.NC}")
        labels.append(label)
        print(f"  {label}")
        
        if show_links and status == "active":
            link = get_proxy_link(proxy)
            print(f"     {Colors.CYAN}🔗 {link}{Colors.NC}")
    
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    return ids, labels

def list_proxies_for_tag(config):
    """Display list of proxies showing full secret (without extra hints)"""
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
        
        # Show full secret (not shortened)
        label = f"{idx}. {Colors.BOLD}{name}{Colors.NC} | {server_text} | Secret: {Colors.WHITE}{secret}{Colors.NC} | {status_text}{tag_text}"
        labels.append(label)
        print(f"  {label}")
    
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    return ids, labels

# ========== Per-port instance engine ==========
# mtprotoproxy listens on exactly ONE port per process, so "a different port
# per proxy" means "a different process per port". Every bind-IP:port pair gets
#   config : /etc/mtpulse/instances/<key>.py
#   service: mtproxy-inst@<key>.service   (systemd template unit)

def valid_port(value):
    """Return the port as int, or None when empty/invalid."""
    try:
        port = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return port if 1 <= port <= 65535 else None


def proxy_port(proxy):
    return str(valid_port(proxy.get('port')) or get_default_port())


def proxy_bind(proxy):
    return (proxy.get('bind') or '').strip()


def instance_key(bind, port):
    return re.sub(r'[^A-Za-z0-9]', '_', f"{bind or 'any'}-{port}")


def proxy_instance_key(proxy):
    return instance_key(proxy_bind(proxy), proxy_port(proxy))


def instance_status(key):
    result = subprocess.run(['systemctl', 'is-active', f"{INSTANCE_UNIT}@{key}.service"],
                            capture_output=True, text=True)
    return result.stdout.strip()


def port_conflict(port, bind="", skip_id=None):
    """Another proxy already owns this bind/port pair -> return its name."""
    port = str(valid_port(port) or '')
    bind = (bind or '').strip()
    for pid, proxy in load_proxies().get('proxies', {}).items():
        if pid == skip_id:
            continue
        if proxy_port(proxy) == port and proxy_bind(proxy) == bind:
            return proxy.get('name', pid)
    return None


def port_busy_on_system(port, bind=""):
    """Some other program is already listening there (ss based, best effort)."""
    port = valid_port(port)
    if not port:
        return False
    try:
        out = subprocess.run(['ss', '-ltnH'], capture_output=True, text=True,
                             timeout=10).stdout
    except Exception:
        return False
    for line in out.splitlines():
        fields = line.split()
        if len(fields) < 4:
            continue
        addr, _, lport = fields[3].rpartition(':')
        if lport != str(port):
            continue
        addr = addr.strip('[]')
        if not bind or addr in ('0.0.0.0', '*', '::', '', bind):
            return True
    return False


def group_instances(config=None):
    """proxies.json -> {key: {port, bind, domain, tag, users{name: secret}}}"""
    if config is None:
        config = load_proxies()
    groups = {}
    for proxy in config.get('proxies', {}).values():
        name = proxy.get('name')
        secret = proxy.get('secret')
        if not name or not secret:
            continue
        key = proxy_instance_key(proxy)
        group = groups.setdefault(key, {"port": proxy_port(proxy),
                                        "bind": proxy_bind(proxy),
                                        "domain": "", "tag": None, "users": {}})
        group['users'][name] = secret
        if proxy.get('domain') and not group['domain']:
            group['domain'] = proxy['domain']
        # AD_TAG is per process, so the first tag on a given port wins
        if proxy.get('tag') and not group['tag']:
            group['tag'] = proxy['tag']
    return groups


def render_instance_config(group):
    domain = group.get('domain') or get_default_domain()
    users = group.get('users', {})
    if users:
        body = ",\n".join(f'    "{n}": "{s}"' for n, s in users.items())
        users_block = "USERS = {\n" + body + "\n}"
    else:
        users_block = "USERS = {}"
    lines = ["# generated by MTProxy Manager - do not edit by hand",
             f"PORT = {group['port']}",
             users_block,
             f'TLS_DOMAIN = "{domain}"',
             'MODES = { "classic": False, "secure": False, "tls": True }',
             "# 60s stats period so usage/online numbers refresh every minute",
             "STATS_PRINT_PERIOD = 60"]
    bind = group.get('bind')
    if bind:
        if ':' in bind:                      # IPv6 literal
            lines.append(f'LISTEN_ADDR_IPV6 = "{bind}"')
            lines.append('LISTEN_ADDR_IPV4 = ""')
        else:
            lines.append(f'LISTEN_ADDR_IPV4 = "{bind}"')
            # do not also grab the IPv6 wildcard: it would clash with the other
            # instances that reuse the same port on a different IP
            lines.append('LISTEN_ADDR_IPV6 = ""')
    if group.get('tag'):
        lines.append(f'AD_TAG = "{group["tag"]}"')
    return "\n".join(lines) + "\n"


def write_instance_config(key, group):
    """Write the instance config, return True when the content changed."""
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    path = f"{INSTANCE_DIR}/{key}.py"
    new = render_instance_config(group)
    old = None
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                old = f.read()
        except OSError:
            old = None
    if old == new:
        return False
    with open(path, 'w') as f:
        f.write(new)
    return True


def ensure_instance_unit():
    unit = f"""[Unit]
Description=MTProto Proxy instance %i
After=network-online.target
Wants=network-online.target
StartLimitBurst=0

[Service]
Type=simple
ExecStart=/usr/bin/python3 {PROXY_DIR}/mtprotoproxy.py {INSTANCE_DIR}/%i.py
Restart=always
RestartSec=3
User=root
LimitNOFILE=infinity
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
"""
    old = ""
    if os.path.exists(INSTANCE_UNIT_FILE):
        try:
            with open(INSTANCE_UNIT_FILE, 'r') as f:
                old = f.read()
        except OSError:
            old = ""
    if old != unit:
        with open(INSTANCE_UNIT_FILE, 'w') as f:
            f.write(unit)
        subprocess.run(['systemctl', 'daemon-reload'], check=False)
        return True
    return False


def sync_instances(config=None, force_restart=False, quiet=True):
    """Make systemd match proxies.json: one service per bind-IP:port pair.

    Only instances whose config actually changed are restarted, so adding a
    proxy on port 8443 no longer kicks everybody off port 443.
    """
    if config is None:
        config = load_proxies()
    groups = group_instances(config)

    if not os.path.exists(PROXY_DIR):
        return groups

    os.makedirs(INSTANCE_DIR, exist_ok=True)
    unit_changed = ensure_instance_unit()

    try:
        existing = {f[:-3] for f in os.listdir(INSTANCE_DIR) if f.endswith('.py')}
    except OSError:
        existing = set()

    # ports with no proxies left: stop and forget them
    for key in existing - set(groups):
        subprocess.run(['systemctl', 'disable', '--now',
                        f"{INSTANCE_UNIT}@{key}.service"], check=False)
        try:
            os.remove(f"{INSTANCE_DIR}/{key}.py")
        except OSError:
            pass

    try:
        mtproxy_stats.flush_stats()
    except Exception:
        pass

    # the old single-port service is replaced by the per-port instances,
    # stop it first so it releases the port it was holding
    if groups and os.path.exists(f"/etc/systemd/system/{SERVICE_NAME}.service"):
        subprocess.run(['systemctl', 'disable', '--now', SERVICE_NAME], check=False)

    for key, group in groups.items():
        changed = write_instance_config(key, group)
        service = f"{INSTANCE_UNIT}@{key}.service"
        subprocess.run(['systemctl', 'enable', service], check=False)
        if force_restart or changed or unit_changed or instance_status(key) != 'active':
            subprocess.run(['systemctl', 'restart', service], check=False)
            if not quiet:
                print(f"{Colors.CYAN}\u21bb {group['bind'] or 'all IPs'}:{group['port']}"
                      f" ({len(group['users'])} proxies){Colors.NC}")
    return groups


def instances_overview():
    """Per-port summary for the dashboard: [(bind, port, count, state)]"""
    rows = []
    for key, group in sorted(group_instances().items(),
                             key=lambda kv: int(kv[1]['port'])):
        rows.append((group['bind'] or 'all IPs', group['port'],
                     len(group['users']), instance_status(key)))
    return rows


def install_mtproto_proxy():
    print(f"{Colors.CYAN}📦 Installing MTProto Proxy...{Colors.NC}")
    
    subprocess.run(['apt-get', 'update', '-qq'], check=False)
    subprocess.run(['apt-get', 'install', '-y', 'python3', 'python3-pip', 'git', 'curl', 'jq', 'ca-certificates'], check=False)
    
    if os.path.exists(PROXY_DIR):
        shutil.rmtree(PROXY_DIR)
    
    clone = subprocess.run(['git', 'clone', '--depth=1', 'https://github.com/alexbers/mtprotoproxy.git', PROXY_DIR],
                          capture_output=True, text=True)
    if clone.returncode != 0:
        print(f"{Colors.RED}❌ Failed to clone repository.{Colors.NC}")
        return False
    
    print(f"{Colors.CYAN}📦 Installing Python packages...{Colors.NC}")
    subprocess.run(['pip3', 'install', '--break-system-packages', 'cryptography', 'uvloop'], check=False)
    
    print("")
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
    else:
        public_ip = get_public_ip()
        set_default_server(public_ip)
        print(f"{Colors.GREEN}✅ Auto-detected public IP: {public_ip}{Colors.NC}")
    
    config_py = f"""PORT = {port}
USERS = {{}}
TLS_DOMAIN = "{domain}"
MODES = {{ "classic": False, "secure": False, "tls": True }}
# 60s stats period so usage/online numbers refresh every minute (default is 600)
STATS_PRINT_PERIOD = 60
"""
    with open(f"{PROXY_DIR}/config.py", 'w') as f:
        f.write(config_py)
    
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
    
    mtproxy_stats.ensure_stats_config(PROXY_DIR)
    print(f"{Colors.GREEN}✅ MTProto Proxy installed successfully!{Colors.NC}")
    return True

def add_proxy():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}➕ Add New Proxy{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print("")
    
    if not os.path.exists(PROXY_DIR):
        print(f"{Colors.RED}❌ MTProto Proxy not installed.{Colors.NC}")
        print(f"{Colors.YELLOW}💡 Please run 'mtproxy --setup' first.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    
    config = load_proxies()
    proxies = config.get('proxies', {})
    
    name = input(f"{Colors.BOLD}{Colors.PURPLE}Enter proxy name (e.g. US, EU, Main): {Colors.NC}").strip()
    if not name:
        name = f"Proxy-{len(proxies)+1}"
    
    server = input(f"{Colors.BOLD}{Colors.PURPLE}Enter server IP/domain for this proxy (leave empty for default): {Colors.NC}").strip()

    # ---- per-proxy port ----
    print("")
    print(f"{Colors.CYAN}\u2139\ufe0f  Each port runs as its own service, so every proxy can have its own port.{Colors.NC}")
    used = [f"{p.get('bind') or 'all'}:{proxy_port(p)}" for p in proxies.values()]
    if used:
        print(f"{Colors.YELLOW}Already in use: {', '.join(used)}{Colors.NC}")

    port = ""
    while True:
        raw = input(f"{Colors.BOLD}{Colors.PURPLE}Enter port for this proxy (Enter = default {get_default_port()}): {Colors.NC}").strip()
        if not raw:
            port = ""
            break
        if valid_port(raw) is None:
            print(f"{Colors.RED}\u274c Port must be a number between 1 and 65535.{Colors.NC}")
            continue
        port = str(valid_port(raw))
        break

    # ---- optional bind IP, for servers with several IPs ----
    bind = input(f"{Colors.BOLD}{Colors.PURPLE}Bind to a specific local IP? (Enter = all IPs): {Colors.NC}").strip()

    check_port = port or get_default_port()
    owner = port_conflict(check_port, bind)
    if owner:
        print(f"{Colors.YELLOW}\u26a0\ufe0f  '{owner}' already uses {bind or 'all IPs'}:{check_port}.{Colors.NC}")
        print(f"{Colors.YELLOW}   They would share that port (both secrets work on it).{Colors.NC}")
        if input(f"{Colors.BOLD}{Colors.PURPLE}Continue anyway? (y/N): {Colors.NC}").strip().lower() != 'y':
            print(f"{Colors.YELLOW}Cancelled.{Colors.NC}")
            input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
            return
    elif port_busy_on_system(check_port, bind):
        print(f"{Colors.RED}\u274c Port {check_port} is already used by another program on this server.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return

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
        "bind": bind,
        "domain": domain,
        "tag": tag if tag else None
    }
    proxies[proxy_id] = proxy
    config['proxies'] = proxies
    save_proxies(config)

    # rewrites every per-port config and (re)starts only what changed
    sync_instances(config)
    
    link = get_proxy_link(proxy)
    
    print("")
    print(f"{Colors.GREEN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"{Colors.GREEN}{Colors.BOLD}     🚀 Proxy Added Successfully!{Colors.NC}")
    print(f"{Colors.GREEN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"Name:   {Colors.WHITE}{name}{Colors.NC}")
    print(f"Server: {Colors.WHITE}{server if server else '(default)'}{Colors.NC}")
    shown_port = port or get_default_port()
    port_note = "" if port else " (default)"
    print(f"Port:   {Colors.WHITE}{shown_port}{Colors.NC}{port_note}")
    if bind:
        print(f"Bind:   {Colors.WHITE}{bind}{Colors.NC}")
    print(f"Secret: {Colors.WHITE}{secret}{Colors.NC}")
    if tag:
        print(f"Tag:    {Colors.WHITE}{tag}{Colors.NC}")
    print("")
    print(f"{Colors.BOLD}{Colors.CYAN}{link}{Colors.NC}")
    print("")
    print(f"{Colors.YELLOW}\U0001f4a1 Open the port in your firewall: ufw allow {shown_port}/tcp{Colors.NC}")
    print("")
    
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")

def remove_all_proxies():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.RED}🗑️ Delete ALL Proxies{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    config = load_proxies()
    proxies = config.get('proxies', {})
    if not proxies:
        print(f"{Colors.YELLOW}⚠️ No proxies to delete.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    print(f"{Colors.RED}⚠️ This will delete {len(proxies)} proxies: {list(proxies.keys())}{Colors.NC}")
    print("")
    confirm1 = input(f"{Colors.BOLD}{Colors.RED}Type 'delete all' to confirm (case sensitive): {Colors.NC}")
    if confirm1 != 'delete all':
        print(f"{Colors.YELLOW}Cancelled.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    print(f"{Colors.YELLOW}Are you sure? All proxies will be removed. Type 'yes': {Colors.NC}")
    confirm2 = input(f"{Colors.BOLD}{Colors.PURPLE}>{Colors.NC} ")
    if confirm2.lower() != 'yes':
        print(f"{Colors.YELLOW}Cancelled.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    config['proxies'] = {}
    save_proxies(config)
    # also drops every per-port instance
    sync_instances(config)
    print(f"{Colors.GREEN}✅ All {len(proxies)} proxies deleted.{Colors.NC}")
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
    
    ids, labels = list_proxies(config, show_status=True, show_links=False)
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
    
    del proxies[proxy_id]
    config['proxies'] = proxies
    save_proxies(config)

    # rewrites the affected port config, stops the instance if it is now empty
    sync_instances(config)
    
    print(f"{Colors.GREEN}✅ Proxy '{name}' removed successfully!{Colors.NC}")
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")

def tag_proxy():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}📝 Add Tag to Proxy{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print(f"{Colors.YELLOW}ℹ️  To get an AD Tag, send the proxy's SECRET to @MTProxybot on Telegram.{Colors.NC}")
    print(f"{Colors.YELLOW}   The SECRET is the 32-character hex string shown below.{Colors.NC}")
    print("")
    
    config = load_proxies()
    proxies = config.get('proxies', {})
    
    if not proxies:
        print(f"{Colors.YELLOW}⚠️ No proxies configured.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    
    # Show proxies with full secret
    ids, labels = list_proxies_for_tag(config)
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
    
    # Save changes to proxies.json correctly
    proxies[proxy_id] = proxy
    config['proxies'] = proxies
    save_proxies(config)
    
    restart_service()
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")

def set_default_server_menu():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}🌐 Set Default Server Settings{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print("")
    
    current_server = get_default_server()
    if current_server:
        print(f"{Colors.YELLOW}Current default server: {Colors.WHITE}{current_server}{Colors.NC}")
    else:
        public_ip = get_public_ip()
        print(f"{Colors.YELLOW}Auto-detected public IP: {Colors.WHITE}{public_ip}{Colors.NC}")
    
    print(f"{Colors.CYAN}Default port: {Colors.WHITE}{get_default_port()}{Colors.NC}")
    print(f"{Colors.CYAN}Default domain: {Colors.WHITE}{get_default_domain()}{Colors.NC}")
    print("")
    print(f"{Colors.CYAN}ℹ️  Changes will be applied to the running proxy service.{Colors.NC}")
    print("")
    
    # 1. Server address
    new_addr = input(f"{Colors.BOLD}{Colors.PURPLE}Enter default server IP/domain (leave empty to auto-detect): {Colors.NC}").strip()
    if new_addr:
        set_default_server(new_addr)
        print(f"{Colors.GREEN}✅ Default server set to: {new_addr}{Colors.NC}")
    else:
        public_ip = get_public_ip()
        set_default_server(public_ip)
        print(f"{Colors.GREEN}✅ Switched to auto-detected IP: {public_ip}{Colors.NC}")
    
    # 2. Port
    new_port = input(f"{Colors.BOLD}{Colors.PURPLE}Enter default port (current: {get_default_port()}): {Colors.NC}").strip()
    if new_port:
        set_default_port(new_port)
        print(f"{Colors.GREEN}✅ Default port set to: {new_port}{Colors.NC}")
    
    # 3. Domain
    new_domain = input(f"{Colors.BOLD}{Colors.PURPLE}Enter default TLS domain (current: {get_default_domain()}): {Colors.NC}").strip()
    if new_domain:
        set_default_domain(new_domain)
        print(f"{Colors.GREEN}✅ Default domain set to: {new_domain}{Colors.NC}")
    
    # ========== Apply changes to config.py and restart service ==========
    if new_port or new_domain:
        print(f"{Colors.CYAN}🔄 Applying changes to proxy configuration...{Colors.NC}")
        apply_config_changes()
    
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")

def apply_config_changes():
    """Push the new default port/domain into every instance that inherits them"""
    sync_instances()
    print(f"{Colors.GREEN}\u2705 Settings applied, affected ports restarted.{Colors.NC}")


def _legacy_apply_config_changes():
    """Kept for reference: single-service behaviour before per-port support"""
    port = get_default_port()
    domain = get_default_domain()
    
    # Update config.py
    config_py_path = f"{PROXY_DIR}/config.py"
    if os.path.exists(config_py_path):
        with open(config_py_path, 'r') as f:
            content = f.read()
        
        # Replace PORT
        content = re.sub(r'PORT\s*=\s*\d+', f'PORT = {port}', content)
        # Replace TLS_DOMAIN
        content = re.sub(r'TLS_DOMAIN\s*=\s*"[^"]*"', f'TLS_DOMAIN = "{domain}"', content)
        
        with open(config_py_path, 'w') as f:
            f.write(content)
        
        # Restart service
        restart_service()
        print(f"{Colors.GREEN}✅ Proxy restarted with new settings.{Colors.NC}")
    else:
        print(f"{Colors.RED}❌ Config file not found at {config_py_path}.{Colors.NC}")

def change_proxy_port():
    """Move an existing proxy to another port / bind IP."""
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}\U0001f500 Change Proxy Port / Bind IP{Colors.NC}")
    print(f"{Colors.CYAN}-----------------------------------------------------------------{Colors.NC}")

    config = load_proxies()
    proxies = config.get('proxies', {})
    if not proxies:
        print(f"{Colors.YELLOW}\u26a0\ufe0f No proxies configured.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return

    ids, _ = list_proxies(config, show_status=True, show_links=False)
    print("")
    try:
        choice = int(input(f"{Colors.BOLD}{Colors.PURPLE}Enter number (1-{len(ids)}): {Colors.NC}").strip())
        if choice < 1 or choice > len(ids):
            raise ValueError
    except ValueError:
        print(f"{Colors.RED}\u274c Invalid selection.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return

    proxy_id = ids[choice - 1]
    proxy = proxies[proxy_id]
    print("")
    print(f"{Colors.CYAN}Current: {Colors.WHITE}{proxy_bind(proxy) or 'all IPs'}:{proxy_port(proxy)}{Colors.NC}")

    raw = input(f"{Colors.BOLD}{Colors.PURPLE}New port (Enter = keep {proxy_port(proxy)}, 'd' = follow default): {Colors.NC}").strip()
    if raw.lower() == 'd':
        new_port = ""
    elif not raw:
        new_port = proxy.get('port', '')
    elif valid_port(raw) is None:
        print(f"{Colors.RED}\u274c Port must be a number between 1 and 65535.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    else:
        new_port = str(valid_port(raw))

    raw_bind = input(f"{Colors.BOLD}{Colors.PURPLE}Bind IP (Enter = keep, '-' = all IPs): {Colors.NC}").strip()
    if raw_bind == '-':
        new_bind = ""
    elif not raw_bind:
        new_bind = proxy_bind(proxy)
    else:
        new_bind = raw_bind

    check_port = new_port or get_default_port()
    owner = port_conflict(check_port, new_bind, skip_id=proxy_id)
    if owner:
        print(f"{Colors.YELLOW}\u26a0\ufe0f  '{owner}' already uses {new_bind or 'all IPs'}:{check_port}, they would share it.{Colors.NC}")
        if input(f"{Colors.BOLD}{Colors.PURPLE}Continue? (y/N): {Colors.NC}").strip().lower() != 'y':
            print(f"{Colors.YELLOW}Cancelled.{Colors.NC}")
            input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
            return

    proxy['port'] = new_port
    proxy['bind'] = new_bind
    proxies[proxy_id] = proxy
    config['proxies'] = proxies
    save_proxies(config)

    sync_instances(config)

    print("")
    print(f"{Colors.GREEN}\u2705 {proxy.get('name')} now on {new_bind or 'all IPs'}:{check_port}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{get_proxy_link(proxy)}{Colors.NC}")
    print(f"{Colors.YELLOW}\U0001f4a1 Open the new port in your firewall: ufw allow {check_port}/tcp{Colors.NC}")
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")


def ports_menu():
    """Show every per-port instance and act on them."""
    while True:
        clear_screen()
        print(f"{Colors.BOLD}{Colors.GREEN}\U0001f50c Ports / Instances{Colors.NC}")
        print(f"{Colors.CYAN}-----------------------------------------------------------------{Colors.NC}")
        rows = instances_overview()
        if not rows:
            print(f"{Colors.YELLOW}\u26a0\ufe0f No proxies yet.{Colors.NC}")
        for bind, port, count, state in rows:
            color = Colors.GREEN if state == 'active' else Colors.RED
            print(f"  {color}\u25cf{Colors.NC} {Colors.WHITE}{bind}:{port}{Colors.NC} "
                  f"| {count} proxies | {color}{state}{Colors.NC}")
        print("")
        print(f"  {Colors.GREEN}1.{Colors.NC} \U0001f500 Change a proxy's port / bind IP")
        print(f"  {Colors.GREEN}2.{Colors.NC} \u267b\ufe0f  Re-sync and restart all ports")
        print(f"  {Colors.GREEN}0.{Colors.NC} Back")
        print(f"{Colors.CYAN}-----------------------------------------------------------------{Colors.NC}")
        choice = input(f"{Colors.BOLD}{Colors.PURPLE}Select option: {Colors.NC}").strip()
        if choice == '1':
            change_proxy_port()
        elif choice == '2':
            print(f"{Colors.CYAN}\U0001f504 Syncing...{Colors.NC}")
            sync_instances(force_restart=True, quiet=False)
            print(f"{Colors.GREEN}\u2705 Done.{Colors.NC}")
            time.sleep(1)
        elif choice == '0':
            break
        else:
            print(f"{Colors.RED}\u274c Invalid option{Colors.NC}")
            time.sleep(1)


def service_menu():
    while True:
        clear_screen()
        print(f"{Colors.BOLD}{Colors.GREEN}⚙️ Service Management{Colors.NC}")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        status = get_proxy_status()
        status_text = f"{Colors.GREEN}Active{Colors.NC}" if status == "active" else f"{Colors.RED}Inactive{Colors.NC}" if status == "inactive" else f"{Colors.YELLOW}Not installed{Colors.NC}"
        print(f"  Status: {status_text}")
        for bind, port, count, state in instances_overview():
            color = Colors.GREEN if state == 'active' else Colors.RED
            print(f"    {color}\u25cf{Colors.NC} {bind}:{port} ({count} proxies)")
        print("")
        print(f"  {Colors.GREEN}1.{Colors.NC} Start")
        print(f"  {Colors.GREEN}2.{Colors.NC} Stop")
        print(f"  {Colors.GREEN}3.{Colors.NC} Restart")
        print(f"  {Colors.GREEN}4.{Colors.NC} Status")
        print(f"  {Colors.GREEN}5.{Colors.NC} View Logs (last 30 lines)")
        print(f"  {Colors.GREEN}6.{Colors.NC} 📡 Live Log Viewer")
        print(f"  {Colors.GREEN}7.{Colors.NC} ♻️ Reset usage counters")
        print(f"  {Colors.GREEN}0.{Colors.NC} Back")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        choice = input(f"{Colors.BOLD}{Colors.PURPLE}Select option: {Colors.NC}").strip()
        
        if choice == '1':
            for key in (list(group_instances()) or [None]):
                target = f"{INSTANCE_UNIT}@{key}.service" if key else SERVICE_NAME
                subprocess.run(['systemctl', 'start', target], check=False)
            print(f"{Colors.GREEN}\u2705 Started{Colors.NC}")
            time.sleep(1)
        elif choice == '2':
            for key in (list(group_instances()) or [None]):
                target = f"{INSTANCE_UNIT}@{key}.service" if key else SERVICE_NAME
                subprocess.run(['systemctl', 'stop', target], check=False)
            print(f"{Colors.GREEN}\u2705 Stopped{Colors.NC}")
            time.sleep(1)
        elif choice == '3':
            restart_service()
            print(f"{Colors.GREEN}✅ Restarted{Colors.NC}")
            time.sleep(1)
        elif choice == '4':
            units = [f"{INSTANCE_UNIT}@{k}.service" for k in group_instances()] or [SERVICE_NAME]
            subprocess.run(['systemctl', 'status'] + units, check=False)
            input(f"{Colors.YELLOW}Press Enter...{Colors.NC}")
        elif choice == '5':
            args = ['journalctl', '-n', '30', '--no-pager']
            for unit in ([f"{INSTANCE_UNIT}@{k}.service" for k in group_instances()] or [SERVICE_NAME]):
                args += ['-u', unit]
            subprocess.run(args, check=False)
            input(f"{Colors.YELLOW}Press Enter...{Colors.NC}")
        elif choice == '6':
            mtproxy_stats.view_live_logs()
        elif choice == '7':
            confirm = input(f"{Colors.RED}Reset stored usage for ALL proxies? (y/N): {Colors.NC}").strip().lower()
            if confirm == 'y':
                mtproxy_stats.reset_usage()
                print(f"{Colors.GREEN}✅ Usage counters reset.{Colors.NC}")
            time.sleep(1)
        elif choice == '0':
            break
        else:
            print(f"{Colors.RED}❌ Invalid option{Colors.NC}")
            time.sleep(1)

def uninstall():
    clear_screen()
    print(f"{Colors.RED}⚠️ Are you sure you want to uninstall MTProxy? (y/N){Colors.NC}")
    confirm = input().strip().lower()
    if confirm != 'y':
        print(f"{Colors.YELLOW}Cancelled.{Colors.NC}")
        time.sleep(1)
        return
    
    subprocess.run(['systemctl', 'stop', SERVICE_NAME], check=False)
    subprocess.run(['systemctl', 'disable', SERVICE_NAME], check=False)
    subprocess.run(['rm', '-f', f'/etc/systemd/system/{SERVICE_NAME}.service'], check=False)

    # per-port instances
    for key in list(group_instances()):
        subprocess.run(['systemctl', 'disable', '--now',
                        f"{INSTANCE_UNIT}@{key}.service"], check=False)
    subprocess.run(['rm', '-f', INSTANCE_UNIT_FILE], check=False)
    subprocess.run(['systemctl', 'daemon-reload'], check=False)
    
    subprocess.run(['rm', '-rf', PROXY_DIR], check=False)
    subprocess.run(['rm', '-rf', CONFIG_DIR], check=False)
    subprocess.run(['rm', '-f', '/usr/local/bin/mtproxy'], check=False)
    
    try:
        mtproxy_socks.uninstall()
    except Exception:
        pass
    
    print(f"{Colors.GREEN}✅ Uninstallation completed!{Colors.NC}")
    time.sleep(1)

def setup():
    print(f"{Colors.BOLD}{Colors.GREEN}🔧 Setting up MTProto Proxy...{Colors.NC}")
    print("")
    install_mtproto_proxy()
    print("")
    print(f"{Colors.GREEN}✅ Setup completed! Run 'mtproxy' to manage proxies.{Colors.NC}")

def update_proxy():
    """Update the proxy manager to the latest version"""
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}🔄 Update MTProxy Manager{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print("")
    
    print(f"{Colors.YELLOW}This will update the MTProxy Manager to the latest version.{Colors.NC}")
    print(f"{Colors.YELLOW}Your existing proxies and settings will be preserved.{Colors.NC}")
    print("")
    
    confirm = input(f"{Colors.BOLD}{Colors.PURPLE}Continue with update? (y/N): {Colors.NC}").strip().lower()
    if confirm != 'y':
        print(f"{Colors.YELLOW}Update cancelled.{Colors.NC}")
        input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
        return
    
    print(f"{Colors.CYAN}🔄 Running update script...{Colors.NC}")
    
    # Run the update script
    result = subprocess.run(
        ['bash', '-c', 'bash <(curl -Ls https://raw.githubusercontent.com/Mahersaber2024/MTProxy-Advanced-/main/update.sh)'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"{Colors.GREEN}✅ Update completed successfully!{Colors.NC}")
        print(f"{Colors.YELLOW}💡 Please restart the program to see changes.{Colors.NC}")
    else:
        print(f"{Colors.RED}❌ Update failed!{Colors.NC}")
        print(f"{Colors.RED}Error: {result.stderr}{Colors.NC}")
    
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
    
def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--setup':
        setup()
        sys.exit(0)
    
    # Existing installs: make sure stats print every 60s instead of every 600s
    if os.path.exists(f"{PROXY_DIR}/config.py"):
        mtproxy_stats.ensure_stats_config(PROXY_DIR)
    # Migrate/repair the per-port instances (no-op when nothing changed)
    if os.path.exists(PROXY_DIR):
        try:
            sync_instances()
        except Exception as exc:
            print(f"{Colors.YELLOW}\u26a0\ufe0f Could not sync port instances: {exc}{Colors.NC}")
    
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
            print(f"  {Colors.YELLOW}💡 Run 'mtproxy --setup' to install the proxy{Colors.NC}")
        elif status == "active":
            print(f"  {Colors.GREEN}●{Colors.NC} Proxy: {Colors.GREEN}Active{Colors.NC}")
            print(f"  {Colors.BLUE}\u25cf{Colors.NC} Default: {Colors.WHITE}{default_server if default_server else 'auto-detect'}:{default_port}{Colors.NC}")
            ports = instances_overview()
            if ports:
                summary = ', '.join(f"{b}:{p}" for b, p, _, _ in ports)
                print(f"  {Colors.BLUE}\u25cf{Colors.NC} Listening: {Colors.WHITE}{summary}{Colors.NC}")
        else:
            print(f"  {Colors.RED}●{Colors.NC} Proxy: {Colors.RED}Inactive{Colors.NC}")
        
        print(f"  {Colors.BLUE}●{Colors.NC} Proxies: {Colors.WHITE}{proxy_count}{Colors.NC}")
        
        socks_status = mtproxy_socks.service_status()
        socks_count = len(mtproxy_socks.load_socks().get('socks', {}))
        if socks_status != 'not_installed' or socks_count:
            socks_color = Colors.GREEN if socks_status == 'active' else Colors.RED
            socks_word = 'active' if socks_status == 'active' else 'stopped'
            print(f"  {socks_color}●{Colors.NC} SOCKS5: {Colors.WHITE}{socks_count}{Colors.NC} ({socks_color}{socks_word}{Colors.NC})")
        
        if proxy_count > 0 and status == "active":
            print("")
            list_proxies(config, show_status=True, show_links=True)
        
        print("")
        print(f"{Colors.BLUE}📋 Menu:{Colors.NC}")
        if not os.path.exists(PROXY_DIR):
            print(f"  {Colors.GREEN}1.{Colors.NC} 🔧 Setup Proxy (install and configure)")
        else:
            print(f"  {Colors.GREEN}1.{Colors.NC} ➕ Add Proxy (with custom IP/domain)")
            print(f"  {Colors.GREEN}2.{Colors.NC} ⚙️ Service Management")
            print(f"  {Colors.GREEN}3.{Colors.NC} 📝 Add Tag to Proxy")
            print(f"  {Colors.GREEN}4.{Colors.NC} ➖ Remove Proxy")
            print(f"  {Colors.GREEN}5.{Colors.NC} 🌐 Edit Default Server Settings")
            print(f"  {Colors.GREEN}6.{Colors.NC} 🔄 Update to Latest Version")
            print(f"  {Colors.GREEN}7.{Colors.NC} 🧦 SOCKS5 Proxy (non-Telegram)")
            print(f"  {Colors.GREEN}8.{Colors.NC} \U0001f5d1\ufe0f Delete ALL Proxies")
            print(f"  {Colors.GREEN}9.{Colors.NC} \U0001f50c Ports / Instances (per-proxy port)")
        print(f"  {Colors.GREEN}0.{Colors.NC} 🚪 Exit")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        choice = input(f"{Colors.BOLD}{Colors.PURPLE}Select an option: {Colors.NC}").strip()
        
        if not os.path.exists(PROXY_DIR):
            if choice == '1':
                setup()
            elif choice == '0':
                print(f"{Colors.GREEN}👋 Goodbye!{Colors.NC}")
                sys.exit(0)
            else:
                print(f"{Colors.RED}❌ Invalid option. Please run setup first.{Colors.NC}")
                time.sleep(1)
        else:
            if choice == '1':
                add_proxy()
            elif choice == '2':
                service_menu()
            elif choice == '3':
                tag_proxy()
            elif choice == '4':
                remove_proxy()
            elif choice == '5':
                set_default_server_menu()
            elif choice == '6':
                update_proxy()
            elif choice == '7':
                mtproxy_socks.menu()
            elif choice == '8':
                remove_all_proxies()
            elif choice == '9':
                ports_menu()
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
