# L0gVigil – Real-time Log Monitor & Intrusion Prevention System

**L0gVigil** is a Python-based security script designed to detect and block brute-force attacks by monitoring system authentication logs (`/var/log/auth.log`) in real time. It automatically blocks malicious IP addresses using `iptables`, sends instant alerts via Telegram, and includes advanced features such as whitelisting, geo-tracking, and automatic unbanning.

---

## Features

* **Real-time Log Tailing**
  Continuously follows the authentication log file and gracefully handles log rotation.

* **Regex Intelligence**
  Parses logs using regex patterns to detect failed and successful login attempts.

* **Stateful Rate Limiting**
  Uses a sliding time window to detect multiple failures from the same IP address (e.g., 5 failures within 10 minutes).

* **Distributed Attack Detection**
  Monitors the global failure rate to detect potential botnet or distributed brute-force attacks.

* **Automatic IP Blocking**
  Integrates with `iptables` to instantly block malicious IP addresses.

* **Automatic Unbanning**
  Blocked IPs are automatically unbanned after a configurable duration (default: 24 hours).

* **Persistent Blocking**
  Blocked IP addresses are saved and restored after a system reboot.

* **Geo-IP Tracking**
  Enriches alerts with attacker location details such as country, city, and ISP.

* **Whitelist Support**
  Prevents trusted IP addresses from being blocked (supports CIDR notation).

* **Telegram Alerts**
  Sends detailed real-time notifications for every blocked IP address.

* **Thread-safe and Efficient**
  Uses threading for non-blocking network operations and is optimized for low CPU and RAM usage.

---

## Installation and Usage

### 1. Prerequisites

* Linux system (tested on Debian/Ubuntu)
* Python 3.6+
* `iptables`
* `git`

---

### 2. Clone the Repository

```bash
git clone https://github.com/Farhan-Ansari-1/L0gVigil.git
cd L0gVigil
```

---

### 3. Install Dependencies

Install the required Python libraries:

```bash
pip install -r requirements.txt
```

---

### 4. Configure the Script

Open `L0gVigil.py` and edit the configuration section at the top of the file:

```python
# Configuration - EDIT THESE!
LOG_FILE = '/var/log/auth.log'
TELEGRAM_TOKEN = 'YOUR_BOT_TOKEN_HERE'
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID_HERE'
IPINFO_TOKEN = 'FREE'  # Or your paid token
WHITELIST = ['127.0.0.1', '192.168.1.0/24', 'YOUR_HOME_IP']
UNBAN_HOURS = 24
```

---

### 5. Run the Script

The script requires `sudo` privileges to interact with `iptables`.

```bash
sudo python3 L0gVigil.py
```

The script will now run in the foreground and continuously monitor your authentication log file.
