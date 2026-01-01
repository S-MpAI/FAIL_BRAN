# Fail2Ban Control Panel

A lightweight interactive CLI control panel written in Python for managing **Fail2Ban** bans across multiple jails, with additional verification at the **firewall level (nftables / iptables-nft)**.

This tool is designed for system administrators who want a clear, centralized way to:

* Manually ban or unban IP addresses
* Apply bans to a specific jail or **all jails at once**
* Inspect where an IP is blocked (Fail2Ban + firewall)
* View all active bans across the system

---

## Features

* Interactive terminal menu (no arguments required)
* Automatic detection of all active Fail2Ban jails
* Ban an IP:

  * in a specific jail
  * in **all jails simultaneously**
* Unban an IP from all jails where it is present
* Check IP status:

  * lists all jails where the IP is banned
  * verifies if the IP is present in firewall rules (nftables / iptables-nft)
* Show all active banned IPs with associated jails
* Clean UI:

  * ASCII logo
  * screen clearing (`cls`) between actions
* Works with modern Linux systems using **nftables (iptables-nft backend)**

---

## Requirements

* Linux system
* Python **3.9+** (tested on Python 3.12)
* Fail2Ban installed and running
* `fail2ban-client` available in PATH
* `nft` command available (for firewall verification)
* Root privileges (required for Fail2Ban and firewall access)

---

## Installation

Clone the repository:

```bash
git clone https://github.com/S-MpAI/FAIL_BRAN.git
cd fail2ban-control-panel
```

(Optional but recommended) Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

No external Python dependencies are required.

---

## Usage

Run the panel as root:

```bash
sudo python3 main.py
```

You will see an interactive menu:

```
1. Ban IP
2. Unban IP
3. Check IP
4. Show all bans
5. Exit
```

### Ban IP

* Enter the IP address
* Select a jail from the list
* Or choose **0** to ban the IP in all jails

### Unban IP

* Enter the IP address
* The tool automatically removes it from all jails where it is banned

### Check IP

* Shows:

  * all Fail2Ban jails where the IP is banned
  * whether the IP is present in firewall rules (nftables / iptables)

### Show all bans

* Lists all currently banned IPs
* Displays the jails in which each IP is banned

---

## Firewall Detection Logic

The panel verifies firewall-level blocking using:

* `nft list ruleset`
* Fallback to `iptables -L -n` (legacy systems)

Warnings from `iptables-nft` are intentionally suppressed to keep output clean.

> Note: The panel does **not** directly modify firewall rules. Firewall changes are handled exclusively by Fail2Ban.

---

## Security Notes

* Always run the tool as **root**.
* Do not manually edit nftables tables managed by iptables-nft.
* This tool is intended for administrative environments, not shared systems.

---

## Tested Environment

* Debian / Ubuntu
* nftables backend (`iptables-nft`)
* Fail2Ban 0.11+

---

## Roadmap (Optional Ideas)

* Persistent manual bans with custom expiration
* Web-based UI
* Export ban lists (JSON / CSV)
* Integration with AbuseIPDB or similar services

---

## License

MIT License

---

## Author

Developed for practical system administration and learning purposes.
Contributions and improvements are welcome.
