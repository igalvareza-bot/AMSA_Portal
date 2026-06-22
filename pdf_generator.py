from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import mm
from datetime import datetime
import qrcode
from io import BytesIO
from reportlab.lib.utils import ImageReader
import os

LOGO_PATH = os.path.join("assets", "logicalis_logo.jpg")

# Corporate colors
PRIMARY = colors.HexColor("#003366")
ACCENT = colors.HexColor("#FF8C00")
TEXT = colors.black

def draw_box(c, x, y, w, h, title, value, title_size=8, value_size=9):
    c.setStrokeColor(PRIMARY)
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", title_size)
    c.setFillColor(PRIMARY)
    c.drawString(x + 4, y + h - 12, title)
    c.setFont("Helvetica", value_size)
    c.setFillColor(TEXT)
    # wrap long text simply
    text = str(value) if value is not None else ""
    c.drawString(x + 4, y + 6, text)

def generar_qr_image(data, size=120):
    qr = qrcode.QRCode(box_size=2, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return ImageReader(bio)

def generar_pdf(file, d):
    c = canvas.Canvas(file, pagesize=letter)
    w, h = letter

    # Header background
    c.setFillColor(PRIMARY)
    c.rect(0, h - 70, w, 70, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, h - 45, "ANTOFAGASTA MINERALS - LOGICALIS")
    c.setFont("Helvetica", 10)
    c.drawString(50, h - 60, "FORMULARIO ENTREGA / RETIRO DE ACTIVOS TI")

    # Logo (if exists)
    try:
        if os.path.exists(LOGO_PATH):
            logo = ImageReader(LOGO_PATH)
            c.drawImage(logo, w - 150, h - 65, width=110, height=50, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    # Subtitle
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, h - 85, "REQUERIMIENTO ENTREGA")
    c.setFont("Helvetica", 9)
    c.drawString(50, h - 100, f"Fecha generación: {d.get('FECHA', datetime.now().isoformat())}")

    # Start Y
    y = h - 130

    # INFORMACIÓN USUARIO block
    draw_box(c, 40, y - 60, 260, 60, "INFORMACIÓN USUARIO", "")
    # inside fields
    c.setFont("Helvetica", 9)
    c.drawString(46, y - 20, f"NOMBRE: {d.get('USUARIO', '')}")
    c.drawString(46, y - 34, f"RUT: {d.get('RUT', '')}")
    c.drawString(46, y - 48, f"UBICACIÓN: {d.get('UBICACION', '')}")

    # Right side: ticket and cargo/responsable
    draw_box(c, 310, y - 60, 240, 60, "TICKET / RESPONSABLE", "")
    c.drawString(316, y - 20, f"TICKET: {d.get('TICKET', '')}")
    c.drawString(316, y - 34, f"CARGO: {d.get('CARGO', '')}")
    c.drawString(316, y - 48, f"RESPONSABLE: {d.get('RESPONSABLE', '')}")

    y -= 80

    # DATOS DE ENTREGA
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "DATOS DE ENTREGA")
    y -= 18

    # Row of boxes for equipo
    draw_box(c, 40, y - 50, 200, 50, "NOMBRE DE EQUIPO", d.get("HOSTNAME", ""))
    draw_box(c, 250, y - 50, 120, 50, "TIPO DE ACTIVO", d.get("TIPO", ""))
    draw_box(c, 380, y - 50, 120, 50, "MARCA", d.get("MARCA", ""))
    draw_box(c, 510, y - 50, 80, 50, "MODELO", d.get("MODELO", ""))

    y -= 70
    draw_box(c, 40, y - 50, 200, 50, "SERIE", d.get("SERIE", ""))
    draw_box(c, 250, y - 50, 120, 50, "ASSET", d.get("ASSET", ""))
    draw_box(c, 380, y - 50, 210, 50, "CÓDIGO OR / CÓDIGO", d.get("CODIGO", ""))

    # QR for asset or ticket
    qr_data = d.get("ASSET", "") or d.get("TICKET", "") or d.get("HOSTNAME", "")
    if qr_data:
        try:
            qr_img = generar_qr_image(qr_data)
            c.drawImage(qr_img, 510, y - 40, width=70, height=70)
        except Exception:
            pass

    y -= 90

    # ACCESORIOS / ESTADO
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "ACCESORIOS / ESTADO")
    y -= 18
    draw_box(c, 40, y - 40, 300, 40, "ACCESORIOS", ", ".join(d.get("ACCESORIOS", [])))
    draw_box(c, 350, y - 40, 240, 40, "ESTADO CARGADOR", d.get("CARGADOR_ESTADO", "N/A"))

    y -= 60

    # OBSERVACIONES
    draw_box(c, 40, y - 80, 510, 80, "OBSERVACIONES GENERALES", d.get("OBSERVACIONES", ""))

    # Footer: firmas
    y -= 100
    draw_box(c, 40, y - 40, 240, 40, "FIRMA TÉCNICO", d.get("FIRMA_TECNICO", ""))
    draw_box(c, 300, y - 40, 240, 40, "SOPORTE", d.get("SOPORTE", ""))

    # Small footer text
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.gray)
    c.drawString(40, 30, "Documento generado por AMSA Portal - Logicalis")
    c.save()
