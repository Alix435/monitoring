from flask import Flask, render_template, jsonify, request
from datetime import datetime

from core.database import Database
from core.monitor import IPMonitor

import time
import threading


app = Flask(__name__)

db = Database()
monitor = IPMonitor()

ERROR_IMAGE_PATH = 'static/img/error.png'
monitor = IPMonitor()

def background_monitor():
    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Проверка IP...")
            monitor.check_all_ips()
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(60)


@app.route('/')
def index():
    return render_template('index.html')

@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(error):
    return render_template('error.html', message="В серверной сейчас кого-то оттарабанят, и все заработает",
                           submessage="немного подождите ;)")

@app.route('/printers')
def printers_page():
    printers = monitor.get_status()
    return render_template('printers.html', printers=printers)


@app.route('/cartridges')
def cartridges_page():
    printer_list = db.read_tab_print()
    db.read_tab_cart()
    # return render_template('cartridges.html', printers=printer_list)


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


@app.route('/api/printers')
def api_printers():
    return jsonify(monitor.get_status())


@app.route('/api/printers', methods=['POST'])
def add_printer():
    try:
        data = request.get_json()
        required_print = ['name', 'ip', 'model', 'location']
        for field in required_print:
            if not data.get(field):
                return jsonify({'error': f'Поле "{field}" обязательно'}), 400


        printer_id= db.add_printer(
            printer_data={
                'name': data['name'],
                'ip': data['ip'],
                'model': data['model'],
                'location': data['location']
            }
        )
        new_printer = {
            'id': printer_id,
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

        threading.Thread(
            target=lambda: monitor.ping_ip(new_printer),
            daemon=True
        ).start()

        return jsonify({'id': printer_id, **new_printer}), 201

    except Exception as e:
        print("Ошибка добавления:", e)
        return jsonify({'error': 'Ошибка сервера'}), 500


@app.route('/api/printers/<int:printer_id>', methods=['PUT'])
def update_printer(printer_id):
    try:
        data = request.get_json()
        required = ['name', 'ip', 'model', 'location']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'Поле "{field}" обязательно'}), 400

        if not db.update_printer(printer_id, data):
            return jsonify({'error': 'Принтер не найден'}), 404

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


@app.route('/api/printers/<int:printer_id>', methods=['DELETE'])
def delete_printer(printer_id):
    try:

        if not db.delete_printer(printer_id):
            return jsonify({'error': f'Принтер ID={printer_id} не найден в БД'}), 404

        removed = False
        with monitor.lock:
            before = len(monitor.ip_addresses)
            monitor.ip_addresses = [
                p for p in monitor.ip_addresses
                if int(p['id']) != printer_id
            ]
            removed = len(monitor.ip_addresses) < before

        threading.Thread(
            target=monitor.check_all_ips,
            daemon=True
        ).start()

        print(f"🗑️ Удаление ID={printer_id}: из памяти {'удалён' if removed else 'не найден'}")

        return jsonify({'success': True})
    except Exception as e:
        print("❌ Ошибка удаления:", e)
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    monitor.check_all_ips()

    thread = threading.Thread(target=background_monitor, daemon=True)
    thread.start()

    app.run(host='0.0.0.0', port=5000)
