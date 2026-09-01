# MTProxy Manager v3.5.0
A complete tool to install, manage, and monitor MTProto Proxy on Ubuntu/Debian.

## Features
âœ… **MTProto Proxy (Telegram)**
- Install and manage multiple proxies per IP/domain
- Start, stop, restart services
- View real-time stats: Online users, Peak, Total connects, Traffic usage
- Add sponsor tags for ads
- TLS domain spoofing

âœ… **SOCKS5 Proxy (Non-Telegram)** - NEW
- Run alongside MTProto for browsers, SSH, torrent clients
- Per-user authentication
- Real traffic accounting (accurate usage)
- Easy import: `ip:port:user:pass`

âœ… **Fixed Usage Accounting** - NEW
- Usage numbers now **accurate** and **survive restarts**
- Shows: Online / Peak / Connects / Traffic per proxy
- Previous bug (always 0 B) is fixed

âœ… **Bulk Operations**
- Delete all proxies at once (with double confirmation)
- Auto-restart program after update

## Requirements
- Ubuntu 22.04+ or Debian 12+
- Python 3.8+
- Root/sudo access

## Installation

### Option 1: Online (from GitHub)
```bash
bash <(curl -Ls https://raw.githubusercontent.com/Mahersaber2024/MTProxy-Advanced-/main/install.sh)
```

### Option 2: Offline (embedded files, no GitHub needed)
Download `mtproxy-3.5.0-offline-installer.sh`, then:
```bash
sudo bash mtproxy-3.5.0-offline-installer.sh
```

## Usage

### Run the manager
```bash
mtproxy
```

### Main Menu
```
1. âž• Add Proxy (with custom IP/domain)
2. âš™ï¸ Service Management (start/stop/restart)
3. ðŸ“ Add Tag to Proxy (sponsor ads)
4. âž– Remove Proxy (delete one)
5. ðŸŒ Edit Default Server Settings
6. ðŸ”„ Update to Latest Version (auto-restarts)
7. ðŸ§¦ SOCKS5 Proxy (non-Telegram) â† NEW
8. ðŸ—‘ï¸ Delete ALL Proxies (with confirmation) â† NEW
0. ðŸšª Exit
```

## Examples

### Add MTProto Proxy
```
mtproxy â†’ 1
Enter proxy name: MyProxy
Enter server IP (leave empty for auto-detect): 1.2.3.4
Press Enter for default port (443)
Generated secret: abc123...
Link: tg://proxy?server=1.2.3.4&port=443&secret=abc123...
```

### Add SOCKS5 Proxy
```
mtproxy â†’ 7
Paste: 143.14.59.117:823:proxyuser:proxyuser1
```
Or fill manually. Get link for browsers/Telegram/SSH:
```
socks5://proxyuser:proxyuser1@143.14.59.117:823
```

### Update to Latest
```
mtproxy â†’ 6 â†’ y
```
Program auto-clears old code, downloads new files, and restarts itself.

**If download fails**, you'll see:
```
âŒ Download failed. Files not in GitHub yet?
Solution: Use the offline installer instead
```

### Delete All Proxies
```
mtproxy â†’ 8
Type 'delete all' to confirm (case sensitive)
Type 'yes' to confirm again
All proxies deleted.
```

## Troubleshooting

### Update stuck/hangs
- Network timeout? Waits max 30 seconds per file
- If fails: automatic rollback to backup
- Check: `journalctl -u mtprotoproxy -n 50`

### Usage shows 0 B
- Need ~1-2 minutes of **live traffic** before numbers update
- Check service is running: `systemctl status mtprotoproxy`

### SOCKS5 connection fails
- Test: `mtproxy â†’ 7 â†’ 4 (Test proxy)`
- If outside: port blocked by firewall/provider
- Check logs: `journalctl -u mtsocks -n 30`

### Rollback after bad update
```bash
cp /tmp/mtproxy_backup_TIMESTAMP/* /usr/local/bin/
mtproxy
```

## Service Management

### Start/Stop manually
```bash
sudo systemctl restart mtprotoproxy
sudo systemctl restart mtsocks          # SOCKS5
sudo systemctl status mtprotoproxy
```

### View logs
```bash
journalctl -u mtprotoproxy -n 50 --no-pager
journalctl -u mtsocks -n 50 --no-pager
```

### Uninstall
```bash
# Via menu
mtproxy â†’ 6 (if available)

# Or manually
bash <(curl -Ls https://raw.githubusercontent.com/Mahersaber2024/MTProxy-Advanced-/main/uninstall.sh)
```

## Version History

### v3.5.0
- âœ¨ SOCKS5 proxy support (non-Telegram)
- ðŸ”§ FIXED: Traffic usage counting (was always 0 B)
- ðŸ“Š Accurate usage survives service restarts
- ðŸ—‘ï¸ Bulk delete all proxies
- ðŸ”„ Auto-restart after update
- ðŸ“¡ Real-time log viewer

### v3.4.1
- Basic proxy management
- Tag support

## Configuration Files
```
/opt/mtprotoproxy/          MTProto proxy root
/etc/mtpulse/proxies.json   MTProto proxy list
/etc/mtpulse/socks.json     SOCKS5 user/pass
/etc/mtpulse/usage.json     Usage counters
```

## Author
Mahersaber2024

## Support
- Logs: `journalctl -u mtprotoproxy -f`
- Contact: @jadetunnel (Telegram)
