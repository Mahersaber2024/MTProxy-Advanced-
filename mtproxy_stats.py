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
<<<<<<< HEAD
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
=======
    View live logs with real-time updates and color highlighting
    Using tail -f on the actual log file for better performance
    """
    try:
        # Find the actual log file or use journalctl with better formatting
        print(f"{Colors.BOLD}{Colors.GREEN}📡 Live Log Viewer (Press Ctrl+C to exit){Colors.NC}")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        print(f"{Colors.YELLOW}ℹ️  Showing real-time logs with proxy statistics highlighted{Colors.NC}")
        print(f"{Colors.YELLOW}💡 Logs update every 10 minutes (MTProxy default){Colors.NC}")
        print("")
        
        # Clear screen and show initial logs
        os.system('clear' if os.name == 'posix' else 'cls')
        print(f"{Colors.BOLD}{Colors.GREEN}📡 Live Log Viewer (Press Ctrl+C to exit){Colors.NC}")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        # Run journalctl with follow and output as plain text
        process = subprocess.Popen(
            ['journalctl', '-u', 'mtprotoproxy', '-f', '--no-pager', '-o', 'cat'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        try:
            for line in process.stdout:
                if not line.strip():
                    continue
                    
                # Colorize based on content
                if 'connects' in line and 'current' in line:
                    # Stats line - highlight with green
                    parts = line.split(':')
                    if len(parts) >= 2:
                        proxy_name = parts[0].strip()
                        stats = ':'.join(parts[1:]).strip()
                        # Check if there are active users
                        if '0 current' in line:
                            print(f"{Colors.YELLOW}[{proxy_name}]{Colors.NC} {stats}")
                        else:
                            print(f"{Colors.GREEN}[{proxy_name}]{Colors.NC} {stats}")
                    else:
                        print(f"{Colors.CYAN}{line}{Colors.NC}")
                elif 'New IPs' in line:
                    print(f"{Colors.MAGENTA}🆕 {line}{Colors.NC}")
                elif 'Error' in line or 'error' in line:
                    print(f"{Colors.RED}❌ {line}{Colors.NC}")
                elif 'connected' in line.lower():
                    print(f"{Colors.BLUE}🔗 {line}{Colors.NC}")
                elif 'disconnected' in line.lower():
                    print(f"{Colors.RED}🔴 {line}{Colors.NC}")
                else:
                    # Check if it's an IP address
                    ip_match = re.search(r'\b(\d+\.\d+\.\d+\.\d+)\b', line)
                    if ip_match:
                        print(f"{Colors.WHITE}📍 {line}{Colors.NC}")
                    else:
                        print(line)
                        
        except KeyboardInterrupt:
            process.terminate()
            print(f"\n{Colors.GREEN}✅ Log viewer stopped.{Colors.NC}")
            
    except Exception as e:
        print(f"{Colors.RED}❌ Error viewing logs: {e}{Colors.NC}")
    
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")

def get_total_bandwidth():
    """
    Get total available bandwidth of the server
    """
    try:
        # Try to get bandwidth from system
        result = subprocess.run(
            ['speedtest-cli', '--simple'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'Download' in line:
                    speed = re.search(r'([\d.]+)\s*Mbit/s', line)
                    if speed:
                        return float(speed.group(1))
        
        # Fallback: use vnstat or iftop
        result = subprocess.run(
            ['vnstat', '--oneline'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Parse vnstat output
            parts = result.stdout.split(';')
            if len(parts) >= 5:
                # Average download speed in Mbit/s
                speed = parts[4].strip()
                if 'Mbit' in speed:
                    return float(speed.replace('Mbit/s', '').strip())
        
        return 100  # Default fallback: 100 Mbit/s
        
    except Exception as e:
        return 100  # Default fallback

def get_per_user_bandwidth(proxy_name):
    """
    Calculate bandwidth per user for a specific proxy
    """
    try:
        # Get active users
        active_users = get_active_users_for_proxy(proxy_name)
        
        if active_users == 0:
            return {
                'total_bandwidth': 0,
                'per_user': 0,
                'active_users': 0,
                'status': 'No active users'
            }
        
        # Get total bandwidth (default 100 Mbit/s if can't detect)
        total_bandwidth = get_total_bandwidth()
        
        # Calculate per user (divide total bandwidth by active users)
        per_user = total_bandwidth / active_users
        
        # Get traffic stats to show actual usage
        traffic = get_traffic_stats(proxy_name)
        
        return {
            'total_bandwidth': total_bandwidth,
            'per_user': per_user,
            'active_users': active_users,
            'status': 'Active',
            'traffic_mb': traffic.get('total_bytes', 0) / (1024 * 1024)
        }
        
    except Exception as e:
        return {
            'total_bandwidth': 0,
            'per_user': 0,
            'active_users': 0,
            'status': 'Error'
        }

def check_connection_quality(proxy_name):
    """
    Check connection quality and suggest if proxy is overloaded
    """
    stats = get_per_user_bandwidth(proxy_name)
    
    if stats['active_users'] == 0:
        return "🟢 Idle (No users)"
    
    per_user = stats['per_user']
    
    if per_user >= 10:
        return f"🟢 Excellent ({per_user:.1f} Mbit/s per user)"
    elif per_user >= 5:
        return f"🟡 Good ({per_user:.1f} Mbit/s per user)"
    elif per_user >= 2:
        return f"🟠 Fair ({per_user:.1f} Mbit/s per user)"
    elif per_user >= 1:
        return f"🔴 Slow ({per_user:.1f} Mbit/s per user)"
    else:
        return f"🔴 Very Slow ({per_user:.1f} Mbit/s per user)"
>>>>>>> v2-stats
