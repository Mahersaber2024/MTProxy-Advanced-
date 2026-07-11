#!/usr/bin/env python3
# mtproxy_stats.py - Statistics module for MTProxy connections

import os
import subprocess
import re
import json
from datetime import datetime
import ipaddress

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

STATS_DIR = "/etc/mtpulse"
os.makedirs(STATS_DIR, exist_ok=True)

def get_stats_file(proxy_name):
    return f"{STATS_DIR}/stats_{proxy_name}.json"

def load_proxy_stats(proxy_name):
    stats_file = get_stats_file(proxy_name)
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r') as f:
                data = json.load(f)
                if 'unique_ips' in data:
                    data['unique_ips'] = set(data['unique_ips'])
                return data
        except:
            pass
    
    return {
        'total_bytes': 0,
        'total_connections': 0,
        'unique_ips': set(),
        'last_traffic_mb': 0.0,
        'last_update': None
    }

def save_proxy_stats(proxy_name, data):
    stats_file = get_stats_file(proxy_name)
    save_data = data.copy()
    if 'unique_ips' in save_data:
        save_data['unique_ips'] = list(save_data['unique_ips'])
    
    try:
        with open(stats_file, 'w') as f:
            json.dump(save_data, f, indent=2)
    except:
        pass

def get_active_users_for_proxy(proxy_name):
    """Online users - using ss (reliable)"""
    try:
        from mtproxy import load_proxies, get_default_port
        config = load_proxies()
        port = None
        for p in config.get('proxies', {}).values():
            if p.get('name') == proxy_name:
                port = p.get('port') or get_default_port()
                break
        if not port:
            port = get_default_port()
        return get_connection_count(port)
    except:
        return 0

def update_unique_users(proxy_name):
    """Update list of unique IPs that connected"""
    stats = load_proxy_stats(proxy_name)
    updated = False
    
    try:
        # Get current connections with IPs
        result = subprocess.run(
            f"ss -tan | grep ':{get_default_port()}' | grep ESTAB | awk '{{print $5}}' | cut -d: -f1",
            shell=True, capture_output=True, text=True
        )
        current_ips = result.stdout.strip().split('\n')
        
        for ip in current_ips:
            if ip and ip != "0.0.0.0" and not ip.startswith("127."):
                if ip not in stats['unique_ips']:
                    stats['unique_ips'].add(ip)
                    updated = True
    except:
        pass
    
    if updated:
        stats['total_users'] = len(stats['unique_ips'])
        save_proxy_stats(proxy_name, stats)

def get_total_historical_users(proxy_name):
    """Total unique users ever connected"""
    stats = load_proxy_stats(proxy_name)
    # Update users before returning
    update_unique_users(proxy_name)
    return stats.get('total_users', 0)

def get_traffic_stats(proxy_name):
    stats = load_proxy_stats(proxy_name)
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '--since', '24 hours ago'],
            capture_output=True, text=True
        )
        logs = result.stdout

        pattern = rf'{proxy_name}:\s*\d+\s*connects\s*\(\d+\s*current\),\s*([\d.]+)\s*([MG]B)'
        latest_mb = stats['last_traffic_mb']
        
        for match in re.finditer(pattern, logs):
            value = float(match.group(1))
            unit = match.group(2)
            current_mb = value * 1024 if unit == 'GB' else value
            if current_mb > latest_mb:
                delta_mb = current_mb - latest_mb
                stats['total_bytes'] += int(delta_mb * 1024 * 1024)
                latest_mb = current_mb

        stats['last_traffic_mb'] = latest_mb
        stats['last_update'] = datetime.now().isoformat()
        save_proxy_stats(proxy_name, stats)

        return {
            'total_sent': stats['total_bytes'] // 2,
            'total_received': stats['total_bytes'] // 2,
            'total_bytes': stats['total_bytes'],
            'total_connections': stats.get('total_connections', 0)
        }
    except:
        return {
            'total_sent': stats['total_bytes'] // 2,
            'total_received': stats['total_bytes'] // 2,
            'total_bytes': stats['total_bytes'],
            'total_connections': 0
        }

def format_bytes(bytes_value):
    if bytes_value == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def get_connection_count(port):
    try:
        result = subprocess.run(
            f"ss -tan | grep ':{port}' | grep ESTAB | wc -l",
            shell=True, capture_output=True, text=True
        )
        return int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
    except:
        return 0

def view_live_logs():
    try:
        print(f"{Colors.BOLD}{Colors.GREEN}📡 Live Log Viewer (Press Ctrl+C to exit){Colors.NC}")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        process = subprocess.Popen(
            ['journalctl', '-u', 'mtprotoproxy', '-f', '--no-pager', '-o', 'cat'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
        )
        try:
            for line in process.stdout:
                if 'connects' in line and 'current' in line:
                    parts = line.split(':', 1)
                    proxy_name = parts[0].strip()
                    stats = parts[1].strip()
                    print(f"{Colors.GREEN}[{proxy_name}]{Colors.NC} {stats}")
                elif 'New IPs' in line:
                    print(f"{Colors.YELLOW}🆕 {line}{Colors.NC}")
                elif 'Error' in line or 'error' in line:
                    print(f"{Colors.RED}❌ {line}{Colors.NC}")
                else:
                    print(line)
        except KeyboardInterrupt:
            process.terminate()
            print(f"\n{Colors.GREEN}✅ Log viewer stopped.{Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
