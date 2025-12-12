import sqlite3
from config import db_path


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()


    def _create_tables(self):
        self.conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS printers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ip_address TEXT NOT NULL UNIQUE,
                model TEXT,
                location TEXT
            )
            ''')

        self.conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS cartridges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_code TEXT,
            color_name TEXT NOT NULL CHECK(color_name IN ('black', 'cyan', 'magenta', 'yellow')),
            quantity INTEGER DEFAULT NULL,
            is_color BOOLEAN NOT NULL,
            printer_model TEXT NOT NULL,
            UNIQUE(printer_model, color_name)  -- ← КЛЮЧЕВОЕ: запрет дублей по модели+цвету
    )
            ''')

        self.conn.commit()


    def read_tables(self):
        try:
            cur = self.conn.execute('SELECT id, name, ip_address, model, location FROM printers')
            printers = cur.fetchall()
            return printers
        except Exception as e:
            print(f"[ERROR] {e}")
            return []


    def read_tab_print(self):
        cur = self.conn.execute('SELECT DISTINCT model FROM printers')
        return [row[0] for row in cur.fetchall()]


    def read_tab_cart(self):
        cur = self.conn.execute('SELECT * FROM cartridges')
        print(cur.fetchall())


    def add_printer(self, printer_data):
        with self.conn:
            cur = self.conn.execute("""
                INSERT INTO printers (name, ip_address, model, location)
                VALUES (?, ?, ?, ?)
            """, (
                printer_data['name'],
                printer_data['ip'],
                printer_data['model'],
                printer_data['location']
            ))
            printer_id = cur.lastrowid
            return printer_id


    def update_printer(self, printer_id, data):
        self.conn.execute('''
            UPDATE printers
            SET name = ?, ip = ?, model = ?, location = ?, color = ?
            WHERE id = ?
        ''', (data['name'], data['ip'], data['model'], data['location'], printer_id))
        self.conn.commit()


    def delete_printer(self, printer_id):
        with self.conn:
            cur = self.conn.execute('DELETE FROM printers WHERE id = ?', (printer_id,))
            return cur.rowcount > 0


    def close(self):
        self.conn.close()
