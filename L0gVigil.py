#!/usr/bin/env python3
"""
The L0gVigil - Real-time SSH Brute Force Detector & IPS
Monitors /var/log/auth.log, detects attacks, blocks IPs, sends alerts.
Run with: sudo python3 l0gvigil.py
"""

import time
import re
import json
import threading
import os
import subprocess
import requests
from datetime import datetime, timedelta
import ipaddress
from collections import defaultdict, deque
import logging

# Configuration - EDIT THESE!
LOG_FILE = '/var/log/auth.log'  # Common Linux auth log
TELEGRAM_TOKEN = 'YOUR_BOT_TOKEN_HERE'  # From @BotFather
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID_HERE'  # Your chat/channel ID
IPINFO_TOKEN = 'FREE'  # Or get free token from ipinfo.io
WHITELIST = ['127.0.0.1', '192.168.1.0/24', 'YOUR_HOME_IP']  # Add your IPs!
MAX_FAILS = 5
WINDOW_MINUTES = 10
# Global rate limiting for distributed attack detection
GLOBAL_MAX_FAILS = 100 # Total fails from ALL IPs in GLOBAL_WINDOW_MINUTES
GLOBAL_WINDOW_MINUTES = 5
UNBAN_HOURS = 24  # Unban IP after this many hours
BLOCKED_JSON = 'blocked_ips.json'
file_lock = threading.Lock()
banned_ips = {} # Memory store for active bans: {ip: datetime_object}
banned_ips_lock = threading.Lock()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SlidingWindow:
    """Memory-efficient rate limiter with time window."""
    def __init__(self, max_fails, window_minutes):
        self.max_fails = max_fails
        self.window = timedelta(minutes=window_minutes)
        self.counts = {}  # IP -> deque of timestamps
        self.lock = threading.Lock()

    def add_attempt(self, ip):
        now = datetime.now()
        with self.lock:
            if ip not in self.counts:
                self.counts[ip] = deque()
            # Remove old attempts
            self.counts[ip] = deque([ts for ts in self.counts[ip] if now - ts < self.window])
            self.counts[ip].append(now)
            count = len(self.counts[ip])
            logger.info(f"IP {ip}: {count}/{self.max_fails} fails in window")
            return count >= self.max_fails

    def cleanup(self):
        now = datetime.now()
        with self.lock:
            to_remove = [ip for ip, deq in self.counts.items() if not deq or now - deq[0] > self.window]
            for ip in to_remove:
                del self.counts[ip]

class LogTailer:
    """Efficient log tailer that handles rotation."""
    def __init__(self, filename):
        self.filename = filename
        self.file = None
        self.position = 0
        self._open_file()

    def _open_file(self):
        try:
            self.file = open(self.filename, 'r')
            self.file.seek(0, 2)
            self.position = self.file.tell()
            logger.info(f"Tailing {self.filename}")
        except Exception as e:
            logger.error(f"Failed to open log: {e}")
            time.sleep(5)

    def read_lines(self):
        if not self.file:
            self._open_file()
            return
        self.file.seek(self.position)
        lines = self.file.readlines()
        if lines:
            self.position = self.file.tell()
        # Check for rotation (file shrank or stat changed)
        stat = os.stat(self.filename)
        if self.position > stat.st_size:
            logger.info("Log rotated, reopening")
            self.file.close()
            self._open_file()
            return self.read_lines()
        return [line.rstrip() for line in lines]

def is_whitelisted(ip):
    """Checks if an IP is in the whitelist (supports single IPs and CIDR)."""
    try:
        client_ip = ipaddress.ip_address(ip)
    except ValueError:
        logger.error(f"Invalid IP address format for whitelisting check: {ip}")
        return False

    for wl_entry in WHITELIST:
        try:
            if '/' in wl_entry:
                network = ipaddress.ip_network(wl_entry, strict=False)
                if client_ip in network:
                    return True
            elif client_ip == ipaddress.ip_address(wl_entry):
                return True
        except ValueError:
            logger.warning(f"Invalid entry in WHITELIST: '{wl_entry}'. Skipping.")
            continue
    return False

def block_ip(ip):
    # Whitelist check is now done before calling this function.
    try:
        subprocess.run(['iptables', '-I', 'INPUT', '1', '-s', ip, '-j', 'DROP'], check=True)
        logger.warning(f"BLOCKED IP: {ip}")
        
        now = datetime.now()
        with banned_ips_lock:
            banned_ips[ip] = now
            
        # Log to JSON
        log_entry = {
            'ip': ip,
            'blocked_at': now.isoformat(),
            'reason': 'brute force'
        }
        try:
            with file_lock:
                with open(BLOCKED_JSON, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write to {BLOCKED_JSON}: {e}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error(f"Failed to block {ip}")
        return False

def unban_ip(ip):
    """Unblocks an IP from iptables."""
    try:
        subprocess.run(['iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP'], check=True)
        logger.info(f"UNBANNED IP: {ip} (Expired after {UNBAN_HOURS}h)")
        return True
    except subprocess.CalledProcessError:
        logger.error(f"Failed to unban {ip} - rule might not exist")
        return False

def cleanup_banned_ips():
    """Checks for expired bans and removes them."""
    now = datetime.now()
    with banned_ips_lock:
        # Create a copy of keys to iterate safely
        for ip in list(banned_ips.keys()):
            block_time = banned_ips[ip]
            if now - block_time > timedelta(hours=UNBAN_HOURS):
                if unban_ip(ip):
                    del banned_ips[ip]

def get_geo(ip):
    """Free IP geolocation."""
    try:
        if IPINFO_TOKEN == 'FREE':
            r = requests.get(f'https://ipinfo.io/{ip}/json', timeout=3)
        else:
            r = requests.get(f'https://ipinfo.io/{ip}/json', 
                           headers={'Authorization': f'Bearer {IPINFO_TOKEN}'}, timeout=4)
        data = r.json()
        return f"{data.get('city', 'N/A')}, {data.get('country', 'N/A')} | ISP: {data.get('org', 'N/A')}"
    except Exception as e:
        return f"Geo unavailable ({type(e).__name__})"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}
        requests.post(url, data=data, timeout=5)
    except:
        logger.error("Telegram alert failed")

def parse_line(line):
    """Extract IP, user, port, type with regex."""
    # Common auth.log patterns [web:2][web:9][web:14]
    patterns = [
        r"Failed password for(?: invalid user)? (\w+) from (\S+) port (\d+)",
        r"Invalid user (\w+) from (\S+) port (\d+)",
        r"Accepted password for (\w+) from (\S+) port (\d+)"
    ]
    for pat in patterns:
        match = re.search(pat, line)
        if match:
            user, ip, port = match.groups()
            return ip, user, port, 'success' if 'Accepted' in line else 'fail'
    return None

def process_attack(ip, user, port):
    """
    Handles the entire process of blocking an IP, logging, and alerting.
    This is run in a separate thread to avoid blocking the main loop.
    """
    # The IP is already confirmed to be over the limit and not whitelisted.
    if block_ip(ip):
        # If blocking was successful, proceed with geo-lookup and alerting.
        geo = get_geo(ip)
        msg = (f"🚨 <b>BRUTE FORCE BLOCKED!</b>\n\n"
               f"<b>IP:</b> <code>{ip}</code>\n"
               f"<b>Target:</b> {user}:{port}\n"
               f"<b>Geo:</b> {geo}\n"
               f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        send_telegram(msg)

def restore_blocked_ips():
    """
    Reads BLOCKED_JSON and re-applies iptables rules on startup.
    Optimized to fetch existing rules once to avoid slow, per-IP checks.
    """
    logger.info("Restoring previously blocked IPs from block list...")
    if not os.path.exists(BLOCKED_JSON):
        logger.info(f"{BLOCKED_JSON} not found. Starting fresh.")
        return
    
    # Optimization: Get all currently blocked IPs from iptables in one go.
    existing_blocked_ips = set()
    use_optimized_check = False
    try:
        result = subprocess.run(['iptables', '-L', 'INPUT', '-n'], capture_output=True, text=True, check=True)
        # Parse the output and store IPs in a set for O(1) lookups.
        existing_blocked_ips = set(re.findall(r"^DROP\s+all\s+--\s+([0-9.]+)\s+", result.stdout, re.MULTILINE))
        logger.info(f"Found {len(existing_blocked_ips)} existing DROP rules in iptables. Optimizing restore.")
        use_optimized_check = True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.warning(f"Could not list existing iptables rules. Falling back to slower, per-IP checks. Error: {e}")

    restored_count = 0
    cutoff_time = datetime.now() - timedelta(hours=UNBAN_HOURS)
    
    with open(BLOCKED_JSON, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line)
                ip = entry.get('ip')
                blocked_at_str = entry.get('blocked_at')
                
                if not ip: continue

                if is_whitelisted(ip):
                    logger.info(f"IP {ip} is now whitelisted, not restoring block.")
                    continue

                # Check expiration
                if blocked_at_str:
                    blocked_at = datetime.fromisoformat(blocked_at_str)
                    if blocked_at < cutoff_time:
                        continue # Skip expired blocks
                    
                    with banned_ips_lock:
                        banned_ips[ip] = blocked_at

                # Check if rule already exists. Use optimized path if available.
                already_blocked = (use_optimized_check and ip in existing_blocked_ips) or \
                                  (not use_optimized_check and subprocess.run(['iptables', '-C', 'INPUT', '-s', ip, '-j', 'DROP'], capture_output=True).returncode == 0)

                if not already_blocked:
                    subprocess.run(['iptables', '-I', 'INPUT', '1', '-s', ip, '-j', 'DROP'], check=True)
                    logger.info(f"Restored block for IP: {ip}")
                    restored_count += 1
            except json.JSONDecodeError:
                logger.warning(f"Skipping malformed line in {BLOCKED_JSON}: {line.strip()}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error(f"Failed to restore block for {ip}. 'iptables' command failed.")
            except Exception:
                pass # Skip entries with bad timestamps or other issues
    
    logger.info(f"Finished restoring IPs. Total restored: {restored_count}")

def main():
    tailer = LogTailer(LOG_FILE)
    rate_limiter = SlidingWindow(MAX_FAILS, WINDOW_MINUTES)
    
    restore_blocked_ips()
    
    # Global attack detection setup
    GLOBAL_WINDOW = timedelta(minutes=GLOBAL_WINDOW_MINUTES)
    global_fails_tracker = deque()
    distributed_attack_alert_sent = False
    
    logger.info("The L0gVigil started. Monitoring for threats. Ctrl+C to stop.")
    
    while True:
        try:
            lines = tailer.read_lines()
            now = datetime.now()

            for line in lines:
                parsed = parse_line(line)
                if parsed:
                    ip, user, port, event_type = parsed
                    if event_type == 'fail':
                        global_fails_tracker.append(now) # Log for global detection
                        if not is_whitelisted(ip) and rate_limiter.add_attempt(ip):
                            logger.info(f"Threshold breached for {ip}. Offloading to worker thread.")
                            threading.Thread(target=process_attack, args=(ip, user, port)).start()
            
            # Prune and check global tracker
            while global_fails_tracker and now - global_fails_tracker[0] > GLOBAL_WINDOW:
                global_fails_tracker.popleft()
            
            if len(global_fails_tracker) > GLOBAL_MAX_FAILS and not distributed_attack_alert_sent:
                logger.warning(f"DISTRIBUTED ATTACK? Global fails ({len(global_fails_tracker)}) exceeded threshold of {GLOBAL_MAX_FAILS}.")
                msg = f"⚠️ <b>Potential Distributed Attack!</b>\n\nGlobal failed logins exceeded {GLOBAL_MAX_FAILS} in {GLOBAL_WINDOW_MINUTES} mins."
                threading.Thread(target=send_telegram, args=(msg,)).start()
                distributed_attack_alert_sent = True
            elif distributed_attack_alert_sent and len(global_fails_tracker) < (GLOBAL_MAX_FAILS / 2):
                logger.info("Global attack rate has subsided.")
                distributed_attack_alert_sent = False

            rate_limiter.cleanup()
            cleanup_banned_ips() # Check for expired bans
            time.sleep(0.1)  # Low CPU
            
        except KeyboardInterrupt:
            logger.info("Stopping The Watcher.")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Run with sudo!")
        exit(1)
    main()
