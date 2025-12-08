from flask import Flask, render_template, jsonify, request
from datetime import datetime

import subprocess
import platform
import re
import concurrent.futures
import time
import threading

import database

app = Flask(__name__)

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
            # ip_info['error'] = str(e)  # опционально

        return ip_info

    def append_ip(self):
        printers = database.read_db()
        for printer in printers:
            # Предполагаем: (id, name, ip, model, location)
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


monitor = IPMonitor()


@app.route('/')
def index():
    printers = monitor.get_status()
    return render_template('index.html', printers=printers)


def background_monitor():
    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Проверка IP...")
            monitor.check_all_ips()
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(30)


@app.route('/api/status')
def api_status():
    printers = monitor.get_status()
    return jsonify([
        {
            'id': p['id'],
            'status': p['status'],
            'response_time': p['response_time'],
            'last_check': p['last_check']
        }
        for p in printers
    ])

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# GET /api/printers — получение списка (альтернатива monitor.get_status())
@app.route('/api/printers')
def api_printers():
    return jsonify(monitor.get_status())

# POST /api/printers — добавить принтер
@app.route('/api/printers', methods=['POST'])
def add_printer():
    try:
        data = request.get_json()
        # Валидация
        required = ['name', 'ip', 'model', 'location']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'Поле "{field}" обязательно'}), 400

        new_id = database.add_printer(data)

        # Добавляем в мониторинг
        new_printer = {
            'id': new_id,
            'name': data['name'],
            'ip': data['ip'],
            'model': data['model'],
            'location': data['location'],
            'status': False,
            'response_time': 0,
            'last_check': ""
        }
        with monitor.lock:
            monitor.ip_addresses.append(new_printer)

        return jsonify({'id': new_id, **new_printer}), 201

    except Exception as e:
        print("Ошибка добавления:", e)
        return jsonify({'error': 'Ошибка сервера'}), 500

# PUT /api/printers/<int:printer_id> — обновить
@app.route('/api/printers/<int:printer_id>', methods=['PUT'])
def update_printer(printer_id):
    try:
        data = request.get_json()
        required = ['name', 'ip', 'model', 'location']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'Поле "{field}" обязательно'}), 400

        if not database.update_database(data, printer_id):
            return jsonify({'error': 'Принтер не найден'}), 404


        # Обновляем в памяти
        with monitor.lock:
            for p in monitor.ip_addresses:
                if p['id'] == printer_id:
                    p.update({
                        'name': data['name'],
                        'ip': data['ip'],
                        'model': data['model'],
                        'location': data['location']
                    })
                    break

        return jsonify({'success': True})

    except Exception as e:
        print("Ошибка обновления:", e)
        return jsonify({'error': 'Ошибка сервера'}), 500


# DELETE /api/printers/<int:printer_id> — удалить
@app.route('/api/printers/<int:printer_id>', methods=['DELETE'])
def delete_printer(printer_id):
    try:
        if not database.delete_printer(printer_id):
            return jsonify({'error': 'Принтер не найден'}), 404

        # Удаляем из памяти
        with monitor.lock:
            monitor.ip_addresses = [p for p in monitor.ip_addresses if p['id'] != printer_id]

        return jsonify({'success': True})

    except Exception as e:
        print("Ошибка удаления:", e)
        return jsonify({'error': 'Ошибка сервера'}), 500

if __name__ == "__main__":
    # Первый запуск
    monitor.check_all_ips()
    # Фоновый поток
    thread = threading.Thread(target=background_monitor, daemon=True)
    thread.start()

    app.run(host='0.0.0.0', port=5000)
