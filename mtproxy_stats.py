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

# Cache for connection data
_connection_cache = {}
_cache_time = 0

def get_active_users_for_proxy(proxy_name):
    """
    Get number of active users for a specific proxy from logs
    """
    try:
        # Get logs from last 10 minutes
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '--since', '10 minutes ago'],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout
        
        # Pattern for connection: "User Proxy-1 connected from 5.121.66.180"
        connect_pattern = rf'User {re.escape(proxy_name)} connected from (\d+\.\d+\.\d+\.\d+)'
        disconnect_pattern = rf'User {re.escape(proxy_name)} disconnected'
        
        # Find all connections and disconnections
        connected_ips = set()
        disconnected_ips = set()
        
        for line in logs.split('\n'):
            # Check for connection
            connect_match = re.search(connect_pattern, line)
            if connect_match:
                ip = connect_match.group(1)
                connected_ips.add(ip)
                # If IP was previously disconnected, remove from disconnected
                if ip in disconnected_ips:
                    disconnected_ips.remove(ip)
                continue
            
            # Check for disconnection
            if re.search(disconnect_pattern, line):
                # Try to extract IP from disconnect message
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    ip = ip_match.group(1)
                    disconnected_ips.add(ip)
        
        # Active users = connected_ips - disconnected_ips
        active_ips = connected_ips - disconnected_ips
        
        # If no connection logs found, try alternative pattern
        if len(connected_ips) == 0:
            # Try to find stats in logs: "Proxy-1: 17 connects (3 current)"
            stats_pattern = rf'{re.escape(proxy_name)}:\s*\d+\s*connects\s*\((\d+)\s*current\)'
            matches = re.findall(stats_pattern, logs)
            if matches:
                return int(matches[-1])
        
        return len(active_ips)
        
    except Exception as e:
        return 0

def get_total_historical_users(proxy_name):
    """
    Get total number of users that have ever connected to this proxy
    """
    try:
        # Check if we have a stats file
        stats_file = f"/etc/mtpulse/stats_{proxy_name}.json"
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                data = json.load(f)
                return data.get('total_users', 0)
    except:
        pass
    
    # Fallback: count from logs
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager'],
            capture_output=True,
            text=True
        )
        logs = result.stdout
        
        # Count unique connections for this proxy
        pattern = rf'User {re.escape(proxy_name)} connected from (\d+\.\d+\.\d+\.\d+)'
        matches = re.findall(pattern, logs)
        
        if matches:
            unique_ips = set(matches)
            return len(unique_ips)
        
        # Alternative: count from stats lines
        stats_pattern = rf'{re.escape(proxy_name)}:\s*(\d+)\s*connects'
        matches = re.findall(stats_pattern, logs)
        if matches:
            return int(matches[-1])
        
        return 0
    except:
        return 0

def get_traffic_stats(proxy_name):
    """
    Get traffic statistics for a specific proxy from logs
    """
    try:
        # Get logs from last 24 hours
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '--since', '24 hours ago'],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout
        
        total_bytes = 0
        
        # Look for traffic in stats lines: "Proxy-1: 17 connects (3 current), 0.66 MB, 723 msgs"
        pattern = rf'{re.escape(proxy_name)}:\s*\d+\s*connects\s*\(\d+\s*current\),\s*([\d.]+)\s*([MG]B)'
        matches = re.findall(pattern, logs)
        
        total_mb = 0.0
        for match in matches:
            value = float(match[0])
            unit = match[1]
            if unit == 'GB':
                total_mb += value * 1024
            else:  # MB
                total_mb += value
        
        total_bytes = int(total_mb * 1024 * 1024)
        
        # If no stats found, try to estimate from connection logs
        if total_bytes == 0:
            # Count connections and estimate 1MB per connection
            conn_pattern = rf'User {re.escape(proxy_name)} connected'
            conn_count = len(re.findall(conn_pattern, logs))
            total_bytes = conn_count * 1024 * 1024  # 1MB per connection (rough estimate)
        
        return {
            'total_bytes': total_bytes,
            'total_connections': 0
        }
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
    """
    Get number of active connections on a specific port
    """
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
