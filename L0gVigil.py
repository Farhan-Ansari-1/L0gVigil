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

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load configuration
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    LOG_FILE = config['LOG_FILE']
    TELEGRAM_TOKEN = config['TELEGRAM_TOKEN']
    TELEGRAM_CHAT_ID = config['TELEGRAM_CHAT_ID']
    IPINFO_TOKEN = config['IPINFO_TOKEN']
    WHITELIST = config['WHITELIST']
    MAX_FAILS = config['MAX_FAILS']
    WINDOW_MINUTES = config['WINDOW_MINUTES']
    GLOBAL_MAX_FAILS = config['GLOBAL_MAX_FAILS']
    GLOBAL_WINDOW_MINUTES = config['GLOBAL_WINDOW_MINUTES']
    UNBAN_HOURS = config['UNBAN_HOURS']
    BLOCKED_JSON = config['BLOCKED_JSON']
except Exception as e:
    logger.error(f"Config Load Error: {e}")
    exit(1)

file_lock = threading.Lock()
banned_ips = {} 
banned_ips_lock = threading.Lock()

class SlidingWindow:
    def __init__(self, max_fails, window_minutes):
        self.max_fails = max_fails
        self.window = timedelta(minutes=window_minutes)
        self.counts = {}
        self.lock = threading.Lock()

    def add_attempt(self, ip):
        now = datetime.now()
        with self.lock:
            if ip not in self.counts: self.counts[ip] = deque()
            self.counts[ip] = deque([ts for ts in self.counts[ip] if now - ts < self.window])
            self.counts[ip].append(now)
            return len(self.counts[ip]) >= self.max_fails

    def cleanup(self):
        now = datetime.now()
        with self.lock:
            to_remove = [ip for ip, deq in self.counts.items() if not deq or now - deq[0] > self.window]
            for ip in to_remove: del self.counts[ip]

class LogTailer:
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

    def read_lines(self):
        if not self.file: self._open_file(); return []
        self.file.seek(self.position)
        lines = self.file.readlines()
        if lines: self.position = self.file.tell()
        return [line.rstrip() for line in lines]

def is_whitelisted(ip):
    try:
        client_ip = ipaddress.ip_address(ip)
        for wl_entry in WHITELIST:
            if '/' in wl_entry:
                if client_ip in ipaddress.ip_network(wl_entry, strict=False): return True
            elif client_ip == ipaddress.ip_address(wl_entry): return True
    except: return False
    return False

def unban_ip(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        cmd = 'ip6tables' if isinstance(ip_obj, ipaddress.IPv6Address) else 'iptables'
        subprocess.run([cmd, '-D', 'INPUT', '-s', ip, '-j', 'DROP'], check=True)
        logger.info(f"UNBANNED IP: {ip}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to unban {ip}: {e}")
        return False

def block_ip(ip):
    try:
        now = datetime.now() # Fix: added variable
        ip_obj = ipaddress.ip_address(ip)
        cmd = 'ip6tables' if isinstance(ip_obj, ipaddress.IPv6Address) else 'iptables'
        
        subprocess.run([cmd, '-I', 'INPUT', '1', '-s', ip, '-j', 'DROP'], check=True)
        logger.warning(f"BLOCKED IP: {ip} ({cmd})")

        with banned_ips_lock:
            banned_ips[ip] = now
            
        log_entry = {'ip': ip, 'blocked_at': now.isoformat(), 'reason': 'brute force'}
        with file_lock:
            with open(BLOCKED_JSON, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        return True
    except Exception as e:
        logger.error(f"Failed to block {ip}: {e}")
        return False

def cleanup_banned_ips():
    now = datetime.now()
    with banned_ips_lock:
        for ip in list(banned_ips.keys()):
            if now - banned_ips[ip] > timedelta(hours=UNBAN_HOURS):
                if unban_ip(ip):
                    del banned_ips[ip]

def get_geo(ip):
    try:
        url = f"https://ipinfo.io/{ip}/json"
        headers = {} if IPINFO_TOKEN == 'FREE' else {'Authorization': f'Bearer {IPINFO_TOKEN}'}
        r = requests.get(url, headers=headers, timeout=3)
        data = r.json()
        city = data.get('city', 'N/A')
        return f"{city}, {data.get('country', 'N/A')} | ISP: {data.get('org', 'N/A')}"
    except: return "Geo unavailable"

def send_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={'chat_id': TELEGRAM_CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}, timeout=5)
    except: logger.error("Telegram alert failed")

def parse_line(line):
    patterns = [
        r"Failed password for(?: invalid user)? (\w+) from ((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|([\da-fA-F:]+)) port (\d+)",
        r"Invalid user (\w+) from ((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|([\da-fA-F:]+)) port (\d+)",
        r"Accepted password for (\w+) from ((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|([\da-fA-F:]+)) port (\d+)"
    ]
    for pat in patterns:
        match = re.search(pat, line)
        if match:
            return match.group(2), match.group(1), match.group(5), 'success' if 'Accepted' in line else 'fail'
    return None

def process_attack(ip, user, port):
    geo = get_geo(ip)
    msg = f"🚨 <b>BRUTE FORCE!</b>\nIP: {ip}\nUser: {user}\nGeo: {geo}"
    send_telegram(msg)
    block_ip(ip)

def restore_blocked_ips():
    if not os.path.exists(BLOCKED_JSON): return
    logger.info("Restoring blocks from JSON...")
    with open(BLOCKED_JSON, 'r') as f:
        for line in f:
        
            try:
                ip = json.loads(line)['ip']
                if not is_whitelisted(ip):
                    # Check if the IP is already banned
                    with banned_ips_lock:
                        if ip not in banned_ips:
                            ip_obj = ipaddress.ip_address(ip)
                            cmd = 'ip6tables' if isinstance(ip_obj, ipaddress.IPv6Address) else 'iptables'
                            subprocess.run([cmd, '-I', 'INPUT', '1', '-s', ip, '-j', 'DROP'], stderr=subprocess.DEVNULL)
                            banned_ips[ip] = datetime.now()  # Mark as banned in memory
                            logger.info(f"Restored block for IP: {ip}")
            except Exception as e:
                logger.error(f"Failed to restore block for IP: {ip} - {e}")
                continue

# ... Restore function logic included in main or defined separately ...

def main():
    tailer = LogTailer(LOG_FILE)
    rate_limiter = SlidingWindow(MAX_FAILS, WINDOW_MINUTES)
    global_fails_tracker = deque()
    
    logger.info("L0gVigil Started. Monitoring...")

    restore_blocked_ips()
    
    while True:
        try:
            lines = tailer.read_lines()
            now = datetime.now()
            for line in lines:
                parsed = parse_line(line)
                if parsed:
                    ip, user, port, event_type = parsed
                    if event_type == 'fail':
                        global_fails_tracker.append(now)
                        if not is_whitelisted(ip) and rate_limiter.add_attempt(ip):
                            threading.Thread(target=process_attack, args=(ip, user, port)).start()
            
            # Pruning global tracker
            while global_fails_tracker and now - global_fails_tracker[0] > timedelta(minutes=GLOBAL_WINDOW_MINUTES):
                global_fails_tracker.popleft()
            
            rate_limiter.cleanup()
            cleanup_banned_ips()
            time.sleep(0.5)
        except KeyboardInterrupt: break
        except Exception as e: logger.error(f"Error: {e}"); time.sleep(5)

if __name__ == "__main__":
    if os.geteuid() != 0: exit("Run with sudo!")
    main()