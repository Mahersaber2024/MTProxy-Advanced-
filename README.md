# MTPulse Proxy Manager

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Ubuntu%20%7C%20Debian-lightgrey)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-yellow.svg)]()

🚀 **MTPulse** is a lightweight, interactive management tool for **MTProto Proxy** (Telegram Proxy) on Ubuntu and Debian servers.

It helps you install, manage, configure, and remove MTProto Proxy with a simple menu-driven interface, similar in style to `x3-tf`.

---

## Features

- Install MTProto Proxy from source.
- Manage the proxy service with start, stop, restart, and status commands.
- View live logs and troubleshoot easily.
- Add or remove sponsor tags using `@MTProxybot` AD tags.
- Uninstall the proxy and clean up installed files.
- Colorful interactive terminal menu.
- Lightweight Python-based implementation.
- Sponsored by [HeySolo](https://t.me/HeySoloATM).

---

## Requirements

- Ubuntu 20.04+ or Debian 11+.
- Python 3.8 or newer.
- Root or sudo access.
- Required packages: `git`, `make`, `build-essential`, `libssl-dev`, `zlib1g-dev`, `curl`, `wget`, `xxd`, `figlet`.

---

## Quick Installation

Run the installer on your server:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/Mahersaber2024/MTProxy-Advanced-/main/install.sh)
```

---

## Usage

After installation, open the management menu with:

```bash
mtpulse
```

Or, if the script is installed with elevated permissions:

```bash
sudo mtpulse
```

The menu lets you manage the proxy, change settings, and view status without manually editing files.

---

## Service Management

Use these commands to control the service:

```bash
systemctl status mtpulse.service
systemctl start mtpulse.service
systemctl stop mtpulse.service
systemctl restart mtpulse.service
journalctl -u mtpulse.service -f
```

If your project uses a separate timer or update script, document it here as well.

---

## Sponsored Tag

This project supports adding a sponsor tag from `@MTProxybot` for Telegram proxy traffic.

Example usage:

- Add sponsor tag.
- Restart the proxy service.
- Verify the proxy is working correctly.

---

## Uninstallation

To remove MTPulse and its installed components:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/Mahersaber2024/MTProxy-Advanced-/main/uninstall.sh)
```

---

## Files

- `install.sh` — Main installation script.
- `manager.py` — Interactive management menu.
- `proxy.py` or main runtime script — Proxy control logic, if present.
- `uninstall.sh` — Removal script.
- `requirements.txt` — Python dependencies.

---

## Notes

- Make sure ports required by MTProto Proxy are open.
- Run the installer as root or with sudo privileges.
- If the menu does not open, check that the installed script has executable permissions and uses Unix line endings.

---

## Troubleshooting

### Menu does not start
Check whether the installed launcher exists and is executable:

```bash
which mtpulse
ls -l /usr/local/bin/mtpulse
```

### Service fails to start
View logs:

```bash
journalctl -u mtpulse.service -n 50 --no-pager
```

### Permission issues
Run the commands as root or with `sudo`.

---

## Contributing

Pull requests and improvements are welcome.  
If you want to contribute, fork the repository, create a feature branch, and submit a pull request.

---

## License

Add your preferred license here, such as MIT.

---

## Disclaimer

Use this tool only on servers and proxies that you own or are authorized to manage.
