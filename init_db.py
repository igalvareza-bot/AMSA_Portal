import sqlite3
import bcrypt

DB = "amsa.db"

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

conn = sqlite3.connect(DB)
cur = conn.cursor()

# USERS
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

# LOGS
cur.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    usuario TEXT,
    accion TEXT,
    detalle TEXT
)
""")

# TABLA "form" - fuente de verdad
cur.execute("""
CREATE TABLE IF NOT EXISTS form (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    usuario TEXT,
    ritm TEXT,
    tipo_equipo TEXT,
    marca TEXT,
    modelo TEXT,
    serie TEXT,
    hostname TEXT,
    asset TEXT,
    estado TEXT,
    ubicacion TEXT,
    observaciones TEXT
)
""")

# Mantener tabla legacy si existe para migración manual
cur.execute("""
CREATE TABLE IF NOT EXISTS formularios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    usuario TEXT,
    ritm TEXT,
    tipo TEXT,
    marca TEXT,
    modelo TEXT,
    serie TEXT,
    hostname TEXT,
    asset TEXT,
    estado TEXT,
    ubicacion TEXT,
    observaciones TEXT
)
""")

# Insert admin si no existe (password '1234' hasheada)
cur.execute("SELECT id FROM users WHERE username='admin'")
if not cur.fetchone():
    cur.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)",
                ("admin", hash_pw("1234"), "admin"))

conn.commit()
conn.close()

print("DB READY OK")
