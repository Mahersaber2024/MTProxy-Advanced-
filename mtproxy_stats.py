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

def get_active_users_from_logs(proxy_name):
    """
    Get active users for a specific proxy from logs
    Counts users who have connected but not disconnected in the last 10 minutes
    """
    try:
        # Get logs from last 10 minutes
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '--since', '10 minutes ago'],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout
        
        # Pattern for connection: "User <proxy_name> connected from <ip>"
        connect_pattern = rf'User {proxy_name} .*connected from (\d+\.\d+\.\d+\.\d+)'
        disconnect_pattern = rf'User {proxy_name} .*disconnected'
        
        # Find all connections and disconnections
        connected_ips = set()
        disconnected_ips = set()
        
        # Process logs line by line to maintain order
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
                else:
                    # If IP not in disconnect message, we need to find which IP disconnected
                    # This is a limitation, but we can handle it by counting connections
                    pass
        
        # Active users = connected_ips - disconnected_ips
        active_ips = connected_ips - disconnected_ips
        
        # Alternative method: count unique users who connected in last 5 minutes
        # and haven't disconnected
        try:
            # Get more detailed logs
            detail_result = subprocess.run(
                ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '--since', '5 minutes ago'],
                capture_output=True,
                text=True
            )
            detail_logs = detail_result.stdout
            
            # Count all connection events
            all_connects = re.findall(rf'User {proxy_name} .*connected', detail_logs)
            all_disconnects = re.findall(rf'User {proxy_name} .*disconnected', detail_logs)
            
            # Estimate active users
            active_estimate = max(0, len(all_connects) - len(all_disconnects))
            
            # If we have at least one connection, use the estimate
            if len(all_connects) > 0:
                # Use the larger of the two methods
                return max(len(active_ips), active_estimate)
        except:
            pass
        
        return len(active_ips)
        
    except Exception as e:
        return 0

def get_connection_count_by_port(port):
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
        pattern = rf'User {proxy_name} .*connected from'
        connections = re.findall(pattern, result.stdout, re.IGNORECASE)
        
        # Try to extract unique IPs
        unique_ips = set()
        for conn in connections:
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', conn)
            if ip_match:
                unique_ips.add(ip_match.group(1))
        
        return len(unique_ips) if unique_ips else len(connections)
    except:
        return 0

def update_stats_file(proxy_name, stats):
    """
    Save statistics to a file for persistence
    """
    stats_file = f"/etc/mtpulse/stats_{proxy_name}.json"
    try:
        os.makedirs('/etc/mtpulse', exist_ok=True)
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
    except:
        pass

def get_traffic_stats(proxy_name):
    """
    Get traffic statistics for a specific proxy
    Returns: (total_bytes, total_connections)
    """
    try:
        # Get traffic logs
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '--since', '24 hours ago'],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout
        
        # Look for traffic lines like: "User NL3_1 sent 1024 bytes, received 2048 bytes"
        traffic_pattern = rf'User {proxy_name} .*sent (\d+) bytes, received (\d+) bytes'
        total_sent = 0
        total_received = 0
        
        for match in re.finditer(traffic_pattern, logs, re.IGNORECASE):
            sent = int(match.group(1))
            received = int(match.group(2))
            total_sent += sent
            total_received += received
        
        # Also count total connections
        connect_pattern = rf'User {proxy_name} .*connected'
        total_connections = len(re.findall(connect_pattern, logs, re.IGNORECASE))
        
        return {
            'total_sent': total_sent,
            'total_received': total_received,
            'total_bytes': total_sent + total_received,
            'total_connections': total_connections
        }
    except Exception as e:
        return {'total_sent': 0, 'total_received': 0, 'total_bytes': 0, 'total_connections': 0}

def format_bytes(bytes):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"
