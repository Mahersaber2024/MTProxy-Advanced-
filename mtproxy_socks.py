#!/usr/bin/env python3
# mtproxy_socks.py - SOCKS5 proxy manager (non-Telegram usage)
# Runs alongside MTProto proxy as its own systemd service: mtsocks
# Accepts the ip:port:user:pass format, e.g. 143.14.59.117:823:proxyuser:proxyuser1

import os
import re
import json
import time
import random
import string
import shutil
import subprocess

CONFIG_DIR = "/etc/mtpulse"
SOCKS_FILE = f"{CONFIG_DIR}/socks.json"
USAGE_FILE = f"{CONFIG_DIR}/socks_usage.json"
SERVICE_NAME = "mtsocks"
SERVICE_FILE = f"/etc/systemd/system/{SERVICE_NAME}.service"
SERVER_BIN = "/usr/local/bin/socks5_server.py"
DEFAULT_PORT = 1080


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


def pause():
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")


def _ask(prompt):
    return input(f"{Colors.BOLD}{Colors.PURPLE}{prompt}{Colors.NC}").strip()


# ------------------------------------------------------------------ config io
def load_socks():
    if not os.path.exists(SOCKS_FILE):
        return {"socks": {}}
    try:
        with open(SOCKS_FILE, 'r') as f:
            data = json.load(f)
        data.setdefault("socks", {})
        return data
    except Exception:
        return {"socks": {}}


def save_socks(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = SOCKS_FILE + ".tmp"
    with open(tmp, 'w') as f:
        json.dump(cfg, f, indent=2)
    os.replace(tmp, SOCKS_FILE)


def load_usage():
    try:
        with open(USAGE_FILE, 'r') as f:
            return (json.load(f) or {}).get("totals", {}) or {}
    except Exception:
        return {}


def format_bytes(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "0 B"
    if v <= 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if v < 1024.0:
            return f"{v:.0f} {unit}" if unit == 'B' else f"{v:.2f} {unit}"
        v /= 1024.0
    return f"{v:.2f} PB"


def get_public_ip():
    try:
        ip = subprocess.run(['curl', '-s', '--max-time', '3', 'https://api.ipify.org'],
                            capture_output=True, text=True).stdout.strip()
        if ip:
            return ip
    except Exception:
        pass
    return ""


def service_status():
    if not os.path.exists(SERVICE_FILE):
        return "not_installed"
    res = subprocess.run(['systemctl', 'is-active', SERVICE_NAME],
                         capture_output=True, text=True)
    return "active" if res.stdout.strip() == "active" else "inactive"


def reload_service(restart=False):
    """SIGHUP reloads users without dropping live sessions; restart if needed."""
    if service_status() == "not_installed":
        return
    if restart or service_status() != "active":
        subprocess.run(['systemctl', 'restart', SERVICE_NAME], check=False)
    else:
        subprocess.run(['systemctl', 'reload-or-restart', SERVICE_NAME], check=False)


def open_firewall(port):
    try:
        if shutil.which('ufw'):
            out = subprocess.run(['ufw', 'status'], capture_output=True, text=True).stdout
            if 'Status: active' in out:
                subprocess.run(['ufw', 'allow', f'{port}/tcp'], check=False,
                               capture_output=True)
    except Exception:
        pass


def rand_str(n=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))


# -------------------------------------------------------------------- install
def install():
    print(f"{Colors.CYAN}📦 Installing SOCKS5 service...{Colors.NC}")
    if not os.path.exists(SERVER_BIN):
        # try to find the server next to this module
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'socks5_server.py')
        if os.path.exists(here):
            shutil.copyfile(here, SERVER_BIN)
        else:
            print(f"{Colors.RED}❌ socks5_server.py not found. Run the updater first.{Colors.NC}")
            return False
    os.chmod(SERVER_BIN, 0o755)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(SOCKS_FILE):
        save_socks({"socks": {}})

    unit = f"""[Unit]
Description=SOCKS5 Proxy Service (MTProxy Manager)
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {SERVER_BIN}
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=2
User=root
LimitNOFILE=65535
StartLimitBurst=0

[Install]
WantedBy=multi-user.target
"""
    with open(SERVICE_FILE, 'w') as f:
        f.write(unit)
    subprocess.run(['systemctl', 'daemon-reload'], check=False)
    subprocess.run(['systemctl', 'enable', SERVICE_NAME], check=False)
    subprocess.run(['systemctl', 'restart', SERVICE_NAME], check=False)
    print(f"{Colors.GREEN}✅ SOCKS5 service installed.{Colors.NC}")
    return True


# ----------------------------------------------------------------- formatting
def socks_link(entry):
    return (f"socks5://{entry['username']}:{entry['password']}"
            f"@{entry.get('server') or '0.0.0.0'}:{entry['port']}")


def socks_plain(entry):
    return (f"{entry.get('server') or '0.0.0.0'}:{entry['port']}:"
            f"{entry['username']}:{entry['password']}")


def tg_socks_link(entry):
    return (f"tg://socks?server={entry.get('server') or '0.0.0.0'}&port={entry['port']}"
            f"&user={entry['username']}&pass={entry['password']}")


def list_socks(cfg=None, show_links=True):
    cfg = cfg or load_socks()
    entries = cfg.get("socks", {})
    if not entries:
        print(f"{Colors.YELLOW}⚠️ No SOCKS5 proxies configured.{Colors.NC}")
        return []
    usage = load_usage()
    status = service_status()
    print(f"{Colors.BLUE}🧦 SOCKS5 Proxies:{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    ids = []
    for idx, (sid, e) in enumerate(entries.items(), 1):
        ids.append(sid)
        u = usage.get(sid, {})
        total = int(u.get('up', 0)) + int(u.get('down', 0))
        enabled = e.get('enabled', True)
        if not enabled:
            st = f"{Colors.YELLOW}● Disabled{Colors.NC}"
        elif status == "active":
            st = f"{Colors.GREEN}● Active{Colors.NC}"
        else:
            st = f"{Colors.RED}● Stopped{Colors.NC}"
        print(f"  {idx}. {Colors.BOLD}{e.get('name', sid)}{Colors.NC} | "
              f"@ {e.get('server') or 'auto'}:{e.get('port')} | "
              f"👤 {Colors.WHITE}{e.get('username')}{Colors.NC}:{Colors.WHITE}{e.get('password')}{Colors.NC} | "
              f"{st} | {Colors.BLUE}● Online: {Colors.WHITE}{u.get('current', 0)}{Colors.NC} | "
              f"{Colors.BLUE}● Peak: {Colors.WHITE}{u.get('peak', 0)}{Colors.NC} | "
              f"{Colors.BLUE}● Usage: {Colors.WHITE}{format_bytes(total)}{Colors.NC} "
              f"({Colors.CYAN}↑{format_bytes(u.get('up', 0))} ↓{format_bytes(u.get('down', 0))}{Colors.NC})")
        if show_links:
            print(f"     {Colors.CYAN}🔗 {socks_link(e)}{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    return ids


# ----------------------------------------------------------------- operations
PASTE_RE = re.compile(
    r'^(?:socks5?h?://)?(?:(?P<u1>[^:@/\s]+):(?P<p1>[^:@/\s]+)@)?'
    r'(?P<host>\[[0-9a-fA-F:]+\]|[^:@/\s]+):(?P<port>\d{1,5})'
    r'(?::(?P<u2>[^:@/\s]+):(?P<p2>[^:@/\s]+))?$')


def parse_paste(text):
    """Accept ip:port:user:pass, socks5://user:pass@ip:port, or ip:port."""
    m = PASTE_RE.match(text.strip())
    if not m:
        return None
    host = m.group('host').strip('[]')
    port = int(m.group('port'))
    if not (0 < port < 65536):
        return None
    user = m.group('u2') or m.group('u1')
    pwd = m.group('p2') or m.group('p1')
    return {"server": host, "port": port, "username": user, "password": pwd}


def add_socks():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}➕ Add SOCKS5 Proxy{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print(f"{Colors.YELLOW}ℹ️  Paste in any of these formats, or press Enter to fill in manually:{Colors.NC}")
    print(f"{Colors.WHITE}   143.14.59.117:823:proxyuser:proxyuser1{Colors.NC}")
    print(f"{Colors.WHITE}   socks5://proxyuser:proxyuser1@143.14.59.117:823{Colors.NC}")
    print("")

    if service_status() == "not_installed":
        if not install():
            pause()
            return

    cfg = load_socks()
    entries = cfg["socks"]

    parsed = None
    paste = _ask("Paste proxy string (or Enter to skip): ")
    if paste:
        parsed = parse_paste(paste)
        if not parsed:
            print(f"{Colors.RED}❌ Could not parse that. Expected ip:port:user:pass{Colors.NC}")
            pause()
            return

    if parsed:
        server = parsed['server']
        port = parsed['port']
        username = parsed['username'] or f"user{rand_str(4)}"
        password = parsed['password'] or rand_str(12)
    else:
        server = _ask("Server IP/domain (Enter = auto-detect): ") or get_public_ip() or "0.0.0.0"
        port_in = _ask(f"Port (Enter = {DEFAULT_PORT}): ")
        try:
            port = int(port_in) if port_in else DEFAULT_PORT
        except ValueError:
            print(f"{Colors.RED}❌ Invalid port.{Colors.NC}")
            pause()
            return
        username = _ask("Username (Enter = random): ") or f"user{rand_str(4)}"
        password = _ask("Password (Enter = random): ") or rand_str(12)

    name = _ask(f"Name (Enter = Socks-{len(entries)+1}): ") or f"Socks-{len(entries)+1}"

    # conflict checks
    for sid, e in entries.items():
        if int(e.get('port', 0)) == port and e.get('username') == username:
            print(f"{Colors.RED}❌ {username} already exists on port {port}.{Colors.NC}")
            pause()
            return

    sid = f"s{int(time.time())}{random.randint(10, 99)}"
    entry = {
        "name": name, "server": server, "port": port,
        "username": username, "password": password,
        "enabled": True, "created": int(time.time()),
    }
    entries[sid] = entry
    cfg["socks"] = entries
    save_socks(cfg)
    open_firewall(port)
    reload_service(restart=True)
    time.sleep(1)

    print("")
    print(f"{Colors.GREEN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"{Colors.GREEN}{Colors.BOLD}     🧦 SOCKS5 Proxy Added!{Colors.NC}")
    print(f"{Colors.GREEN}{Colors.BOLD}════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"Name:     {Colors.WHITE}{name}{Colors.NC}")
    print(f"Server:   {Colors.WHITE}{server}:{port}{Colors.NC}")
    print(f"User:     {Colors.WHITE}{username}{Colors.NC}")
    print(f"Password: {Colors.WHITE}{password}{Colors.NC}")
    print("")
    print(f"{Colors.BOLD}{Colors.CYAN}{socks_link(entry)}{Colors.NC}")
    print(f"{Colors.WHITE}{socks_plain(entry)}{Colors.NC}")
    print(f"{Colors.CYAN}Telegram-compatible: {tg_socks_link(entry)}{Colors.NC}")
    print("")
    if service_status() != "active":
        print(f"{Colors.RED}⚠️ Service is not active. Check: journalctl -u {SERVICE_NAME} -n 30{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}💡 Works with browsers, curl, SSH, torrent clients, any SOCKS5 app.{Colors.NC}")
    pause()


def remove_socks():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.RED}➖ Remove SOCKS5 Proxy{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    cfg = load_socks()
    ids = list_socks(cfg, show_links=False)
    if not ids:
        pause()
        return
    try:
        choice = int(_ask(f"Enter number (1-{len(ids)}): "))
        if not 1 <= choice <= len(ids):
            raise ValueError
    except ValueError:
        print(f"{Colors.RED}❌ Invalid selection.{Colors.NC}")
        pause()
        return
    sid = ids[choice - 1]
    name = cfg["socks"][sid].get('name', sid)
    if _ask(f"Remove '{name}'? (y/N): ").lower() != 'y':
        print(f"{Colors.YELLOW}Cancelled.{Colors.NC}")
        pause()
        return
    del cfg["socks"][sid]
    save_socks(cfg)
    reload_service(restart=True)
    print(f"{Colors.GREEN}✅ '{name}' removed.{Colors.NC}")
    pause()


def toggle_socks():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.YELLOW}⏯️ Enable / Disable SOCKS5 Proxy{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    cfg = load_socks()
    ids = list_socks(cfg, show_links=False)
    if not ids:
        pause()
        return
    try:
        choice = int(_ask(f"Enter number (1-{len(ids)}): "))
        if not 1 <= choice <= len(ids):
            raise ValueError
    except ValueError:
        print(f"{Colors.RED}❌ Invalid selection.{Colors.NC}")
        pause()
        return
    sid = ids[choice - 1]
    e = cfg["socks"][sid]
    e["enabled"] = not e.get("enabled", True)
    save_socks(cfg)
    reload_service(restart=True)
    print(f"{Colors.GREEN}✅ '{e.get('name', sid)}' is now "
          f"{'enabled' if e['enabled'] else 'disabled'}.{Colors.NC}")
    pause()


def reset_usage():
    clear_screen()
    if _ask(f"{Colors.RED}Reset ALL SOCKS5 usage counters? (y/N): {Colors.NC}").lower() != 'y':
        return
    try:
        if os.path.exists(USAGE_FILE):
            os.remove(USAGE_FILE)
        reload_service(restart=True)
        print(f"{Colors.GREEN}✅ Usage counters reset.{Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}❌ {e}{Colors.NC}")
    pause()


def service_menu():
    while True:
        clear_screen()
        print(f"{Colors.BOLD}{Colors.GREEN}⚙️ SOCKS5 Service{Colors.NC}")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        st = service_status()
        st_text = (f"{Colors.GREEN}Active{Colors.NC}" if st == "active"
                   else f"{Colors.RED}Inactive{Colors.NC}" if st == "inactive"
                   else f"{Colors.YELLOW}Not installed{Colors.NC}")
        print(f"  Status: {st_text}")
        print("")
        print(f"  {Colors.GREEN}1.{Colors.NC} Start")
        print(f"  {Colors.GREEN}2.{Colors.NC} Stop")
        print(f"  {Colors.GREEN}3.{Colors.NC} Restart")
        print(f"  {Colors.GREEN}4.{Colors.NC} Status")
        print(f"  {Colors.GREEN}5.{Colors.NC} Logs (last 40 lines)")
        print(f"  {Colors.GREEN}0.{Colors.NC} Back")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        c = _ask("Select option: ")
        if c == '1':
            subprocess.run(['systemctl', 'start', SERVICE_NAME], check=False)
        elif c == '2':
            subprocess.run(['systemctl', 'stop', SERVICE_NAME], check=False)
        elif c == '3':
            subprocess.run(['systemctl', 'restart', SERVICE_NAME], check=False)
        elif c == '4':
            subprocess.run(['systemctl', 'status', SERVICE_NAME, '--no-pager'], check=False)
            pause()
        elif c == '5':
            subprocess.run(['journalctl', '-u', SERVICE_NAME, '-n', '40', '--no-pager'],
                           check=False)
            pause()
        elif c == '0':
            return
        time.sleep(0.6)


def test_socks():
    """Verify a proxy actually works end to end."""
    clear_screen()
    print(f"{Colors.BOLD}{Colors.GREEN}🧪 Test SOCKS5 Proxy{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    cfg = load_socks()
    ids = list_socks(cfg, show_links=False)
    if not ids:
        pause()
        return
    try:
        choice = int(_ask(f"Enter number (1-{len(ids)}): "))
        if not 1 <= choice <= len(ids):
            raise ValueError
    except ValueError:
        print(f"{Colors.RED}❌ Invalid selection.{Colors.NC}")
        pause()
        return
    e = cfg["socks"][ids[choice - 1]]
    target = f"{e['username']}:{e['password']}@127.0.0.1:{e['port']}"
    print(f"{Colors.CYAN}Testing locally through 127.0.0.1:{e['port']} ...{Colors.NC}")
    res = subprocess.run(
        ['curl', '-s', '--max-time', '15', '--socks5-hostname', target,
         'https://api.ipify.org'], capture_output=True, text=True)
    ip = res.stdout.strip()
    if res.returncode == 0 and ip:
        print(f"{Colors.GREEN}✅ Working. Exit IP: {Colors.WHITE}{ip}{Colors.NC}")
        print(f"{Colors.YELLOW}💡 If it fails from outside, port {e['port']} is blocked "
              f"by a firewall/provider.{Colors.NC}")
    else:
        print(f"{Colors.RED}❌ Test failed (curl exit {res.returncode}).{Colors.NC}")
        print(f"{Colors.YELLOW}Check: journalctl -u {SERVICE_NAME} -n 30{Colors.NC}")
    pause()


def uninstall():
    subprocess.run(['systemctl', 'stop', SERVICE_NAME], check=False)
    subprocess.run(['systemctl', 'disable', SERVICE_NAME], check=False)
    subprocess.run(['rm', '-f', SERVICE_FILE], check=False)
    subprocess.run(['systemctl', 'daemon-reload'], check=False)
    subprocess.run(['rm', '-f', SERVER_BIN], check=False)


def menu():
    while True:
        clear_screen()
        print(f"{Colors.BOLD}{Colors.CYAN}🧦 SOCKS5 Proxy (non-Telegram){Colors.NC}")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        st = service_status()
        if st == "not_installed":
            print(f"  {Colors.YELLOW}● Service: Not installed{Colors.NC}")
        elif st == "active":
            print(f"  {Colors.GREEN}● Service: Active{Colors.NC}")
        else:
            print(f"  {Colors.RED}● Service: Stopped{Colors.NC}")
        print("")
        if st != "not_installed":
            list_socks(show_links=True)
        print("")
        print(f"  {Colors.GREEN}1.{Colors.NC} ➕ Add SOCKS5 proxy (paste ip:port:user:pass)")
        print(f"  {Colors.GREEN}2.{Colors.NC} ➖ Remove SOCKS5 proxy")
        print(f"  {Colors.GREEN}3.{Colors.NC} ⏯️ Enable / Disable proxy")
        print(f"  {Colors.GREEN}4.{Colors.NC} 🧪 Test proxy")
        print(f"  {Colors.GREEN}5.{Colors.NC} ⚙️ Service management")
        print(f"  {Colors.GREEN}6.{Colors.NC} ♻️ Reset usage counters")
        print(f"  {Colors.GREEN}0.{Colors.NC} 🔙 Back")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        c = _ask("Select option: ")
        if c == '1':
            add_socks()
        elif c == '2':
            remove_socks()
        elif c == '3':
            toggle_socks()
        elif c == '4':
            test_socks()
        elif c == '5':
            service_menu()
        elif c == '6':
            reset_usage()
        elif c == '0':
            return
        else:
            print(f"{Colors.RED}❌ Invalid option{Colors.NC}")
            time.sleep(0.8)


if __name__ == "__main__":
    menu()
