#!/usr/bin/env python3
# mtproxy_stats.py - Statistics module for MTProxy connections (Improved Version)

import os
import subprocess
import re
import json
from datetime import datetime

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
    """Load persistent stats for a proxy"""
    stats_file = get_stats_file(proxy_name)
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'total_bytes': 0,
        'total_connections': 0,
        'total_users': 0,
        'last_traffic_mb': 0.0,
        'last_update': None
    }

def save_proxy_stats(proxy_name, data):
    """Save stats persistently"""
    stats_file = get_stats_file(proxy_name)
    try:
        with open(stats_file, 'w') as f:
            json.dump(data, f, indent=2)
    except:
        pass

def get_active_users_for_proxy(proxy_name):
    """Get currently online users"""
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '--since', '10 minutes ago'],
            capture_output=True, text=True
        )
        logs = result.stdout
        pattern = rf'{proxy_name}:\s*(\d+)\s*connects\s*\((\d+)\s*current\)'
        matches = re.findall(pattern, logs)
        return int(matches[-1][1]) if matches else 0
    except:
        return 0

def get_total_historical_users(proxy_name):
    """Get total unique users ever connected"""
    stats = load_proxy_stats(proxy_name)
    return stats.get('total_users', 0)

def get_traffic_stats(proxy_name):
    """
    Get accurate cumulative traffic ONLY for this MTProxy instance
    """
    stats = load_proxy_stats(proxy_name)
    
    try:
        # Get recent logs (last 24h is enough to catch new reports)
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '--since', '24 hours ago'],
            capture_output=True, text=True
        )
        logs = result.stdout

        # Pattern to extract traffic: "ProxyName: X connects (Y current), Z.ZZ GB, ..."
        pattern = rf'{proxy_name}:\s*\d+\s*connects\s*\(\d+\s*current\),\s*([\d.]+)\s*([MG]B)'
        
        latest_mb = stats['last_traffic_mb']
        
        for match in re.finditer(pattern, logs):
            value = float(match.group(1))
            unit = match.group(2)
            current_mb = value * 1024 if unit == 'GB' else value
            
            # Only add the difference (delta) to avoid double counting
            if current_mb > latest_mb:
                delta_mb = current_mb - latest_mb
                stats['total_bytes'] += int(delta_mb * 1024 * 1024)
                latest_mb = current_mb

        # Update last known traffic
        stats['last_traffic_mb'] = latest_mb
        stats['last_update'] = datetime.now().isoformat()

        # Update total connections
        connect_pattern = rf'{proxy_name}:\s*(\d+)\s*connects'
        connect_matches = re.findall(connect_pattern, logs)
        if connect_matches:
            stats['total_connections'] = int(connect_matches[-1])

        save_proxy_stats(proxy_name, stats)

        return {
            'total_sent': stats['total_bytes'] // 2,      # Approximate upload
            'total_received': stats['total_bytes'] // 2,  # Approximate download
            'total_bytes': stats['total_bytes'],
            'total_connections': stats['total_connections']
        }

    except Exception:
        # Return cached stats if log reading fails
        return {
            'total_sent': stats['total_bytes'] // 2,
            'total_received': stats['total_bytes'] // 2,
            'total_bytes': stats['total_bytes'],
            'total_connections': stats.get('total_connections', 0)
        }

def format_bytes(bytes_value):
    """Format bytes to human readable"""
    if bytes_value == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

# Keep other functions unchanged
def get_connection_count(port):
    try:
        result = subprocess.run(
            ['ss', '-tan', '|', 'grep', f':{port}'],
            shell=True, capture_output=True, text=True
        )
        lines = result.stdout.strip().split('\n')
        return sum(1 for line in lines if line.strip() and 'ESTAB' in line)
    except:
        return 0

def view_live_logs():
    # (unchanged - you can keep your original version)
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
