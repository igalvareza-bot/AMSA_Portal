from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import sqlite3

DB = "amsa.db"

def generar_pdf(form_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM form WHERE id=?", (form_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return

    doc = SimpleDocTemplate(f"form_{form_id}.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Logo corporativo
    try:
        logo = Image("assets/logicalis_logo.png", width=120, height=60)
        story.append(logo)
        story.append(Spacer(1, 20))
    except Exception:
        pass

    # Título
    story.append(Paragraph("Formulario ABM", styles["Title"]))
    story.append(Spacer(1, 20))

    # Datos
    labels = ["ID", "Fecha", "Usuario", "RITM", "Tipo Equipo", "Marca", "Modelo",
              "Serie", "Hostname", "Asset", "Estado", "Ubicación", "Observaciones"]

    for i, label in enumerate(labels):
        story.append(Paragraph(f"<b>{label}:</b> {row[i]}", styles["Normal"]))
        story.append(Spacer(1, 12))

    doc.build(story)
