import sqlite3
import pandas as pd

DB = "amsa.db"

def conn():
    return sqlite3.connect(DB)

# =========================
# LOG AUDITORIA
# =========================
def log(user, action, detail=""):
    c = conn()
    cur = c.cursor()
    cur.execute("""
        INSERT INTO logs (fecha, usuario, accion, detalle)
        VALUES (datetime('now'),?,?,?)
    """, (user, action, detail))
    c.commit()
    c.close()

# =========================
# EXPORT EXCEL
# =========================
def export_excel():
    c = conn()
    df = pd.read_sql_query("SELECT * FROM form ORDER BY id DESC", c)
    file = "export_amsa.xlsx"
    df.to_excel(file, index=False)
    c.close()
    return file
