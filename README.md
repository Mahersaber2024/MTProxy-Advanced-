# MTProxy Manager

A comprehensive management tool for **MTProto Proxy** (Telegram Proxy) on Ubuntu and Debian servers.

Developed in Python, it provides an interactive menu to install, manage, configure, test, and remove MTProto proxy instances with ease. It supports multiple proxies with different IP addresses, ports, secrets, and domains, making it useful for personal deployments and multi-instance server management.

---

## ✨ Features

- 📥 **Automatic Installation** – Installs MTProto Proxy from the official source during setup.
- ➕ **Add Multiple Proxies** – Each proxy can have its own IP/domain, port, secret, and TLS domain.
- ⚙️ **Service Management** – Start, stop, restart, check status, and view logs for each proxy individually.
- 📝 **Sponsor Tag Support** – Assign AD tags to individual proxies from `@MTProxybot`.
- 🔍 **Real Proxy Testing** – Test proxies using `pyrogram` to verify a real MTProto connection to Telegram.
- 🏷️ **Tag Status Display** – View proxy tags directly in the main menu.
- 🌐 **Custom Server Address** – Set a default or per-proxy IP/domain for client connections.
- 🎨 **Beautiful Interactive Menu** – Colorful, user-friendly CLI interface.
- 🗑️ **Uninstallation Support** – Remove the project and installed components cleanly.

---

## 📋 Requirements

- **OS**: Ubuntu 22.04+ or Debian 12+
- **Python**: 3.8+
- **Root/Sudo**: Required for installation and management
- **Network**: A public IP or domain is recommended
- **Firewall**: Required ports must be open
- **Dependencies**: Installed automatically by the installer script

---

## 🚀 Quick Installation

Run this command on your server:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/Mahersaber2024/MTProxy-Advanced-/main/install.sh)
```

Follow the interactive menu to install and manage your proxy instances.

---

## 📦 Manual Installation

```bash
git clone https://github.com/Mahersaber2024/MTProxy-Advanced-.git
cd MTProxy-Advanced-
chmod +x install.sh
sudo ./install.sh
```

---

## ⚙️ How It Works

This project simplifies MTProto proxy management by wrapping the official proxy binary and service logic in a Python-based control panel.

Typical workflow:

1. Install the proxy binary.
2. Generate or define a secret.
3. Set a listening port.
4. Add an optional sponsor tag.
5. Start the service.
6. Test connectivity.
7. Manage multiple proxy instances from the same interface.

Telegram’s MTProxy setup normally uses the official proxy components and requires a secret plus configuration files from Telegram’s endpoints [web:11]. Sponsor tags are commonly attached through `@MTProxybot` as part of the proxy promotion workflow [web:11][web:12].

---

## 🔐 Proxy Setup Notes

Before starting a proxy, make sure you have:

- A generated MTProto secret.
- An open TCP port on the server firewall.
- A valid public IP or domain.
- An optional sponsor tag from `@MTProxybot`.

A standard MTProxy deployment uses the proxy binary with a secret and Telegram’s configuration files [web:11][web:13]. In many setups, the proxy is run as a `systemd` service for stable startup and lifecycle control [web:12][web:13].

---

## 🧪 Testing

The project includes real proxy testing using `pyrogram`, which helps confirm that the proxy can actually connect to Telegram rather than only checking whether the port is open.

Recommended checks:

- Service status.
- Log output.
- Telegram connection test.
- Port reachability from outside the server.

---

## 🖥️ Menu Options

The interactive menu may include actions such as:

- Install MTProto Proxy.
- Add new proxy.
- Remove proxy.
- Start proxy.
- Stop proxy.
- Restart proxy.
- Check proxy status.
- View proxy logs.
- Test proxy connection.
- Manage AD tag.
- Show proxy list.
- Uninstall project components.

---

## 🗑️ Uninstallation

To remove **MTProxy Manager** and its installed components, use the project’s uninstall option if it is available in the menu.

If your project includes a dedicated uninstall script, run:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/Mahersaber2024/MTProxy-Advanced-/main/uninstall.sh)
```

If there is no script yet, uninstallation usually requires manual cleanup of the installed files and services.

### Manual cleanup may include:

- Stopping and disabling related `systemd` services.
- Removing proxy binaries and project files.
- Deleting configuration directories.
- Removing log files.
- Reloading `systemd` after cleanup.

Example commands:

```bash
sudo systemctl stop MTProxy.service
sudo systemctl disable MTProxy.service
sudo rm -f /etc/systemd/system/MTProxy.service
sudo systemctl daemon-reload
sudo systemctl reset-failed
```

Then remove the project files and related data:

```bash
sudo rm -rf /opt/MTProxy
sudo rm -rf /path/to/MTProxy-Advanced-
```

> Make sure to back up any important proxy configuration before uninstalling.

---

---

## 🌍 Supported Platforms

- Ubuntu 22.04+.
- Debian 12+.
- VPS or dedicated Linux servers.
- Cloud servers with public IPs.

---

## 🧱 Firewall Requirements

Make sure the required proxy port is allowed through your firewall.

Example with UFW:

```bash
sudo ufw allow 443/tcp
sudo ufw reload
```

If you use a different port, replace `443` with your chosen port.

---

## 🧰 Dependencies

The installer may include packages such as:

- `python3`
- `python3-pip`
- `git`
- `curl`
- `screen` or `tmux`
- `systemd`
- `pyrogram` for testing

---

## 🧭 Example Proxy Flow

1. Install the project.
2. Choose “Add Proxy” from the menu.
3. Enter server IP or domain.
4. Set proxy port.
5. Paste or generate MTProto secret.
6. Optionally set sponsor tag.
7. Start the proxy.
8. Test the proxy connection.

---

## 🛡️ Security Tips

- Use a strong secret for every proxy.
- Keep the server updated.
- Restrict SSH access.
- Monitor logs regularly.
- Avoid exposing unnecessary ports.
- Use a domain with a stable DNS setup when possible.

---

## 🐞 Troubleshooting

### Proxy does not start
- Check if the port is already in use.
- Verify that the secret is valid.
- Confirm that the system service file is correct.

### Telegram connection fails
- Make sure the server can reach Telegram endpoints.
- Check firewall and NAT rules.
- Verify that the proxy config files are present and current.

### Sponsor tag is not visible
- Confirm the tag from `@MTProxybot`.
- Restart the proxy after applying the tag.
- Recheck the proxy configuration.

---

## 📌 Disclaimer

This project is provided for legitimate proxy management and administration purposes. Users are responsible for complying with local laws, hosting provider policies, and Telegram’s terms of service.

---
