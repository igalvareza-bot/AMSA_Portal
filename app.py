import streamlit as st
import sqlite3
import bcrypt
import pandas as pd
from pdf_generator import generar_pdf
from catalogo import obtener_catalogo
from utils import log_action
from init_db import init_db  # inicializador de la DB

# Inicializar DB al arrancar
init_db()

DB = "amsa.db"

# ------------------ FUNCIONES AUXILIARES ------------------

def check_login(user, pw):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, username, password, role FROM users WHERE username=?", (user,))
    res = c.fetchone()
    conn.close()
    if res and bcrypt.checkpw(pw.encode(), res[2].encode()):
        return {"id": res[0], "username": res[1], "role": res[3]}
    return None

def insert_form(data, usuario):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        INSERT INTO form (fecha, usuario, ritm, tipo_equipo, marca, modelo, serie,
                          hostname, asset, estado, ubicacion, observaciones)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data["fecha"], usuario, data["ritm"], data["tipo_equipo"], data["marca"],
        data["modelo"], data["serie"], data["hostname"], data["asset"],
        data["estado"], data["ubicacion"], data["observaciones"]
    ))
    conn.commit()
    conn.close()
    log_action(usuario, "CREAR", f"Formulario creado: {data['ritm']}")

def get_forms():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM form ORDER BY fecha DESC", conn)
    conn.close()
    return df

# ------------------ UI ------------------

def login_ui():
    st.title("Portal AMSA ABM")
    user = st.text_input("Usuario")
    pw = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        res = check_login(user, pw)
        if res:
            st.session_state["user"] = res
            st.experimental_rerun()
        else:
            st.error("Credenciales inválidas")

def crear_abm_ui():
    st.header("Crear ABM")
    data = {}
    data["fecha"] = st.date_input("Fecha").strftime("%Y-%m-%d")
    data["ritm"] = st.text_input("RITM")
    data["tipo_equipo"] = st.selectbox("Tipo de equipo", ["Notebook", "Desktop", "Servidor"])
    data["marca"] = st.selectbox("Marca", obtener_catalogo("marca"))
    data["modelo"] = st.text_input("Modelo")
    data["serie"] = st.text_input("Serie")
    data["hostname"] = st.text_input("Hostname")
    data["asset"] = st.text_input("Asset")
    data["estado"] = st.selectbox("Estado", ["Asignado", "Disponible", "En reparación"])
    data["ubicacion"] = st.text_input("Ubicación")
    data["observaciones"] = st.text_area("Observaciones")

    if st.button("Guardar"):
        insert_form(data, st.session_state["user"]["username"])
        st.success("Formulario guardado correctamente")

def historial_ui():
    st.header("Historial de Formularios")
    df = get_forms()
    st.dataframe(df)
    if not df.empty:
        id_sel = st.selectbox("Seleccionar ID para exportar PDF", df["id"])
        if st.button("Exportar PDF"):
            generar_pdf(id_sel)
            st.success("PDF generado correctamente")

def config_ui():
    st.header("Configuración")
    st.write("Opciones de idioma, colores corporativos, etc. (pendiente)")

def main_menu():
    st.sidebar.title("Menú")
    choice = st.sidebar.radio("Navegación", ["Crear ABM", "Historial", "Exportar PDF", "Configuración", "Salir"])
    if choice == "Crear ABM":
        crear_abm_ui()
    elif choice == "Historial":
        historial_ui()
    elif choice == "Exportar PDF":
        historial_ui()
    elif choice == "Configuración":
        config_ui()
    elif choice == "Salir":
        st.session_state.clear()
        st.experimental_rerun()

# ------------------ MAIN ------------------

if "user" not in st.session_state:
    login_ui()
else:
    main_menu()
