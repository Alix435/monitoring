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


# printer_model_hint TEXT UNIQUE изза него не работает корректно
        self.conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS cartridges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_code TEXT,
                color_name TEXT NOT NULL,
                quantity INTEGER DEFAULT NULL,
                is_color BOOLEAN NOT NULL,
                printer_model_hint TEXT UNIQUE
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

    # def add_printer(self, data):
    #     cur = self.conn.execute(
    #         "INSERT INTO printers (name, ip_address, model, location) VALUES (?, ?, ?, ?)",
    #         (data['name'], data['ip'], data['model'], data['location'])
    #     )
    #     self.conn.commit()
    #     return cur.lastrowid
    #
    # def add_cartridge(self, data):
    #     self.conn.execute(
    #         "INSERT INTO cartridges (model, is_color) VALUES (?, ?)",
    #         (data['model'], data['color'])
    #     )
    #     self.conn.commit()

    def add_printer_with_cartridges(self, printer_data, cartridges_data):
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

            list_color = ['black', 'cyan', 'magenta', 'yellow']

            if cartridges_data['color']:
                for i in range(len(list_color)):
                    self.conn.execute("""
                                    INSERT INTO cartridges (color_name, is_color, printer_model_hint)
                                    VALUES (?, ?, ?)
                                """, (
                        list_color[i],
                        cartridges_data['color'],
                        cartridges_data.get('model')
                    ))
            else:
                self.conn.execute("""
                                INSERT INTO cartridges (color_name, is_color, printer_model_hint)
                                VALUES (?, ?, ?)
                            """, (
                    list_color[0],
                    cartridges_data['color'],
                    cartridges_data.get('model')
                ))


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


# def create_db():
#     con = sqlite3.connect(db_path)
#     cur = con.cursor()
#
#     cur.execute(
#         '''
#         CREATE TABLE IF NOT EXISTS printers (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT NOT NULL,
#             ip_address TEXT NOT NULL UNIQUE,
#             model TEXT,
#             location TEXT
#         )
#         ''')
#
#     cur.execute(
#         '''
#         CREATE TABLE IF NOT EXISTS cartridges (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             model TEXT NOT NULL,
#             is_color BOOLEAN NOT NULL,
#             number_black TEXT DEFAULT NULL,
#             black_qty INT DEFAULT 0,
#             number_cyan TEXT DEFAULT NULL,
#             cyan_qty INT DEFAULT NULL,
#             number_magenta TEXT DEFAULT NULL,
#             magenta_qty INT DEFAULT NULL,
#             number_yellow TEXT DEFAULT NULL,
#             yellow_qty INT DEFAULT NULL
#         )
#         ''')
#
#     con.commit()
#     con.close()
#
#
# def read_db():
#     try:
#         con = sqlite3.connect(db_path)
#         cur = con.cursor()
#         cur.execute('SELECT id, name, ip_address, model, location FROM printers')
#         printers = cur.fetchall()
#         con.close()
#         return printers
#     except Exception as e:
#         print(f"[ERROR] {e}")
#         return []
#
#
# def add_printers(printers_list):
#     con = sqlite3.connect(db_path)
#     cur = con.cursor()
#     for printer in printers_list:
#         name, ip_address, model, location = printer
#
#         if printer_exists(ip_address):
#             continue
#
#         cur.execute('''
#                 INSERT INTO printers (name, ip_address, model, location)
#                 VALUES (?, ?, ?, ?)
#             ''', (name, ip_address, model, location))
#
#     con.commit()
#     con.close()
#
#
# def add_printer(name_tab, data):
#     con = sqlite3.connect(db_path)
#     cur = con.cursor()
#     if name_tab == 'printers':
#         cur.execute(
#             f"INSERT INTO {name_tab} (name, ip_address, model, location) VALUES (?, ?, ?, ?)",
#             (data['name'], data['ip'], data['model'], data['location'])
#         )
#     elif name_tab == 'cartridges':
#         cur.execute(
#             f"INSERT INTO {name_tab} (model, is_color) VALUES (?, ?)",
#             (data['model'], data['color'])
#         )
#     new_id = cur.lastrowid  # ← это реальный id из БД
#     con.commit()
#     con.close()
#     return new_id
#
#
#
#
# def update_database(printer_id, data):
#     con = sqlite3.connect(db_path)
#     cur = con.cursor()
#     cur.execute(
#         'UPDATE printers SET name = ?, ip_address = ?, model = ?, location = ? WHERE id = ?',
#         (data['name'], data['ip'], data['model'], data['location'], printer_id)
#     )
#     if cur.rowcount == 0:
#         con.close()
#         return False
#     else:
#         con.commit()
#         con.close()
#         return True
#
#
# def delete_printer(printer_id):
#     try:
#         print(printer_id)
#         con = sqlite3.connect(db_path)
#         cur = con.cursor()
#         cur.execute('DELETE FROM printers WHERE id = ?', (printer_id,))
#         deleted = cur.rowcount
#         con.commit()
#         con.close()
#         return deleted > 0  # True только если что-то удалено
#     except Exception as e:
#         print("Ошибка удаления:", e)
#         return False
#
#
# def printer_exists(ip_address):
#     con = sqlite3.connect(db_path)
#     cur = con.cursor()
#
#     cur.execute('SELECT id, name FROM printers WHERE ip_address = ?', (ip_address,))
#     result = cur.fetchone()
#
#     con.close()
#     return result is not None
#
#
# def command_center():
#     create_db()
#     # add_printer()
#     read_db()
#
#
# if __name__ == "__main__":
#     command_center()
