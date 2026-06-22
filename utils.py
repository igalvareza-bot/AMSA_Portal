import sqlite3

DB = "amsa.db"

def log_action(usuario, accion, detalle):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        INSERT INTO logs (fecha, usuario, accion, detalle)
        VALUES (datetime('now','localtime'),?,?,?)
    """, (usuario, accion, detalle))
    conn.commit()
    conn.close()
