def create_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS printers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ip_address TEXT NOT NULL UNIQUE,
            model TEXT,
            location TEXT
        )
        ''')


def read_db():
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute('SELECT id, name, ip_address, model, location FROM printers')
        printers = cur.fetchall()
        con.close()
        return printers
    except Exception as e:
        print(f"[ERROR] {e}")
        return []


def add_printers(printers_list):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    for printer in printers_list:
        name, ip_address, model, location = printer

        if printer_exists(ip_address):
            continue

        cur.execute('''
                INSERT INTO printers (name, ip_address, model, location)
                VALUES (?, ?, ?, ?)
            ''', (name, ip_address, model, location))

    con.commit()
    con.close()


def add_printer(data):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO printers (name, ip_address, model, location) VALUES (?, ?, ?, ?)",
        (data['name'], data['ip'], data['model'], data['location'])
    )
    new_id = cur.lastrowid  # ← это реальный id из БД
    con.commit()
    con.close()
    return new_id


def printer_exists(ip_address):
    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.execute('SELECT id, name FROM printers WHERE ip_address = ?', (ip_address,))
    result = cur.fetchone()

    con.close()
    return result is not None


def update_database(data, printer_id):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(
        'UPDATE printers SET name = ?, ip_address = ?, model = ?, location = ? WHERE id = ?',
        (data['name'], data['ip'], data['model'], data['location'], printer_id)
    )
    if cur.rowcount == 0:
        con.close()
        return False
    else:
        con.commit()
        con.close()
        return True


def delete_printer(printer_id):
    try:
        print(printer_id)
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute('DELETE FROM printers WHERE id = ?', (printer_id,))
        deleted = cur.rowcount
        con.commit()
        con.close()
        return deleted > 0  # True только если что-то удалено
    except Exception as e:
        print("Ошибка удаления:", e)
        return False


def command_center():
    # create_db()
    # add_printer()
    read_db()

if __name__ == "__main__":
    command_center()
