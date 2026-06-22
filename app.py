import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import bcrypt
from datetime import datetime
from pdf_generator import generar_pdf
from catalogo import CATALOGO
import utils
import os

DB = "amsa.db"

# ======================
# CONFIG INICIAL
# ======================
st.set_page_config(page_title="AMSA Portal Enterprise", layout="wide", page_icon="🛠️")

# Paletas y etiquetas (idioma)
PALETTES = {
    "AMSA (azul/naranja)": {"PRIMARY": "#003366", "ACCENT": "#FF8C00", "BG": "#F4F6FB", "CARD_BORDER": "#E5E7EB"},
    "Oscuro": {"PRIMARY": "#0b3d91", "ACCENT": "#ffb84d", "BG": "#0f1724", "CARD_BORDER": "#1f2937"},
    "Claro minimal": {"PRIMARY": "#0f172a", "ACCENT": "#2563eb", "BG": "#ffffff", "CARD_BORDER": "#e5e7eb"}
}

LABELS = {
    "Español": {
        "login_title": "AMSA Portal Enterprise",
        "usuario": "Usuario",
        "password": "Password",
        "ingresar": "Ingresar",
        "crear_abm": "Crear ABM",
        "historial": "Historial",
        "exportar": "Exportar PDF/Excel",
        "config": "Configuración",
        "salir": "Salir",
        "guardar": "Guardar",
        "nombre": "Nombre completo *",
        "ticket": "Ticket / WOT *",
        "ubicacion": "Ubicación *",
        "tipo_usuario": "Tipo Usuario",
        "otro": "OTRO",
        "tipo_activo": "Tipo de activo",
        "marca": "Marca",
        "modelo": "Modelo",
        "estado": "Estado",
        "estado_cargador": "Estado cargador",
        "accesorios": "Accesorios",
        "buscar": "Buscar",
        "asset": "Asset",
        "serie": "Serie",
        "ritm": "RITM / Ticket",
        "ingresar_enter_hint": "Presiona Enter para enviar"
    },
    "English": {
        "login_title": "AMSA Portal Enterprise",
        "usuario": "User",
        "password": "Password",
        "ingresar": "Sign in",
        "crear_abm": "Create ABM",
        "historial": "History",
        "exportar": "Export PDF/Excel",
        "config": "Settings",
        "salir": "Logout",
        "guardar": "Save",
        "nombre": "Full name *",
        "ticket": "Ticket / WOT *",
        "ubicacion": "Location *",
        "tipo_usuario": "User type",
        "otro": "OTHER",
        "tipo_activo": "Asset type",
        "marca": "Brand",
        "modelo": "Model",
        "estado": "State",
        "estado_cargador": "Charger state",
        "accesorios": "Accessories",
        "buscar": "Search",
        "asset": "Asset",
        "serie": "Serial",
        "ritm": "RITM / Ticket",
        "ingresar_enter_hint": "Press Enter to submit"
    }
}

# ======================
# UTILIDADES DB / RERUN
# ======================
def conn():
    return sqlite3.connect(DB, check_same_thread=False)

def safe_rerun():
    try:
        st.experimental_rerun()
        return
    except Exception:
        pass
    candidates = [
        "streamlit.runtime.scriptrunner.script_runner",
        "streamlit.runtime.scriptrunner",
        "streamlit.script_runner",
        "streamlit.scriptrunner.script_runner",
    ]
    for path in candidates:
        try:
            mod = __import__(path, fromlist=["RerunException"])
            RerunException = getattr(mod, "RerunException", None)
            if RerunException:
                raise RerunException()
        except Exception:
            continue
    st.stop()

# Reutilizable: asegurar key en session_state
def ensure_session_key(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

# select_with_other robusto
def select_with_other(label, options, key_base, other_label="OTRO"):
    """
    Muestra selectbox con opciones + OTRO. Si OTRO, muestra input manual persistente.
    Devuelve el valor final (string). Si OTRO seleccionado pero no escrito, devuelve "".
    """
    ensure_session_key(f"{key_base}__manual", "")
    opts = list(options) + [other_label]
    sel = st.selectbox(label, opts, key=f"{key_base}__select")
    if sel == other_label:
        manual = st.text_input(f"{label} (manual)", value=st.session_state.get(f"{key_base}__manual", ""), key=f"{key_base}__manual")
        st.session_state[f"{key_base}__manual"] = manual
        return manual.strip() if manual and manual.strip() else ""
    else:
        # limpiar manual previo si existía
        if st.session_state.get(f"{key_base}__manual"):
            st.session_state[f"{key_base}__manual"] = ""
        return sel

# multiselect_with_manual corregida para usar form_submit_button
def multiselect_with_manual(base_label, options, key_base):
    """
    Multiselect con posibilidad de agregar accesorios manuales múltiples dentro de un form.
    Usa st.form_submit_button para añadir manuales sin romper las reglas de forms.
    Devuelve lista combinada (seleccionados + manuales).
    """
    ensure_session_key(f"{key_base}__manuals", [])
    sel = st.multiselect(base_label, options, key=f"{key_base}__multiselect")

    st.markdown("**Accesorios manuales añadidos**")
    if st.session_state[f"{key_base}__manuals"]:
        st.write(", ".join(st.session_state[f"{key_base}__manuals"]))
        if st.checkbox("Limpiar accesorios manuales", key=f"{key_base}__clear_chk"):
            st.session_state[f"{key_base}__manuals"] = []

    manual_input_key = f"{key_base}__add_input"
    manual_text = st.text_input("Agregar accesorio manual (separar por coma para varios)", key=manual_input_key)

    # Usar form_submit_button para agregar manuales dentro del form
    add_clicked = st.form_submit_button("Agregar accesorios manuales", key=f"{key_base}__add_btn")
    if add_clicked:
        if manual_text and manual_text.strip():
            new_items = [a.strip() for a in manual_text.split(",") if a.strip()]
            st.session_state[f"{key_base}__manuals"].extend(new_items)
            # limpiar input
            st.session_state[manual_input_key] = ""
            st.success(f"Agregados: {', '.join(new_items)}")
        else:
            st.warning("Ingrese al menos un accesorio manual antes de agregar.")

    combined = sel + st.session_state[f"{key_base}__manuals"]
    return combined

# ======================
# SIDEBAR (Menú arriba, controles abajo)
# ======================
st.sidebar.title("AMSA Enterprise")

# Inicializar idioma en session_state si no existe
ensure_session_key("lang", "Español")

# Etiquetas L actuales
L = LABELS.get(st.session_state.lang, LABELS["Español"])

# Menú arriba (etiquetas en idioma actual)
menu = st.sidebar.radio("Menú", [
    L["crear_abm"],
    L["historial"],
    L["exportar"],
    L["config"],
    L["salir"]
], index=0, key="sidebar_menu")

st.sidebar.markdown("---")

# Controles de configuración debajo del menú
lang_choice = st.sidebar.selectbox("Idioma", ["Español", "English"], index=0 if st.session_state.lang == "Español" else 1, key="sidebar_lang")
if lang_choice != st.session_state.lang:
    st.session_state.lang = lang_choice
    safe_rerun()

color_scheme = st.sidebar.selectbox("Paleta corporativa", list(PALETTES.keys()), key="sidebar_palette")
theme = st.sidebar.selectbox("Tema", ["Claro", "Oscuro"], key="sidebar_theme")

st.sidebar.markdown("---")
st.sidebar.markdown("**Sesión local**")
if "user" in st.session_state:
    st.sidebar.markdown(f"<small style='color:gray'>Usuario: {st.session_state.get('user','—')} • Rol: {st.session_state.get('role','—')}</small>", unsafe_allow_html=True)
else:
    st.sidebar.markdown("<small style='color:gray'>Usuario: — • Rol: —</small>", unsafe_allow_html=True)

# Vista de paleta
st.sidebar.markdown("---")
st.sidebar.markdown("**Vista de paleta**")
palette = PALETTES.get(color_scheme, PALETTES["AMSA (azul/naranja)"])
PRIMARY = palette["PRIMARY"]; ACCENT = palette["ACCENT"]; BG = palette["BG"]; CARD_BORDER = palette["CARD_BORDER"]
st.sidebar.markdown(f"""
<div style="display:flex; gap:6px; align-items:center;">
  <div style="width:36px; height:36px; background:{PRIMARY}; border-radius:6px; border:1px solid #00000020"></div>
  <div style="width:36px; height:36px; background:{ACCENT}; border-radius:6px; border:1px solid #00000020"></div>
  <div style="width:36px; height:36px; background:{BG}; border-radius:6px; border:1px solid #00000020"></div>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Recalcular etiquetas L (por si cambió idioma)
L = LABELS.get(st.session_state.lang, LABELS["Español"])

# ======================
# CSS global dinámico
# ======================
st.markdown(f"""
<style>
:root {{
  --primary: {PRIMARY};
  --accent: {ACCENT};
  --bg: {BG};
  --card-border: {CARD_BORDER};
}}
body {{ background-color: var(--bg); }}
.login-box {{ background:white; padding:28px; border-radius:12px; width:420px; margin:auto; margin-top:60px; box-shadow:0px 10px 30px rgba(0,0,0,0.06); border:1px solid var(--card-border); }}
.login-title {{ color:var(--primary); font-weight:700; }}
.card {{ background:white; padding:15px; border-radius:10px; border:1px solid var(--card-border); }}
.header-accent {{ background: linear-gradient(90deg, var(--primary), var(--accent)); color: white; padding: 10px; border-radius: 8px; }}
.small-muted {{ color: #6b7280; font-size:12px; }}
</style>
""", unsafe_allow_html=True)

# ======================
# LOGIN
# ======================
def check_login(user, password):
    c = conn().cursor()
    c.execute("SELECT id, username, password, role FROM users WHERE username=?", (user,))
    row = c.fetchone()
    if not row:
        return None
    user_id, username, stored_pw, role = row
    try:
        if stored_pw and bcrypt.checkpw(password.encode(), stored_pw.encode()):
            return username, role
    except Exception:
        pass
    if stored_pw == password:
        new_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cur = conn().cursor()
        cur.execute("UPDATE users SET password=? WHERE id=?", (new_hash, user_id))
        conn().commit()
        return username, role
    return None

if "auth" not in st.session_state:
    st.session_state.auth = False

def login_ui():
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown(f"<h2 class='login-title'>{L['login_title']}</h2>", unsafe_allow_html=True)
    st.markdown("<hr/>", unsafe_allow_html=True)

    # Formulario de login: Enter dentro de este form dispara submit
    with st.form("login"):
        u = st.text_input(L["usuario"], key="login_user")
        p = st.text_input(L["password"], type="password", key="login_pass")
        btn = st.form_submit_button(L["ingresar"])

        # JS: Enter solo en este form dispara submit
        components.html("""
        <script>
        (function(){
          try {
            const forms = window.parent.document.querySelectorAll('form');
            if(!forms.length) return;
            const form = forms[forms.length-1];
            form.addEventListener('keydown', function(e){
              if(e.key === 'Enter'){
                const active = document.activeElement;
                if(!active) return;
                if(form.contains(active) && (active.type === 'text' || active.type === 'password')){
                  const submit = form.querySelector('button[type="submit"]');
                  if(submit){
                    submit.click();
                    e.preventDefault();
                  }
                }
              }
            });
          } catch(err) {
            // silent fail
          }
        })();
        </script>
        """, height=0)

    if btn:
        res = check_login(u, p)
        if res:
            st.session_state.auth = True
            st.session_state.user = res[0]
            st.session_state.role = res[1]
            try:
                utils.log(st.session_state.user, "LOGIN", "Ingreso exitoso")
            except Exception:
                pass
            safe_rerun()
        else:
            try:
                utils.log(u, "LOGIN_FAIL", "Credenciales inválidas")
            except Exception:
                pass
            st.error("Credenciales inválidas")

    st.markdown("</div>", unsafe_allow_html=True)

# ======================
# APP PRINCIPAL
# ======================
if not st.session_state.auth:
    login_ui()
    st.stop()

# Actualizar sidebar con usuario
st.sidebar.markdown(f"<small style='color:gray'>Usuario: {st.session_state.user} • Rol: {st.session_state.role}</small>", unsafe_allow_html=True)

# Header
st.markdown(f"<div class='header-accent'><h2 style='margin:6px 12px'>Formulario de Entrega / Retiro</h2></div>", unsafe_allow_html=True)

# ======================
# CREAR ABM
# ======================
if menu == L["crear_abm"]:
    st.write("Complete los datos del requerimiento. Los campos con * son obligatorios.")

    ensure_session_key("manual_accesorios", [])

    with st.form("abm", clear_on_submit=False):
        # INFORMACIÓN USUARIO
        st.subheader("Información Usuario")
        col1, col2, col3 = st.columns([3,3,2])

        with col1:
            nombre = st.text_input(L["nombre"], value="")
            rut = st.text_input("RUT", value="")
            correo = st.text_input("Correo", value="")
            cargo = st.text_input("Cargo", value="")
            empresa = st.text_input("Empresa", value="AMSA")
        with col2:
            ubicacion = st.text_input(L["ubicacion"], value="")
            ticket = st.text_input(L["ticket"], value="")
            tipo_usuario = select_with_other(L["tipo_usuario"], ["COLABORADOR", "CONTRATISTA"], "tipo_usuario", other_label=L["otro"])
            responsable = st.text_input("Responsable", value="AMSA")
        with col3:
            fecha = st.date_input("Fecha", value=datetime.now().date())
            hora = st.time_input("Hora", value=datetime.now().time())

        st.markdown("---")
        st.subheader("Datos de Entrega / Retiro")

        # Equipo principal (entrega)
        st.markdown("**Equipo principal**")
        col4, col5, col6 = st.columns([3,2,2])

        with col4:
            nombre_equipo = st.text_input("Nombre de equipo", value="")
            tipo_activo = select_with_other(L["tipo_activo"], ["Notebook", "Desktop", "Monitor", "Servidor"], "tipo_activo", other_label=L["otro"])
        with col5:
            marca = select_with_other(L["marca"], list(CATALOGO.keys()), "marca", other_label=L["otro"])
            modelos = CATALOGO.get(marca, []) if marca in CATALOGO else []
            if modelos:
                modelo = select_with_other(L["modelo"], modelos, "modelo", other_label=L["otro"])
            else:
                modelo = st.text_input("Modelo", key="modelo_free")
        with col6:
            serie = st.text_input(L["serie"], key="serie")
            asset = st.text_input(L["asset"], key="asset")
            codigo_or = st.text_input("Código OR", key="codigo_or")

        st.markdown("---")
        st.subheader("Accesorios y Estado")
        col7, col8 = st.columns(2)
        with col7:
            estado = select_with_other(L["estado"], ["Entrega", "Retiro", "Cambio"], "estado", other_label=L["otro"])
            cargador_estado = select_with_other(L["estado_cargador"], ["N/A", "OK", "DAÑADO", "FALTANTE"], "cargador_estado", other_label=L["otro"])

            accesorios = multiselect_with_manual(L["accesorios"], ["MOCHILA","TECLADO","CARGADOR NOTEBOOK","AUDIFONOS","CANDADO","MOUSE","DOCKING","CÁMARA WEB"], "accesorios")
        with col8:
            observaciones = st.text_area("Observaciones generales", key="observaciones")
            firma_tecnico = st.text_input("Firma técnico", value="", key="firma_tecnico")
            soporte = st.text_input("Soporte", value="", key="soporte")

        save = st.form_submit_button(L["guardar"])

        if save:
            # Validaciones: si select_with_other devolvió "" (OTRO seleccionado pero no escrito), pedir completar
            missing_manuals = []
            for key_name, display in [
                ("tipo_usuario", L["tipo_usuario"]),
                ("tipo_activo", L["tipo_activo"]),
                ("marca", L["marca"]),
                ("modelo", L["modelo"])
            ]:
                if st.session_state.get(f"{key_name}__select", None) == L["otro"] and not st.session_state.get(f"{key_name}__manual", "").strip():
                    missing_manuals.append(display)

            if missing_manuals:
                st.error(f"Complete los campos manuales para: {', '.join(missing_manuals)}")
            elif not ticket or not nombre or not ubicacion:
                st.error("Complete los campos obligatorios: Nombre, Ticket, Ubicación")
            else:
                c = conn()
                cur = c.cursor()
                accesorios_str = ", ".join(accesorios) if isinstance(accesorios, (list, tuple)) else str(accesorios)
                observaciones_full = observaciones or ""
                if accesorios_str:
                    observaciones_full = (observaciones_full + "\n" + "Accesorios: " + accesorios_str).strip()
                cur.execute("""
                    INSERT INTO form (
                        fecha, usuario, ritm, tipo_equipo, marca, modelo,
                        serie, hostname, asset, estado, ubicacion, observaciones
                    )
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    datetime.now().isoformat(),
                    nombre,
                    ticket,
                    tipo_activo,
                    marca,
                    modelo,
                    serie,
                    nombre_equipo,
                    asset,
                    estado,
                    ubicacion,
                    observaciones_full
                ))
                c.commit()
                c.close()
                try:
                    utils.log(st.session_state.user, "CREAR_FORM", f"RITM={ticket} ASSET={asset} MODELO={modelo}")
                except Exception:
                    pass
                st.success("Registro guardado correctamente")
                # limpiar manuales temporales
                st.session_state[f"accesorios__manuals"] = []
                for k in ["tipo_usuario", "tipo_activo", "marca", "modelo", "estado", "cargador_estado"]:
                    if f"{k}__manual" in st.session_state:
                        st.session_state[f"{k}__manual"] = ""
                safe_rerun()

# ======================
# HISTORIAL
# ======================
elif menu == L["historial"]:
    st.markdown("<div class='header-accent'><h3 style='margin:6px 12px'>Historial ABM</h3></div>", unsafe_allow_html=True)
    st.write("Filtra por Asset, Serie, Nombre, Hostname o RITM")

    colf1, colf2, colf3, colf4 = st.columns(4)
    with colf1:
        q_asset = st.text_input(L["asset"], key="q_asset")
    with colf2:
        q_serie = st.text_input(L["serie"], key="q_serie")
    with colf3:
        q_nombre = st.text_input("Nombre", key="q_nombre")
    with colf4:
        q_ritm = st.text_input(L["ritm"], key="q_ritm")

    c = conn().cursor()
    query = "SELECT * FROM form WHERE 1=1"
    params = []
    if q_asset:
        query += " AND asset LIKE ?"
        params.append(f"%{q_asset}%")
    if q_serie:
        query += " AND serie LIKE ?"
        params.append(f"%{q_serie}%")
    if q_nombre:
        query += " AND usuario LIKE ?"
        params.append(f"%{q_nombre}%")
    if q_ritm:
        query += " AND ritm LIKE ?"
        params.append(f"%{q_ritm}%")
    query += " ORDER BY id DESC LIMIT 500"
    c.execute(query, params)
    rows = c.fetchall()

    st.write(f"Resultados: {len(rows)}")
    for r in rows:
        col1, col2 = st.columns([8,2])
        with col1:
            st.markdown(f"""
            <div class="card">
            <b>ID:</b> {r[0]} |
            <b>RITM:</b> {r[3]} |
            <b>Usuario:</b> {r[2]} |
            <b>Asset:</b> {r[9]} |
            <b>Serie:</b> {r[7]} |
            <b>Estado:</b> {r[10]}
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("PDF", key=f"pdf_{r[0]}"):
                data = {
                    "USUARIO": r[2],
                    "TICKET": r[3],
                    "TIPO": r[4],
                    "MARCA": r[5],
                    "MODELO": r[6],
                    "SERIE": r[7],
                    "HOSTNAME": r[8],
                    "ASSET": r[9],
                    "ESTADO": r[10],
                    "UBICACION": r[11],
                    "OBSERVACIONES": r[12],
                    "FECHA": r[1]
                }
                file = f"form_{r[0]}.pdf"
                try:
                    generar_pdf(file, data)
                    with open(file, "rb") as f:
                        st.download_button("Descargar PDF", f, file_name=file)
                except Exception as e:
                    st.error(f"Error generando PDF: {e}")

# ======================
# EXPORT / CONFIG / SALIR
# ======================
elif menu == L["exportar"]:
    st.markdown("<div class='header-accent'><h3 style='margin:6px 12px'>Exportar</h3></div>", unsafe_allow_html=True)
    st.write("Exporta último registro a PDF o todo el historial a Excel")

    if st.button("Generar PDF último registro"):
        c = conn().cursor()
        c.execute("SELECT * FROM form ORDER BY id DESC LIMIT 1")
        r = c.fetchone()
        if r:
            data = {
                "USUARIO": r[2],
                "TICKET": r[3],
                "TIPO": r[4],
                "MARCA": r[5],
                "MODELO": r[6],
                "SERIE": r[7],
                "HOSTNAME": r[8],
                "ASSET": r[9],
                "ESTADO": r[10],
                "UBICACION": r[11],
                "OBSERVACIONES": r[12],
                "FECHA": r[1]
            }
            file = "ultimo_formulario.pdf"
            try:
                generar_pdf(file, data)
                with open(file, "rb") as f:
                    st.download_button("Descargar", f, file_name=file)
            except Exception as e:
                st.error(f"Error generando PDF: {e}")
        else:
            st.warning("No hay registros.")

    if st.button("Exportar todo a Excel"):
        try:
            file = utils.export_excel()
            with open(file, "rb") as f:
                st.download_button("Descargar Excel", f, file_name=file)
        except Exception as e:
            st.error(f"Error exportando Excel: {e}")

elif menu == L["config"]:
    st.markdown("<div class='header-accent'><h3 style='margin:6px 12px'>Configuración del Sistema</h3></div>", unsafe_allow_html=True)
    st.write("Ajustes visuales y de idioma")
    st.success("Configuración aplicada (temporal en sesión)")

elif menu == L["salir"]:
    try:
        utils.log(st.session_state.user, "LOGOUT", "Cierre de sesión")
    except Exception:
        pass
    st.session_state.auth = False
    safe_rerun()