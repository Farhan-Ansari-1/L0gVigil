<p align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f2027,50:203a43,100:2c5364&height=200&section=header&text=L0gVigil&fontSize=50&fontColor=ffffff&animation=fadeIn&fontAlignY=35"/>
</p>

<h1 align="center">🛡️ L0gVigil – Real-time IPS & SSH Shield</h1>

<p align="center">
A lightweight Intrusion Prevention System that detects and blocks SSH brute-force attacks in real time.
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Platform](https://img.shields.io/badge/Platform-Linux-green)
![Firewall](https://img.shields.io/badge/Firewall-iptables%20%7C%20ip6tables-red)
![Security](https://img.shields.io/badge/Security-IPS-black)
![License](https://img.shields.io/badge/License-MIT-yellow)

</p>

---

# 🔍 Overview

**L0gVigil** is a high-performance **Python-based Intrusion Prevention System (IPS)** designed to protect Linux servers from **SSH brute-force attacks**.

It continuously monitors:

```
/var/log/auth.log
```

When repeated failed login attempts are detected, L0gVigil:

1. Identifies the attacking IP
2. Blocks it instantly using **iptables / ip6tables**
3. Sends a **Telegram alert with Geo-IP information**

This allows system administrators to detect and stop attacks **within seconds**.

---

# 🎥 Live Terminal Demo

```bash
[INFO] L0gVigil started
[INFO] Monitoring /var/log/auth.log

[ALERT] Failed SSH login detected
IP: 45.77.12.88
User: root
Port: 22

[WARNING] Multiple failures detected
Attempts: 5 within 10 minutes

[ACTION] Blocking IP via firewall...

iptables -A INPUT -s 45.77.12.88 -j DROP

[SUCCESS] Attacker blocked
Telegram alert sent
```

---

# 🚀 Key Features

## 🔐 Dual Stack Protection

Supports both **IPv4 and IPv6** attacks using:

* iptables
* ip6tables

Including protection against localhost abuse (`::1`).

---

## 🧠 Stateful Attack Detection

Uses a **Sliding Window Algorithm** to track authentication failures within a configurable time period.

Example:

```
5 failed attempts within 10 minutes
```

Triggers automatic blocking.

---

## 💾 Persistent Firewall Bans

Blocked IP addresses are stored in:

```
blocked_ips.json
```

When the server restarts, L0gVigil automatically restores all bans.

---

## 🌍 Geo-IP Intelligence

Each attack alert includes:

* Country
* City
* ISP

Example:

```
Geo: Mumbai, India
ISP: Reliance Jio
```

---

## 🌐 Distributed Botnet Detection

Tracks **global authentication failure rates** to detect distributed attacks across multiple IP addresses.

---

## ⚡ High Performance

Uses **threading and non-blocking operations** so monitoring never slows down even under heavy attack traffic.

---

## 🔄 Automatic Unban System

Blocked IP addresses are automatically removed after a defined time.

Example default:

```
24 hours
```

This keeps firewall rules clean and prevents permanent blocks.

---

# 🧠 System Architecture

```
┌────────────────────┐
│  /var/log/auth.log │
└──────────┬─────────┘
           │
           ▼
┌────────────────────┐
│      LogTailer     │
│  Real-time reader  │
└──────────┬─────────┘
           │
           ▼
┌────────────────────┐
│     Regex Engine   │
│ Extract IP / User  │
└──────────┬─────────┘
           │
           ▼
┌────────────────────┐
│   Sliding Window   │
│ Attack detection   │
└──────────┬─────────┘
           │
           ▼
┌────────────────────────────┐
│        Action Worker       │
├──────────────┬─────────────┤
│   iptables   │   Telegram  │
│   Firewall   │   Alerts    │
└──────────────┴─────────────┘
```

---

# 📦 Installation

## 1. Requirements

* Linux server (Ubuntu / Debian recommended)
* Python **3.8+**
* iptables / ip6tables
* sudo privileges

---

## 2. Clone Repository

```bash
git clone https://github.com/Farhan-Ansari-1/L0gVigil.git
cd L0gVigil
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ⚙️ Configuration

Create a file called:

```
config.json
```

Example configuration:

```json
{
  "LOG_FILE": "/var/log/auth.log",
  "TELEGRAM_TOKEN": "YOUR_BOT_TOKEN",
  "TELEGRAM_CHAT_ID": "YOUR_CHAT_ID",
  "IPINFO_TOKEN": "FREE",
  "WHITELIST": ["127.0.0.1", "::1", "192.168.1.0/24"],
  "MAX_FAILS": 5,
  "WINDOW_MINUTES": 10,
  "GLOBAL_MAX_FAILS": 100,
  "GLOBAL_WINDOW_MINUTES": 5,
  "UNBAN_HOURS": 24,
  "BLOCKED_JSON": "blocked_ips.json"
}
```

---

# 🚦 Usage

## Run Manually

```bash
sudo python3 L0gVigil.py
```

---

## Run as Background Service

Copy the service file:

```bash
sudo cp l0gvigil.service /etc/systemd/system/
```

Reload systemd:

```bash
sudo systemctl daemon-reload
```

Enable service:

```bash
sudo systemctl enable --now l0gvigil
```

Check status:

```bash
sudo systemctl status l0gvigil
```

---

# 📩 Telegram Alert Example

```
🚨 BRUTE FORCE DETECTED

IP: 1.2.3.4
Target: root:22

Geo: Mumbai, India
ISP: Reliance Jio

Status: IP Blocked Successfully
```

---

# 📂 Project Structure

```
L0gVigil
│
├── L0gVigil.py
├── config.json
├── requirements.txt
├── blocked_ips.json
├── l0gvigil.service
└── README.md
```

---

# ⚖️ Disclaimer

This tool is intended for **educational purposes and personal server hardening**.

Always test in a **staging environment** before deploying to production systems.

The author is not responsible for misuse or damage caused by improper configuration.

---

<p align="center">
⭐ If you find this project useful, consider giving it a star on GitHub!
</p>
