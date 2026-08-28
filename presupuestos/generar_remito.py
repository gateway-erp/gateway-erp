from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas as pdfcanvas
import os

_NEW_LOGO = os.path.join(os.path.dirname(__file__), "..", "Logo-Gateway.jpeg")
_OLD_LOGO = os.path.join(os.path.dirname(__file__), "..", "assets", "logo_gateway_0.png")
LOGO_PATH = _NEW_LOGO if os.path.exists(_NEW_LOGO) else _OLD_LOGO

NAVY       = colors.HexColor("#1B2A4A")
LIGHT_GRAY = colors.HexColor("#E4E8EE")
WHITE      = colors.white

PAGE_W, PAGE_H = A4
MARGIN_L = 15*mm
MARGIN_R = 15*mm
MARGIN_T = 12*mm
FOOTER_H = 36*mm
MARGIN_B = FOOTER_H + 8*mm
W = PAGE_W - MARGIN_L - MARGIN_R

EMISOR_NOMBRE = "SANTIAGO FEDERICO PIUSSAN"
EMISOR_CUIT   = "20-28714251-0"
EMISOR_IB     = "20-28714251-0"


def s(name, **kw):
    return ParagraphStyle(name, **kw)


def draw_footer(c):
    y_bottom = 12*mm
    box_top  = y_bottom + FOOTER_H

    # Línea separadora
    c.setStrokeColor(LIGHT_GRAY)
    c.setLineWidth(0.5)
    c.line(MARGIN_L, box_top, MARGIN_L + W, box_top)

    # Etiqueta
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(NAVY)
    c.drawString(MARGIN_L, box_top - 7*mm, "RECIBIÓ CONFORME:")

    # Caja firma izquierda
    firma_x = MARGIN_L
    firma_y = y_bottom + 2*mm
    firma_w = W * 0.45
    firma_h = 20*mm
    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(0.5)
    c.rect(firma_x, firma_y, firma_w, firma_h)
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.grey)
    c.drawString(firma_x + 2*mm, firma_y + firma_h - 5*mm, "FIRMA")

    # Caja aclaración derecha
    acl_x = MARGIN_L + W * 0.55
    acl_w = W * 0.45
    c.setStrokeColor(colors.lightgrey)
    c.rect(acl_x, firma_y, acl_w, firma_h)
    c.drawString(acl_x + 2*mm, firma_y + firma_h - 5*mm, "ACLARACIÓN")


def draw_header(c, datos):
    y = PAGE_H - MARGIN_T

    # Logo
    if os.path.exists(LOGO_PATH):
        logo_h = 18*mm
        logo_w = logo_h * 3.2
        c.drawImage(LOGO_PATH, MARGIN_L, y - logo_h, width=logo_w, height=logo_h,
                    preserveAspectRatio=True, mask="auto")

    # Datos emisor (centro)
    cx = MARGIN_L + W / 2
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(NAVY)
    c.drawCentredString(cx, y - 7*mm, EMISOR_NOMBRE)
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    c.drawCentredString(cx, y - 12*mm, f"C.U.I.T.: {EMISOR_CUIT}   –   I.B.: {EMISOR_IB}")

    # Bloque REMITO (derecha)
    rx = MARGIN_L + W
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(NAVY)
    c.drawRightString(rx, y - 6*mm, f"Remito # {datos['numero']}")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    c.drawRightString(rx, y - 12*mm, f"Fecha: {datos['fecha']}")

    # Línea separadora
    c.setStrokeColor(NAVY)
    c.setLineWidth(1)
    c.line(MARGIN_L, y - 16*mm, MARGIN_L + W, y - 16*mm)

    # Destinatario
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(NAVY)
    c.drawString(MARGIN_L, y - 22*mm, "Entrega:")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    c.drawString(MARGIN_L + 22*mm, y - 22*mm, datos.get("entrega", ""))

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(NAVY)
    c.drawString(MARGIN_L, y - 27*mm, "C.U.I.T.:")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    c.drawString(MARGIN_L + 22*mm, y - 27*mm, datos.get("cuit_dest", ""))

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(NAVY)
    c.drawString(MARGIN_L, y - 32*mm, "Domicilio:")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    c.drawString(MARGIN_L + 22*mm, y - 32*mm, datos.get("domicilio", ""))

    c.setStrokeColor(LIGHT_GRAY)
    c.setLineWidth(0.5)
    c.line(MARGIN_L, y - 35*mm, MARGIN_L + W, y - 35*mm)

    return y - 38*mm   # top disponible para el contenido


def generar_remito(datos, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Canvas manual para header/footer fijos
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import Frame

    c = Canvas(output_path, pagesize=A4)

    content_top = draw_header(c, datos)
    draw_footer(c)

    # Tabla de ítems
    st_head = s("th", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE,
                 alignment=TA_CENTER, leading=10)
    st_cell = s("td", fontName="Helvetica", fontSize=8, textColor=colors.black,
                 alignment=TA_LEFT, leading=11)
    st_cant = s("cant", fontName="Helvetica", fontSize=8, textColor=colors.black,
                alignment=TA_CENTER, leading=11)

    col_cant = 18*mm
    col_det  = W - col_cant

    table_data = [
        [Paragraph("CANTIDAD", st_head), Paragraph("D E T A L L E", st_head)]
    ]
    for it in datos.get("items", []):
        det = str(it.get("detalle", "")).replace("\n", "<br/>")
        table_data.append([
            Paragraph(str(it.get("cantidad", "")), st_cant),
            Paragraph(det, st_cell),
        ])

    tbl = Table(table_data, colWidths=[col_cant, col_det])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID",         (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
    ]))

    avail_h = content_top - MARGIN_B
    frame = Frame(MARGIN_L, MARGIN_B, W, avail_h, showBoundary=0)
    story  = [tbl]
    frame.addFromList(story, c)

    c.save()
