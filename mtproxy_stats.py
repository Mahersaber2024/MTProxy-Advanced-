#!/usr/bin/env python3
import os
import subprocess
import re
import json
from datetime import datetime

class Colors:
    RED = '\033[0;31m'; GREEN = '\033[0;32m'; YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'; PURPLE = '\033[0;35m'; CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'; NC = '\033[0m'; BOLD = '\033[1m'

def get_active_users_for_proxy(proxy_name):
    """Get active users for a specific proxy from logs"""
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '--since', '10 minutes ago'],
            capture_output=True, text=True
        )
        logs = result.stdout
        pattern = rf'{proxy_name}:\s*\d+\s*connects\s*\((\d+)\s*current\)'
        matches = re.findall(pattern, logs)
        if matches:
            return int(matches[-1])
        return 0
    except:
        return 0

def get_total_historical_users(proxy_name):
    """Get total users that ever connected"""
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager'],
            capture_output=True, text=True
        )
        logs = result.stdout
        pattern = rf'{proxy_name}:\s*(\d+)\s*connects'
        matches = re.findall(pattern, logs)
        return int(matches[-1]) if matches else 0
    except:
        return 0

def get_traffic_stats(proxy_name):
    """Get traffic stats from logs"""
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '--since', '24 hours ago'],
            capture_output=True, text=True
        )
        logs = result.stdout
        pattern = rf'{proxy_name}:\s*\d+\s*connects\s*\(\d+\s*current\),\s*([\d.]+)\s*([MG]B)'
        total_mb = 0.0
        for match in re.finditer(pattern, logs):
            value = float(match.group(1))
            unit = match.group(2)
            total_mb += value * 1024 if unit == 'GB' else value
        total_bytes = int(total_mb * 1024 * 1024)
        return {'total_bytes': total_bytes}
    except:
        return {'total_bytes': 0}

def format_bytes(bytes_value):
    if bytes_value == 0: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def get_active_users_count():
    """Get total active users across all proxies"""
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '--since', '10 minutes ago'],
            capture_output=True, text=True
        )
        logs = result.stdout
        total = 0
        pattern = r'(\w+):\s*\d+\s*connects\s*\((\d+)\s*current\)'
        for match in re.findall(pattern, logs):
            total += int(match[1])
        return total
    except:
        return 0

def get_total_bandwidth():
    """Get total bandwidth - simplified"""
    # Default 100 Mbps if can't detect
    try:
        result = subprocess.run(['speedtest-cli', '--simple'], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'Download' in line:
                    match = re.search(r'([\d.]+)\s*Mbit/s', line)
                    if match:
                        return float(match.group(1))
    except:
        pass
    return 100.0

def view_live_logs():
    """Simple live log viewer"""
    try:
        print(f"{Colors.BOLD}{Colors.GREEN}📡 Live Log Viewer (Press Ctrl+C to exit){Colors.NC}")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        process = subprocess.Popen(
            ['journalctl', '-u', 'mtprotoproxy', '-f', '--no-pager', '-o', 'cat'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1
        )
        try:
            for line in process.stdout:
                if 'connects' in line and 'current' in line:
                    print(f"{Colors.GREEN}{line}{Colors.NC}")
                elif 'New IPs' in line:
                    print(f"{Colors.MAGENTA}🆕 {line}{Colors.NC}")
                elif 'Error' in line:
                    print(f"{Colors.RED}❌ {line}{Colors.NC}")
                else:
                    print(line)
        except KeyboardInterrupt:
            process.terminate()
            print(f"\n{Colors.GREEN}✅ Log viewer stopped.{Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
    input(f"Press Enter to return...")
