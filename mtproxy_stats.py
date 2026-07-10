#!/usr/bin/env python3
# mtproxy_stats.py - Statistics module for MTProxy connections

import os
import subprocess
import re
import time
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

def get_connection_count(port):
    """
    Get number of active connections on a specific port
    Returns: (total_connections, established_connections, time_wait_connections)
    """
    try:
        # Get all connections on the port
        result = subprocess.run(
            ['ss', '-tan', '|', 'grep', f':{port}'],
            shell=True,
            capture_output=True,
            text=True
        )
        
        lines = result.stdout.strip().split('\n')
        total = 0
        established = 0
        time_wait = 0
        other = 0
        
        for line in lines:
            if not line.strip():
                continue
            total += 1
            if 'ESTAB' in line:
                established += 1
            elif 'TIME-WAIT' in line:
                time_wait += 1
            else:
                other += 1
        
        return {
            'total': total,
            'established': established,
            'time_wait': time_wait,
            'other': other
        }
    except Exception as e:
        return {'total': 0, 'established': 0, 'time_wait': 0, 'other': 0}

def get_connection_count_netstat(port):
    """
    Alternative method using netstat (fallback)
    """
    try:
        result = subprocess.run(
            ['netstat', '-an', '|', 'grep', f':{port}'],
            shell=True,
            capture_output=True,
            text=True
        )
        
        lines = result.stdout.strip().split('\n')
        established = 0
        for line in lines:
            if 'ESTABLISHED' in line:
                established += 1
        
        return established
    except:
        return 0

def get_proxy_stats(proxy_name, port, server=None):
    """
    Get statistics for a specific proxy
    """
    stats = get_connection_count(port)
    
    # Try to get more detailed stats from logs
    log_stats = get_stats_from_logs(proxy_name)
    
    # Combine stats
    stats['online_users'] = stats['established']
    stats['offline_users'] = log_stats.get('offline_users', 0)
    stats['total_users'] = log_stats.get('total_users', stats['established'])
    
    return stats

def get_stats_from_logs(proxy_name):
    """
    Extract user statistics from proxy logs
    """
    try:
        # Get last 1000 lines of logs
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager', '-n', '1000'],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout
        
        # Count connections/disconnections for this proxy
        # Pattern: "User <name> connected" or "User <name> disconnected"
        connect_pattern = rf'User {proxy_name} .*connected'
        disconnect_pattern = rf'User {proxy_name} .*disconnected'
        
        connects = len(re.findall(connect_pattern, logs, re.IGNORECASE))
        disconnects = len(re.findall(disconnect_pattern, logs, re.IGNORECASE))
        
        # Try to get current online from the latest logs
        online_pattern = rf'User {proxy_name} .*connected'
        current_online = len(re.findall(online_pattern, logs[-1000:], re.IGNORECASE))
        
        return {
            'online_users': current_online,
            'offline_users': max(0, connects - disconnects),
            'total_users': connects
        }
    except Exception as e:
        return {'online_users': 0, 'offline_users': 0, 'total_users': 0}

def get_active_users_from_process(port):
    """
    Get active users by analyzing process connections
    """
    try:
        # Get PID of mtprotoproxy
        pid_result = subprocess.run(
            ['pgrep', '-f', 'mtprotoproxy.py'],
            capture_output=True,
            text=True
        )
        
        if not pid_result.stdout.strip():
            return 0
            
        pid = pid_result.stdout.strip().split('\n')[0]
        
        # Get connections for this PID
        result = subprocess.run(
            ['ss', '-tanp', '|', 'grep', f'pid={pid}'],
            shell=True,
            capture_output=True,
            text=True
        )
        
        # Count unique IPs (users)
        ips = set()
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 5:
                # Get remote IP (format: IP:PORT)
                remote = parts[4]
                if ':' in remote:
                    ip = remote.split(':')[0]
                    if ip and not ip.startswith('127.'):
                        ips.add(ip)
        
        return len(ips)
    except Exception as e:
        return 0

def display_proxy_stats(proxy_name, port, show_offline=True):
    """
    Display statistics for a single proxy
    """
    stats = get_connection_count(port)
    active_users = get_active_users_from_process(port)
    
    # For MTProto, we need to count connections per user
    # Each user might have multiple connections, so we need to estimate
    estimated_users = max(1, active_users) if active_users > 0 else 0
    
    print(f"\n{Colors.CYAN}📊 Statistics for {Colors.BOLD}{proxy_name}{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────{Colors.NC}")
    print(f"  {Colors.BLUE}●{Colors.NC} Active Connections: {Colors.GREEN}{stats['established']}{Colors.NC}")
    print(f"  {Colors.BLUE}●{Colors.NC} Time-Wait:          {Colors.YELLOW}{stats['time_wait']}{Colors.NC}")
    print(f"  {Colors.BLUE}●{Colors.NC} Total Connections:   {Colors.WHITE}{stats['total']}{Colors.NC}")
    print(f"  {Colors.BLUE}●{Colors.NC} Active Users:        {Colors.GREEN}{estimated_users}{Colors.NC}")
    
    # Estimate offline users (users that were connected but not now)
    if show_offline:
        total_history = get_total_historical_users(proxy_name)
        if total_history > 0:
            offline = max(0, total_history - estimated_users)
            print(f"  {Colors.BLUE}●{Colors.NC} Historical Users:     {Colors.WHITE}{total_history}{Colors.NC}")
            print(f"  {Colors.BLUE}●{Colors.NC} Offline Users:        {Colors.RED}{offline}{Colors.NC}")

def get_total_historical_users(proxy_name):
    """
    Get total number of users that have ever connected to this proxy
    """
    try:
        # Check if we have a stats file
        stats_file = f"/etc/mtpulse/stats_{proxy_name}.json"
        if os.path.exists(stats_file):
            import json
            with open(stats_file, 'r') as f:
                data = json.load(f)
                return data.get('total_users', 0)
    except:
        pass
    
    # Fallback: count unique connection logs
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'mtprotoproxy', '--no-pager'],
            capture_output=True,
            text=True
        )
        # Count unique user connections
        pattern = rf'User {proxy_name} .*connected'
        connections = re.findall(pattern, result.stdout, re.IGNORECASE)
        # Try to extract unique user IDs if possible
        unique_users = set()
        for conn in connections:
            # Extract user identifier if available
            match = re.search(r'User (\S+)', conn)
            if match:
                unique_users.add(match.group(1))
        return len(unique_users) if unique_users else len(connections)
    except:
        return 0

def update_stats_file(proxy_name, stats):
    """
    Save statistics to a file for persistence
    """
    import json
    stats_file = f"/etc/mtpulse/stats_{proxy_name}.json"
    try:
        os.makedirs('/etc/mtpulse', exist_ok=True)
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
    except:
        pass

def show_all_proxy_stats(proxies):
    """
    Display statistics for all proxies
    """
    print(f"\n{Colors.BOLD}{Colors.GREEN}📊 Overall Proxy Statistics{Colors.NC}")
    print(f"{Colors.CYAN}═════════════════════════════════════════════════{Colors.NC}")
    
    total_active = 0
    total_connections = 0
    
    for proxy_id, proxy in proxies.items():
        name = proxy.get('name', 'Unnamed')
        port = proxy.get('port', 443)
        server = proxy.get('server', 'default')
        
        stats = get_connection_count(port)
        active_users = get_active_users_from_process(port)
        
        total_active += active_users
        total_connections += stats['established']
        
        # Show status indicator
        if active_users > 0:
            status_icon = f"{Colors.GREEN}🟢 Online{Colors.NC}"
        else:
            status_icon = f"{Colors.RED}🔴 Offline{Colors.NC}"
        
        print(f"\n  {Colors.BOLD}{name}{Colors.NC}")
        print(f"    Server: {Colors.WHITE}{server}{Colors.NC}")
        print(f"    Port:   {Colors.WHITE}{port}{Colors.NC}")
        print(f"    Status: {status_icon}")
        print(f"    Active Connections: {Colors.GREEN}{stats['established']}{Colors.NC}")
        print(f"    Active Users:       {Colors.GREEN}{active_users}{Colors.NC}")
        
        # Show link if active
        if active_users > 0:
            # Generate proxy link
            from mtproxy import get_proxy_link
            link = get_proxy_link(proxy)
            print(f"    Link:   {Colors.CYAN}{link}{Colors.NC}")
    
    print(f"\n{Colors.CYAN}─────────────────────────────────────────────────{Colors.NC}")
    print(f"  {Colors.BOLD}Total Active Users:    {Colors.GREEN}{total_active}{Colors.NC}")
    print(f"  {Colors.BOLD}Total Connections:     {Colors.GREEN}{total_connections}{Colors.NC}")
    print(f"{Colors.CYAN}═════════════════════════════════════════════════{Colors.NC}")

def continuous_monitor(proxies, interval=5):
    """
    Continuous monitoring mode
    """
    print(f"{Colors.BOLD}{Colors.GREEN}📊 Continuous Monitoring Mode{Colors.NC}")
    print(f"{Colors.YELLOW}Press Ctrl+C to stop{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────{Colors.NC}")
    
    try:
        while True:
            # Clear screen
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print(f"{Colors.BOLD}{Colors.GREEN}📊 Proxy Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.NC}")
            print(f"{Colors.CYAN}─────────────────────────────────────────────────{Colors.NC}")
            
            show_all_proxy_stats(proxies)
            
            print(f"\n{Colors.YELLOW}⏱️  Updating every {interval} seconds... (Ctrl+C to exit){Colors.NC}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}✅ Monitoring stopped.{Colors.NC}")
