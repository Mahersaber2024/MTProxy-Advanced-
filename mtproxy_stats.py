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

def get_active_users_for_proxy(proxy_name):
    """
    Get number of active users for a specific proxy from logs
    Using the format: "Proxy-1: 17 connects (3 current), 0.66 MB, 723 msgs"
    """
    try:
        # Get logs from last 10 minutes
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '--since', '10 minutes ago'],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout
        
        # Improved pattern for stats line
        # Example: "Proxy-1: 17 connects (3 current), 0.66 MB, 723 msgs"
        # This pattern extracts the number inside parentheses
        pattern = rf'{re.escape(proxy_name)}:\s*\d+\s*connects\s*\((\d+)\s*current\)'
        
        matches = re.findall(pattern, logs)
        
        if matches:
            # Get the last match (most recent stats)
            current_users = int(matches[-1])
            return current_users
        
        # Alternative: Try a more flexible pattern
        pattern2 = rf'{re.escape(proxy_name)}:[^)]*\((\d+)\s*current\)'
        matches2 = re.findall(pattern2, logs)
        
        if matches2:
            return int(matches2[-1])
        
        return 0
        
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
        
        # Find the latest stats for this proxy
        pattern = rf'{re.escape(proxy_name)}:\s*(\d+)\s*connects'
        matches = re.findall(pattern, logs)
        
        if matches:
            # Return the latest total connects
            return int(matches[-1])
        
        return 0
    except:
        return 0

def get_traffic_stats(proxy_name):
    """
    Get traffic statistics for a specific proxy
    From format: "Proxy-1: 17 connects (3 current), 0.66 MB, 723 msgs"
    """
    try:
        # Get traffic logs from last 24 hours
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '--since', '24 hours ago'],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout
        
        # Pattern for stats line - extract traffic
        pattern = rf'{re.escape(proxy_name)}:\s*\d+\s*connects\s*\(\d+\s*current\),\s*([\d.]+)\s*([MG]B)'
        
        total_mb = 0.0
        for match in re.finditer(pattern, logs):
            value = float(match.group(1))
            unit = match.group(2)
            if unit == 'GB':
                total_mb += value * 1024
            else:  # MB
                total_mb += value
        
        # Convert MB to bytes
        total_bytes = int(total_mb * 1024 * 1024)
        
        # Count total connections
        connect_pattern = rf'{re.escape(proxy_name)}:\s*(\d+)\s*connects'
        connect_matches = re.findall(connect_pattern, logs)
        total_connections = int(connect_matches[-1]) if connect_matches else 0
        
        return {
            'total_sent': total_bytes // 2,  # Approximate
            'total_received': total_bytes // 2,  # Approximate
            'total_bytes': total_bytes,
            'total_connections': total_connections
        }
    except Exception as e:
        return {'total_sent': 0, 'total_received': 0, 'total_bytes': 0, 'total_connections': 0}

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
