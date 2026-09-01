#!/usr/bin/env python3
# mtproxy_stats.py - Statistics module for MTProxy (v2 - accurate usage accounting)
#
# What was broken in v1 and is fixed here:
#  1) Traffic regex only accepted "MB"/"GB". mtprotoproxy also prints B/KB/TB
#     (and "0.00 MB" for small traffic) -> usage always showed "0 B".
#  2) v1 SUMMED every periodic stats snapshot. Those snapshots are CUMULATIVE
#     totals, not deltas, so summing 24h of logs gave nonsense numbers.
#     Now we take the latest snapshot per proxy.
#  3) Every add/remove/tag restarts the service, which resets mtprotoproxy's
#     in-memory counters to zero. v1 had no persistence -> usage back to 0.
#     Now counters are persisted in /etc/mtpulse/usage.json and resets are
#     detected (counter went backwards) and carried over as a baseline.
#  4) "Online" read only the last 10 minutes while mtprotoproxy's default
#     STATS_PRINT_PERIOD is 600s, so the window was frequently empty.
#     ensure_stats_config() forces STATS_PRINT_PERIOD = 60.
#  5) Proxy names were interpolated into regexes unescaped, and the journal was
#     re-read 3x per proxy per refresh. Now: one cached pass, names escaped.
#  6) get_connection_count() passed a list to shell=True (only the first item
#     ran). Fixed.

import os
import re
import json
import time
import shlex
import subprocess

CONFIG_DIR = "/etc/mtpulse"
USAGE_DB = f"{CONFIG_DIR}/usage.json"
SERVICE_NAME = "mtprotoproxy"
PROXY_DIR = "/opt/mtprotoproxy"
CACHE_TTL = 5          # seconds - avoid hammering journalctl on every redraw
DEFAULT_PERIOD = 60    # stats print period we enforce in config.py


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


# "Proxy-1: 17 connects (3 current), 0.66 MB, 723 msgs"
STAT_RE = re.compile(
    r'^(?P<user>[^:]{1,64}):\s+(?P<connects>\d+)\s+connects\s+'
    r'\((?P<current>\d+)\s+current\)\s*,\s*'
    r'(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[KMGT]?i?B)?\s*,\s*'
    r'(?P<msgs>\d+)\s+msgs',
    re.IGNORECASE)

UNITS = {
    'b': 1,
    'kb': 1024, 'kib': 1024,
    'mb': 1024 ** 2, 'mib': 1024 ** 2,
    'gb': 1024 ** 3, 'gib': 1024 ** 3,
    'tb': 1024 ** 4, 'tib': 1024 ** 4,
}

_cache = {"ts": 0.0, "data": {}}


# ---------------------------------------------------------------- persistence
def _load_db():
    try:
        with open(USAGE_DB, 'r') as f:
            db = json.load(f)
        if isinstance(db, dict) and isinstance(db.get('users'), dict):
            return db
    except Exception:
        pass
    return {"since": 0.0, "users": {}}


def _save_db(db):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        tmp = USAGE_DB + ".tmp"
        with open(tmp, 'w') as f:
            json.dump(db, f, indent=2)
        os.replace(tmp, USAGE_DB)
    except Exception:
        pass


def _blank_user():
    return {
        "base_octets": 0, "last_octets": 0,
        "base_connects": 0, "last_connects": 0,
        "base_msgs": 0, "last_msgs": 0,
        "online": 0, "peak": 0, "last_seen": 0.0,
    }


# ------------------------------------------------------------- journal parser
def _stats_period():
    """Read STATS_PRINT_PERIOD from mtprotoproxy config.py (default 60)."""
    try:
        with open(f"{PROXY_DIR}/config.py", 'r') as f:
            m = re.search(r'STATS_PRINT_PERIOD\s*=\s*(\d+)', f.read())
            if m:
                return max(10, int(m.group(1)))
    except Exception:
        pass
    return DEFAULT_PERIOD


def _read_journal(since_epoch):
    """Return list of (epoch, message) tuples for the proxy service."""
    if since_epoch and since_epoch > 0:
        since = f"@{int(since_epoch)}"
    else:
        since = "7 days ago"
    try:
        res = subprocess.run(
            ['journalctl', '-u', SERVICE_NAME, '--no-pager',
             '-o', 'short-unix', '--since', since],
            capture_output=True, text=True, timeout=20)
        raw = res.stdout
    except Exception:
        return []

    out = []
    for line in raw.splitlines():
        if not line or line.startswith('--'):
            continue
        head, _, rest = line.partition(' ')
        try:
            ts = float(head)
        except ValueError:
            continue
        # strip "host process[pid]: " prefix
        idx = rest.find(']: ')
        if idx != -1:
            msg = rest[idx + 3:]
        else:
            _, _, msg = rest.partition(': ')
        out.append((ts, msg.strip()))
    return out


def get_all_stats(force=False):
    """
    Parse new journal entries, fold them into the persistent usage DB and
    return {proxy_name: stats}. Cumulative counters survive service restarts.
    """
    now = time.time()
    if not force and (now - _cache["ts"]) < CACHE_TTL and _cache["data"]:
        return _cache["data"]

    db = _load_db()
    users = db["users"]
    entries = _read_journal(db.get("since", 0))
    newest = db.get("since", 0.0)

    for ts, msg in entries:
        m = STAT_RE.match(msg)
        if not m:
            continue
        name = m.group('user').strip()
        if not name or name.lower().startswith('stats for'):
            continue

        unit = (m.group('unit') or 'MB').lower().replace('ytes', '')
        octets = int(float(m.group('value')) * UNITS.get(unit, UNITS['mb']))
        connects = int(m.group('connects'))
        current = int(m.group('current'))
        msgs = int(m.group('msgs'))

        u = users.setdefault(name, _blank_user())

        # Service restarted -> counters went back to (near) zero.
        # Carry the last known totals over into the baseline.
        if octets < u["last_octets"] or connects < u["last_connects"]:
            u["base_octets"] += u["last_octets"]
            u["base_connects"] += u["last_connects"]
            u["base_msgs"] += u["last_msgs"]

        u["last_octets"] = octets
        u["last_connects"] = connects
        u["last_msgs"] = msgs
        u["online"] = current
        u["peak"] = max(u.get("peak", 0), current)
        u["last_seen"] = ts
        newest = max(newest, ts)

    db["since"] = newest
    db["users"] = users
    _save_db(db)

    period = _stats_period()
    stale_after = period * 3 + 60

    data = {}
    for name, u in users.items():
        fresh = (now - u.get("last_seen", 0)) <= stale_after
        data[name] = {
            "online": u.get("online", 0) if fresh else 0,
            "peak": u.get("peak", 0),
            "total_connects": u.get("base_connects", 0) + u.get("last_connects", 0),
            "total_msgs": u.get("base_msgs", 0) + u.get("last_msgs", 0),
            "total_bytes": u.get("base_octets", 0) + u.get("last_octets", 0),
            "last_seen": u.get("last_seen", 0),
            "fresh": fresh,
        }
    _cache["ts"] = now
    _cache["data"] = data
    return data


def flush_stats():
    """Persist current counters. Call this BEFORE restarting the service."""
    get_all_stats(force=True)


def reset_usage(proxy_name=None):
    """Reset stored usage for one proxy, or all of them."""
    db = _load_db()
    if proxy_name:
        db["users"].pop(proxy_name, None)
    else:
        db["users"] = {}
    _save_db(db)
    _cache["ts"] = 0.0
    _cache["data"] = {}


def ensure_stats_config(proxy_dir=PROXY_DIR):
    """
    Force STATS_PRINT_PERIOD = 60 in mtprotoproxy config.py so stats show up
    every minute instead of every 10 minutes. Returns True if file changed.
    """
    path = f"{proxy_dir}/config.py"
    if not os.path.exists(path):
        return False
    try:
        with open(path, 'r') as f:
            content = f.read()
        if re.search(r'^\s*STATS_PRINT_PERIOD', content, re.M):
            new = re.sub(r'^\s*STATS_PRINT_PERIOD\s*=\s*\d+\s*$',
                         f'STATS_PRINT_PERIOD = {DEFAULT_PERIOD}',
                         content, flags=re.M)
        else:
            new = content.rstrip('\n') + f'\nSTATS_PRINT_PERIOD = {DEFAULT_PERIOD}\n'
        if new != content:
            with open(path, 'w') as f:
                f.write(new)
            return True
    except Exception:
        pass
    return False


# ------------------------------------------------------- backwards-compatible
def get_active_users_for_proxy(proxy_name):
    return get_all_stats().get(proxy_name, {}).get('online', 0)


def get_total_historical_users(proxy_name):
    return get_all_stats().get(proxy_name, {}).get('total_connects', 0)


def get_traffic_stats(proxy_name):
    s = get_all_stats().get(proxy_name)
    if not s:
        return {'total_sent': 0, 'total_received': 0, 'total_bytes': 0,
                'total_connections': 0, 'online': 0, 'peak': 0, 'fresh': False}
    total = s['total_bytes']
    return {
        'total_sent': total // 2,
        'total_received': total - total // 2,
        'total_bytes': total,
        'total_connections': s['total_connects'],
        'online': s['online'],
        'peak': s['peak'],
        'fresh': s['fresh'],
    }


def format_bytes(bytes_value):
    try:
        bytes_value = float(bytes_value)
    except (TypeError, ValueError):
        return "0 B"
    if bytes_value <= 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.0f} {unit}" if unit == 'B' else f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def get_connection_count(port):
    """Established TCP connections on a port (fixed: proper shell command)."""
    try:
        res = subprocess.run(
            f"ss -tan state established | grep -c ':{shlex.quote(str(port))} '",
            shell=True, capture_output=True, text=True, timeout=10)
        return int(res.stdout.strip() or 0)
    except Exception:
        return 0


def view_live_logs():
    try:
        print(f"{Colors.BOLD}{Colors.GREEN}📡 Live Log Viewer (Press Ctrl+C to exit){Colors.NC}")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        print(f"{Colors.YELLOW}ℹ️  Real-time logs, proxy statistics highlighted{Colors.NC}")
        print("")
        process = subprocess.Popen(
            ['journalctl', '-u', SERVICE_NAME, '-f', '--no-pager', '-o', 'cat'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, bufsize=1)
        try:
            for line in process.stdout:
                line = line.rstrip('\n')
                m = STAT_RE.match(line.strip())
                if m:
                    print(f"{Colors.GREEN}[{m.group('user')}]{Colors.NC} "
                          f"{Colors.WHITE}{m.group('connects')} connects "
                          f"({m.group('current')} now){Colors.NC} | "
                          f"{Colors.CYAN}{m.group('value')} {m.group('unit') or 'MB'}{Colors.NC} | "
                          f"{m.group('msgs')} msgs")
                elif 'Stats for' in line:
                    print(f"{Colors.PURPLE}{line}{Colors.NC}")
                elif 'New IPs' in line:
                    print(f"{Colors.YELLOW}🆕 {line}{Colors.NC}")
                elif 'rror' in line:
                    print(f"{Colors.RED}❌ {line}{Colors.NC}")
                else:
                    print(line)
        except KeyboardInterrupt:
            process.terminate()
            print(f"\n{Colors.GREEN}✅ Log viewer stopped.{Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}❌ Error viewing logs: {e}{Colors.NC}")
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")


if __name__ == "__main__":
    for n, s in get_all_stats(force=True).items():
        print(f"{n}: online={s['online']} peak={s['peak']} "
              f"connects={s['total_connects']} usage={format_bytes(s['total_bytes'])}")
