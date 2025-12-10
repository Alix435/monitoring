from datetime import datetime

import threading
import platform
import subprocess
import re
import concurrent.futures

from core.database import Database

db = Database()
class IPMonitor:
    def __init__(self):
        self.ip_addresses = []
        self.lock = threading.Lock()
        self.append_ip()

    def ping_ip(self, ip_info):
        try:
            ip = ip_info['ip']
            if platform.system().lower() == "windows":
                command = ["ping", "-n", "2", "-w", "2000", ip]
            else:
                command = ["ping", "-c", "2", "-W", "2", ip]

            result = subprocess.run(command, capture_output=True, text=True, timeout=5)

            now = datetime.now().strftime("%H:%M:%S")
            if result.returncode == 0:
                time_match = re.search(r'time=([\d.]+)\s*ms', result.stdout)
                if not time_match and platform.system().lower() == "windows":
                    time_match = re.search(r'Average = (\d+)ms', result.stdout)

                response_time = float(time_match.group(1)) if time_match else 0

                ip_info['status'] = True
                ip_info['response_time'] = round(response_time, 2)
                ip_info['last_check'] = now
            else:
                ip_info['status'] = False
                ip_info['response_time'] = 0
                ip_info['last_check'] = now

        except Exception as e:
            ip_info['status'] = False
            ip_info['response_time'] = 0
            ip_info['last_check'] = datetime.now().strftime("%H:%M:%S")

        return ip_info


    def append_ip(self):
        printers = db.read_tables()
        if not printers:
            print("ℹ️ БД пустая. Добавьте принтеры через интерфейс.")
            self.ip_addresses = []
            return
        else:
            for printer in printers:
                tmp = {
                    'id': printer[0],
                    'name': printer[1],
                    'ip': printer[2],
                    'model': printer[3],
                    'location': printer[4],
                    'status': False,
                    'response_time': 0,
                    'last_check': ""
                }
                self.ip_addresses.append(tmp)


    def check_all_ips(self):
        with self.lock:
            targets = self.ip_addresses.copy()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(self.ping_ip, targets))

        with self.lock:
            self.ip_addresses = results

        return results

    def get_status(self):
        with self.lock:
            return self.ip_addresses.copy()
