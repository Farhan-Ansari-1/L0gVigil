<p align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f2027,50:203a43,100:2c5364&height=200&section=header&text=L0gVigil&fontSize=50&fontColor=ffffff&animation=fadeIn&fontAlignY=35"/>
</p>

<h1 align="center">🛡️ L0gVigil – Real-time IPS & SSH Shield</h1>

<p align="center">
A powerful Intrusion Prevention System that detects, analyzes, and blocks SSH brute-force attacks in real time.
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Platform](https://img.shields.io/badge/Platform-Linux-green)
![Firewall](https://img.shields.io/badge/Firewall-iptables%20%7C%20ip6tables-red)
![Security](https://img.shields.io/badge/Security-IPS-black)
![License](https://img.shields.io/badge/License-MIT-yellow)

</p>

---

# 🎬 Demo Preview

<p align="center">
<img src="docs/demo.gif" width="800"/>
</p>

> ⚠️ Replace this with a real demo GIF of your dashboard (recommended for better engagement)

---

# 🔍 Overview

**L0gVigil** is a high-performance **Python-based Intrusion Prevention System (IPS)** built to secure Linux servers against **SSH brute-force attacks**.

It continuously monitors:

```bash
/var/log/auth.log
```

When suspicious activity is detected, it:

* Detects repeated failed login attempts
* Identifies attacker IP address
* Blocks the IP instantly via firewall
* Sends real-time alerts via Telegram
* Stores attack data for analysis

---

# 🧠 System Architecture

```text
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

# 🚀 Key Features

* 🔐 Dual-stack protection (IPv4 + IPv6)
* 🧠 Sliding window attack detection
* 💾 Persistent IP blocking (SQLite + JSON)
* 🌍 Geo-IP tracking (City, Country, ISP)
* 🌐 Botnet detection (global fail tracking)
* ⚡ Threaded high-performance engine
* 🔄 Automatic unban system
* 📊 Real-time React dashboard

---

# 💻 Live Detection Example

```bash
[INFO] L0gVigil started
[INFO] Monitoring /var/log/auth.log

[ALERT] Failed SSH login detected
IP: 45.77.12.88
User: root
Port: 22

[WARNING] Threshold exceeded (5 attempts / 10 min)

[ACTION] Blocking attacker...

iptables -A INPUT -s 45.77.12.88 -j DROP

[SUCCESS] IP blocked
Telegram alert sent
```

---

# 📦 Installation

## 1️⃣ Requirements

* Linux (Ubuntu/Debian recommended)
* Python 3.8+
* iptables / ip6tables
* sudo access

---

## 2️⃣ Clone Repository

```bash
git clone https://github.com/Farhan-Ansari-1/L0gVigil.git
cd L0gVigil
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ⚙️ Configuration

Create `config.json`:

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

## Run Core Engine

```bash
sudo python3 L0gVigil.py
```

---

## Run Backend API

```bash
cd backend
uvicorn main:app --reload
```

API runs at:

```
http://localhost:8000
```

---

## Run Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```
http://localhost:5173
```

---

# 📊 Dashboard API

* `GET http://localhost:8000/attacks` → fetch recent attacks
* `GET http://localhost:8000/stats` → fetch statistics
* `DELETE http://localhost:8000/attacks/{id}` → remove attack

---

# 📂 Project Structure

```bash
L0gVigil/
│
├── frontend/              # React Dashboard
│   └── src/App.jsx
│
├── backend/               # FastAPI API
│   └── main.py
│
├── L0gVigil.py            # Core IPS Engine
├── config.json
├── blocked_ips.db
├── requirements.txt
├── l0gvigil.service
│
├── docs/
│   └── demo.gif
│
└── README.md
```

---

# 📩 Telegram Alert Example

```
🚨 BRUTE FORCE DETECTED

IP: 1.2.3.4
User: root

Geo: Mumbai, India
ISP: Reliance Jio

Status: Blocked Successfully
```

---

# ⚖️ Disclaimer

This project is intended for **educational and defensive security purposes only**.

* Do not use on systems you do not own
* Always test in a staging environment
* Use responsibly

---

<p align="center">
⭐ Star this repo if you like it — and build your cyber arsenal ⚡
</p>
