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
        
        # Pattern for stats line: "Proxy-1: 17 connects (3 current), 0.66 MB, 723 msgs"
        pattern = rf'{proxy_name}:\s*(\d+)\s*connects\s*\((\d+)\s*current\)'
        
        # Find all matches
        matches = re.findall(pattern, logs)
        
        if matches:
            # Get the last match (most recent stats)
            total_connects, current_users = matches[-1]
            return int(current_users)
        
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
        pattern = rf'{proxy_name}:\s*(\d+)\s*connects'
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
        
        # Pattern for stats line
        pattern = rf'{proxy_name}:\s*\d+\s*connects\s*\(\d+\s*current\),\s*([\d.]+)\s*([MG]B)'
        
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
        connect_pattern = rf'{proxy_name}:\s*(\d+)\s*connects'
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

def view_live_logs():
    """
    View live logs with color highlighting using tail -f
    """
    try:
        print(f"{Colors.BOLD}{Colors.GREEN}📡 Live Log Viewer (Press Ctrl+C to exit){Colors.NC}")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        print(f"{Colors.YELLOW}ℹ️  Showing real-time logs with proxy statistics highlighted{Colors.NC}")
        print(f"{Colors.YELLOW}💡 Press Ctrl+C to stop viewing{Colors.NC}")
        print("")
        
        # Use tail -f on the journalctl output
        # First, get the last 50 lines, then follow
        cmd = "journalctl -u mtprotoproxy --no-pager -n 50 -o cat && journalctl -u mtprotoproxy -f --no-pager -o cat"
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Set stdout to non-blocking
        import fcntl
        import os
        fd = process.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        
        try:
            while True:
                try:
                    line = process.stdout.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    
                    # Colorize based on content
                    if 'connects' in line and 'current' in line:
                        # Stats line - highlight proxy name
                        parts = line.split(':')
                        if len(parts) >= 2:
                            proxy_name = parts[0].strip()
                            stats = ':'.join(parts[1:]).strip()
                            print(f"{Colors.GREEN}[{proxy_name}]{Colors.NC}{stats}")
                        else:
                            print(f"{Colors.CYAN}{line.strip()}{Colors.NC}")
                    elif 'New IPs' in line:
                        print(f"{Colors.YELLOW}🆕 {line.strip()}{Colors.NC}")
                    elif 'Error' in line or 'error' in line or 'ERROR' in line:
                        print(f"{Colors.RED}❌ {line.strip()}{Colors.NC}")
                    elif 'WARNING' in line or 'Warning' in line:
                        print(f"{Colors.YELLOW}⚠️ {line.strip()}{Colors.NC}")
                    else:
                        print(line.strip())
                        
                except IOError:
                    # No data available yet
                    time.sleep(0.1)
                    continue
                    
        except KeyboardInterrupt:
            process.terminate()
            print(f"\n{Colors.GREEN}✅ Log viewer stopped.{Colors.NC}")
            
    except Exception as e:
        print(f"{Colors.RED}❌ Error viewing logs: {e}{Colors.NC}")
        import traceback
        traceback.print_exc()
    
    input(f"{Colors.BOLD}{Colors.PURPLE}Press Enter to return...{Colors.NC}")
