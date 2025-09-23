# app.py
from flask import Flask, render_template, jsonify
import subprocess
import platform
import datetime
import time
import threading
import concurrent.futures
import re

app = Flask(__name__)


class IPMonitor:
    def __init__(self):
        # Список IP-адресов для мониторинга
        self.ip_addresses = []
        self.append_ip()
        self.system_info = self.get_system_info()


    def append_ip(self):
        file_name = 'ip_print.txt'
        name = ['ip', 'name', 'status', 'response_time']

        with open(file_name, 'r') as file:
            for line in file:  # Читаем файл построчно без readlines()
                if line.strip():  # Пропускаем пустые строки
                    tmp = {
                        name[0]: line.split()[0],
                        name[1]: line.split()[1],
                        name[2]: False,
                        name[3]: 0
                    }
                    self.ip_addresses.append(tmp)


    def get_system_info(self):
        """Получение информации о системе"""
        system = platform.system()
        release = platform.release()
        version = platform.version()
        machine = platform.machine()
        processor = platform.processor()

        return {
            'system': system,
            'release': release,
            'version': version,
            'machine': machine,
            'processor': processor,
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


    def ping_ip(self, ip_info):
        """Пинг IP-адреса с использованием subprocess"""
        try:
            # Определяем команду ping в зависимости от ОС
            if platform.system().lower() == "windows":
                command = ["ping", "-n", "2", "-w", "2000", ip_info['ip']]
            else:
                command = ["ping", "-c", "2", "-W", "2", ip_info['ip']]

            # Выполняем ping
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5
            )

            # Анализируем результат
            if result.returncode == 0:
                # Парсим время ответа
                time_match = None
                if platform.system().lower() == "windows":
                    time_match = re.search(r'Average = (\d+)ms', result.stdout)
                else:
                    time_match = re.search(r'time=([\d.]+)\s*ms', result.stdout)

                response_time = 0
                if time_match:
                    response_time = float(time_match.group(1))

                ip_info['status'] = True
                ip_info['response_time'] = round(response_time, 2)
                ip_info['last_check'] = datetime.datetime.now().strftime("%H:%M:%S")
            else:
                ip_info['status'] = False
                ip_info['response_time'] = 0
                ip_info['last_check'] = datetime.datetime.now().strftime("%H:%M:%S")

        except subprocess.TimeoutExpired:
            ip_info['status'] = False
            ip_info['response_time'] = 0
            ip_info['last_check'] = datetime.datetime.now().strftime("%H:%M:%S")
        except Exception as e:
            ip_info['status'] = False
            ip_info['response_time'] = 0
            ip_info['last_check'] = datetime.datetime.now().strftime("%H:%M:%S")
            ip_info['error'] = str(e)

        return ip_info


    def check_all_ips(self):
        """Проверка всех IP-адресов с использованием многопоточности"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(self.ping_ip, self.ip_addresses))

        self.ip_addresses = results
        return results


    def get_network_info(self):
        """Получение базовой сетевой информации"""
        try:
            # Получаем IP хоста
            hostname = platform.node()

            # Получаем сетевые интерфейсы (простая версия)
            if platform.system().lower() == "windows":
                ipconfig = subprocess.run(["ipconfig"], capture_output=True, text=True)
                network_info = ipconfig.stdout[:500]  # Первые 500 символов
            else:
                ifconfig = subprocess.run(["ifconfig"], capture_output=True, text=True)
                network_info = ifconfig.stdout[:500] if ifconfig.returncode == 0 else "Не удалось получить ifconfig"

            return {
                'hostname': hostname,
                'network_info': network_info,
                'check_time': datetime.datetime.now().strftime("%H:%M:%S")
            }
        except:
            return {
                'hostname': platform.node(),
                'network_info': 'Ошибка получения сетевой информации',
                'check_time': datetime.datetime.now().strftime("%H:%M:%S")
            }


monitor = IPMonitor()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/ip-status')
def get_ip_status():
    ip_status = monitor.check_all_ips()
    system_info = monitor.get_system_info()
    network_info = monitor.get_network_info()

    return jsonify({
        'ip_status': ip_status,
        'system_info': system_info,
        'network_info': network_info,
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route('/api/system-info')
def get_system_info():
    return jsonify(monitor.get_system_info())


def background_monitor():
    """Фоновая задача для мониторинга IP"""
    while True:
        monitor.check_all_ips()
        time.sleep(30)  # Проверка каждые 30 секунд


if __name__ == '__main__':
    # Запускаем фоновый мониторинг
    thread = threading.Thread(target=background_monitor, daemon=True)
    thread.start()

    # Первоначальная проверка
    monitor.check_all_ips()

    app.run(debug=True, host='127.0.0.1', port=5000)

