#!/usr/bin/env python3
# mtproxy_stats.py - Statistics module for MTProxy connections

import os
import subprocess
import re
import time
import json
from datetime import datetime, timedelta

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

# Store ports for each proxy
PROXY_PORTS = {}

def load_proxy_ports():
    """Load proxy ports from config.py"""
    global PROXY_PORTS
    try:
        config_path = "/opt/mtprotoproxy/config.py"
        if not os.path.exists(config_path):
            return
        
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Find USERS dictionary
        users_match = re.search(r'USERS\s*=\s*\{([^}]*)\}', content, re.DOTALL)
        if not users_match:
            return
        
        users_str = users_match.group(1)
        
        # Parse each user
        # Pattern: "name": {"secret": "xxx", "port": 4443}
        pattern = r'"([^"]+)"\s*:\s*\{[^}]*"secret"\s*:\s*"([^"]+)"[^}]*"port"\s*:\s*(\d+)'
        matches = re.findall(pattern, users_str)
        
        for name, secret, port in matches:
            PROXY_PORTS[name] = port
            print(f"🔍 Loaded proxy: {name} -> port {port}")
        
        # If no custom ports found, use default port
        if not PROXY_PORTS:
            port_match = re.search(r'PORT\s*=\s*(\d+)', content)
            default_port = port_match.group(1) if port_match else "443"
            # Get user names from USERS
            user_pattern = r'"([^"]+)"\s*:\s*"([^"]+)"'
            user_matches = re.findall(user_pattern, users_str)
            for name, secret in user_matches:
                PROXY_PORTS[name] = default_port
        
    except Exception as e:
        print(f"Error loading proxy ports: {e}")

def get_proxy_port(proxy_name):
    """Get the port for a specific proxy"""
    if not PROXY_PORTS:
        load_proxy_ports()
    return PROXY_PORTS.get(proxy_name, "443")

def get_active_users_for_proxy(proxy_name):
    """
    Get number of active users for a specific proxy using its specific port
    """
    try:
        port = get_proxy_port(proxy_name)
        if not port:
            return 0
        
        # Get all established connections on this specific port
        result = subprocess.run(
            ['ss', '-tan', '|', 'grep', f':{port}', '|', 'grep', 'ESTAB'],
            shell=True,
            capture_output=True,
            text=True
        )
        
        lines = result.stdout.strip().split('\n')
        if not lines or not lines[0]:
            return 0
        
        # Count unique IPs (each IP = one user)
        unique_ips = set()
        for line in lines:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 5:
                remote = parts[4]
                if ':' in remote:
                    ip = remote.split(':')[0]
                    if ip and not ip.startswith('127.') and not ip.startswith('::1'):
                        unique_ips.add(ip)
        
        return len(unique_ips)
        
    except Exception as e:
        return 0

def get_total_historical_users(proxy_name):
    """
    Get total number of users that have ever connected to this proxy
    """
    try:
        stats_file = f"/etc/mtpulse/stats_{proxy_name}.json"
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                data = json.load(f)
                return data.get('total_users', 0)
    except:
        pass
    
    # Count from journalctl logs
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '--since', '7 days ago'],
            capture_output=True,
            text=True
        )
        logs = result.stdout
        
        # Look for connection patterns
        pattern = rf'User {re.escape(proxy_name)}.*connected from (\d+\.\d+\.\d+\.\d+)'
        matches = re.findall(pattern, logs)
        
        if matches:
            unique_ips = set(matches)
            return len(unique_ips)
        
        return 0
    except:
        return 0

def get_traffic_stats(proxy_name):
    """
    Get traffic statistics for a specific proxy
    """
    try:
        port = get_proxy_port(proxy_name)
        if not port:
            return {'total_bytes': 0, 'total_connections': 0}
        
        # Get PID of mtprotoproxy
        pid_result = subprocess.run(
            ['pgrep', '-f', 'mtprotoproxy.py'],
            capture_output=True,
            text=True
        )
        
        if not pid_result.stdout.strip():
            return {'total_bytes': 0, 'total_connections': 0}
        
        pid = pid_result.stdout.strip().split('\n')[0]
        
        # Get network stats for this PID
        try:
            with open(f'/proc/{pid}/net/dev', 'r') as f:
                net_stats = f.read()
            
            total_bytes = 0
            for line in net_stats.split('\n'):
                if 'eth0' in line or 'ens' in line:
                    parts = line.split()
                    if len(parts) >= 10:
                        rx_bytes = int(parts[1])
                        tx_bytes = int(parts[9])
                        total_bytes += rx_bytes + tx_bytes
                        break
            
            # If no traffic, try from logs
            if total_bytes == 0:
                result = subprocess.run(
                    ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '--since', '1 hour ago'],
                    capture_output=True,
                    text=True
                )
                logs = result.stdout
                
                # Look for traffic patterns
                pattern = rf'{re.escape(proxy_name)}.*(\d+\.?\d*)\s*(MB|GB|KB)'
                matches = re.findall(pattern, logs)
                total_mb = 0
                for match in matches:
                    value = float(match[0])
                    unit = match[1]
                    if unit == 'GB':
                        total_mb += value * 1024
                    elif unit == 'MB':
                        total_mb += value
                    elif unit == 'KB':
                        total_mb += value / 1024
                
                total_bytes = int(total_mb * 1024 * 1024)
            
            return {
                'total_bytes': total_bytes,
                'total_connections': 0
            }
        except:
            return {'total_bytes': 0, 'total_connections': 0}
            
    except Exception as e:
        return {'total_bytes': 0, 'total_connections': 0}

def format_bytes(bytes_value):
    """Format bytes to human readable format"""
    if bytes_value == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def get_connection_count(port):
    """Get number of active connections on a specific port"""
    try:
        result = subprocess.run(
            ['ss', '-tan', '|', 'grep', f':{port}'],
            shell=True,
            capture_output=True,
            text=True
        )
        
        lines = result.stdout.strip().split('\n')
        established = 0
        
        for line in lines:
            if not line.strip():
                continue
            if 'ESTAB' in line:
                established += 1
        
        return established
        
    except Exception as e:
        return 0

# Load proxy ports on module import
load_proxy_ports()
