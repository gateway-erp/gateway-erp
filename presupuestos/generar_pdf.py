from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, Frame, BaseDocTemplate, PageTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.pdfgen import canvas as pdfcanvas
import os

LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo_gateway_0.png")
NAVY       = colors.HexColor("#1B2A4A")
LIGHT_GRAY = colors.HexColor("#F2F2F2")
WHITE      = colors.white

PAGE_W, PAGE_H = A4
MARGIN_L = 15*mm
MARGIN_R = 15*mm
MARGIN_T = 12*mm
FOOTER_H = 52*mm   # altura reservada para el pie fijo
MARGIN_B = FOOTER_H + 5*mm

W = PAGE_W - MARGIN_L - MARGIN_R  # ancho útil

def s(name, **kw):
    return ParagraphStyle(name, **kw)


# ── PIE FIJO dibujado en canvas ───────────────────────────────────────────────
def draw_footer(c, datos):
    moneda = datos.get("moneda", "USD")
    items  = datos["items"]

    base_total   = sum(i["precio_unitario"] * i["cantidad"] for i in items)
    iva_totales  = {}
    for i in items:
        pct = i["iva_pct"]
        iva_totales[pct] = iva_totales.get(pct, 0) + i["precio_unitario"] * i["cantidad"] * pct / 100
    iva_total = sum(iva_totales.values())
    total     = base_total + iva_total

    def fmt(n):
        return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    y_bottom = 12*mm          # margen inferior de la hoja
    box_top  = y_bottom + FOOTER_H
    box_h    = FOOTER_H

    # ── columna izquierda: condiciones + firma ────────────────────────────────
    left_w  = W - 72*mm
    firma_y = y_bottom + 3*mm
    firma_h = (len(iva_totales) + 2) * 7*mm   # misma altura que bloque totales
    cond_y  = firma_y + firma_h + 2*mm         # justo encima de la caja firma
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    c.drawString(MARGIN_L + 3*mm, cond_y, "Condiciones de pago:")
    c.drawString(MARGIN_L + 38*mm, cond_y, datos.get("condiciones_pago", ""))

    # caja firma
    firma_x = MARGIN_L + 3*mm
    firma_w = left_w - 6*mm
    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(0.5)
    c.rect(firma_x, firma_y, firma_w, firma_h)
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.grey)
    c.drawString(firma_x + 2*mm, firma_y + firma_h - 5*mm, "Aceptación por escrito, sello de la empresa, fecha y firma")

    # ── columna derecha: totales (exactamente igual de alto que caja firma) ───
    tot_x  = MARGIN_L + left_w + 2*mm
    tot_w  = 70*mm - 2*mm

    rows   = [("Base imponible", fmt(base_total))]
    for pct, monto in sorted(iva_totales.items()):
        rows.append((f"Total IVA {pct}%", fmt(monto)))
    n_rows = len(rows)

    # altura fija por fila, la caja firma se ajusta a esto (no al revés)
    tot_block_bottom = firma_y
    row_h            = 7*mm

    for idx, (label, valor) in enumerate(rows):
        ry = tot_block_bottom + row_h + (n_rows - 1 - idx) * row_h
        c.setFillColor(LIGHT_GRAY)
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.3)
        c.rect(tot_x, ry, tot_w, row_h, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8)
        c.drawString(tot_x + 2*mm, ry + row_h * 0.3, label)
        c.drawRightString(tot_x + tot_w - 2*mm, ry + row_h * 0.3, valor)

    # fila Total (navy) — pegada al fondo de la caja firma
    c.setFillColor(NAVY)
    c.rect(tot_x, tot_block_bottom, tot_w, row_h, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(tot_x + 2*mm, tot_block_bottom + row_h * 0.3, "Total")
    c.drawRightString(tot_x + tot_w - 2*mm, tot_block_bottom + row_h * 0.3, fmt(total))


def generar_presupuesto(datos, output_path):

    class PdfWithFooter(BaseDocTemplate):
        def __init__(self, filename, **kw):
            super().__init__(filename, **kw)
            frame = Frame(
                MARGIN_L, MARGIN_B,
                W, PAGE_H - MARGIN_T - MARGIN_B,
                leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0,
            )
            self.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=self._on_page)])

        def _on_page(self, canvas, doc):
            draw_footer(canvas, datos)

    doc = PdfWithFooter(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T,
        bottomMargin=MARGIN_B,
    )

    elements = []

    # ── ENCABEZADO: logo | datos del presupuesto ──────────────────────────────
    logo = Image(LOGO_PATH, width=50*mm, height=17*mm)

    ref_data = [
        [Paragraph("<b>Presupuesto</b>", s("ref", fontName="Helvetica-Bold", fontSize=13, textColor=NAVY, alignment=TA_RIGHT))],
        [Paragraph(f"Ref. : {datos['numero']}",               s("r1", fontName="Helvetica", fontSize=8, textColor=NAVY, alignment=TA_RIGHT))],
        [Paragraph(f"Ref. cliente : {datos['ref_cliente']}",  s("r2", fontName="Helvetica", fontSize=8, textColor=NAVY, alignment=TA_RIGHT))],
        [Paragraph(f"Fecha : {datos['fecha']}",               s("r3", fontName="Helvetica", fontSize=8, textColor=NAVY, alignment=TA_RIGHT))],
        [Paragraph(f"Fecha fin de validez : {datos['fecha_validez']}", s("r4", fontName="Helvetica", fontSize=8, textColor=NAVY, alignment=TA_RIGHT))],
        [Paragraph(f"Código cliente : {datos['codigo_cliente']}", s("r5", fontName="Helvetica", fontSize=8, textColor=NAVY, alignment=TA_RIGHT))],
    ]
    ref_table = Table(ref_data, colWidths=[70*mm])
    ref_table.setStyle(TableStyle([
        ("ALIGN",         (0,0),(-1,-1), "RIGHT"),
        ("TOPPADDING",    (0,0),(-1,-1), 1),
        ("BOTTOMPADDING", (0,0),(-1,-1), 1),
    ]))

    header = Table([[logo, ref_table]], colWidths=[W-70*mm, 70*mm])
    header.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP")]))
    elements.append(header)
    elements.append(Spacer(1, 5*mm))

    # ── EMISOR / DESTINATARIO ─────────────────────────────────────────────────
    cs = s("cs", fontName="Helvetica", fontSize=8, leading=12)
    cb = s("cb", fontName="Helvetica-Bold", fontSize=9, leading=13)

    emisor_rows = [
        [Paragraph("Emisor:", s("el", fontName="Helvetica", fontSize=7, textColor=colors.grey))],
        [Paragraph("GateWay",               cb)],
        [Paragraph("Rivadavia 919",         cs)],
        [Paragraph("2804 Campana",          cs)],
        [Spacer(1, 2*mm)],
        [Paragraph("Teléfono: +54-3489-683375",          cs)],
        [Paragraph("Email: administracion@gateway.com.ar", cs)],
        [Paragraph("Web: www.gateway.com.ar",              cs)],
    ]
    emisor_t = Table(emisor_rows, colWidths=[W/2 - 5*mm])
    emisor_t.setStyle(TableStyle([
        ("BOX", (0,0),(-1,-1), 0.5, colors.lightgrey),
        ("LEFTPADDING",(0,0),(-1,-1),4), ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),2),  ("BOTTOMPADDING",(0,0),(-1,-1),2),
    ]))

    cliente = datos["cliente"]
    dest_rows = [
        [Paragraph("Enviar a:", s("ea", fontName="Helvetica", fontSize=7, textColor=colors.grey))],
        [Paragraph(cliente["nombre"],    cb)],
    ]
    if cliente.get("cuit"):
        dest_rows.append([Paragraph(f"CUIT: {cliente['cuit']}", cs)])
    dest_rows += [
        [Paragraph(cliente.get("direccion", ""), cs)],
        [Paragraph(cliente.get("ciudad", ""),    cs)],
    ]
    dest_t = Table(dest_rows, colWidths=[W/2 - 5*mm])
    dest_t.setStyle(TableStyle([
        ("BOX", (0,0),(-1,-1), 0.5, colors.lightgrey),
        ("BACKGROUND",(0,0),(-1,-1), LIGHT_GRAY),
        ("LEFTPADDING",(0,0),(-1,-1),4), ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),2),  ("BOTTOMPADDING",(0,0),(-1,-1),2),
    ]))

    dir_row = Table([[emisor_t, dest_t]], colWidths=[W/2, W/2])
    dir_row.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0), ("RIGHTPADDING",(0,0),(-1,-1),0),
    ]))
    elements.append(dir_row)
    elements.append(Spacer(1, 4*mm))

    # ── TABLA DE ÍTEMS ────────────────────────────────────────────────────────
    moneda = datos.get("moneda", "USD")
    th = lambda t, align=TA_LEFT: Paragraph(t, s("th", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE, alignment=align))

    col_w = [W*0.52, W*0.08, W*0.13, W*0.08, W*0.19]
    rows  = [[th("Descripción"), th("IVA", TA_CENTER), th("P.U.", TA_RIGHT), th("Cant.", TA_CENTER), th("Base imponible", TA_RIGHT)]]

    def fmt(n):
        return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    for item in datos["items"]:
        pu   = item["precio_unitario"]
        cant = item["cantidad"]
        pct  = item["iva_pct"]
        base = pu * cant
        rows.append([
            Paragraph(item["descripcion"], cs),
            Paragraph(f"{pct}%",    s("ic", fontName="Helvetica", fontSize=8, alignment=TA_CENTER)),
            Paragraph(fmt(pu),      s("ir", fontName="Helvetica", fontSize=8, alignment=TA_RIGHT)),
            Paragraph(str(cant),    s("iq", fontName="Helvetica", fontSize=8, alignment=TA_CENTER)),
            Paragraph(fmt(base),    s("ib", fontName="Helvetica", fontSize=8, alignment=TA_RIGHT)),
        ])

    # relleno hasta al menos 8 filas de contenido
    for _ in range(max(0, 8 - len(datos["items"]))):
        rows.append(["", "", "", "", ""])

    items_t = Table(rows, colWidths=col_w, repeatRows=1)
    items_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), NAVY),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHT_GRAY]),
        ("GRID",          (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))

    elements.append(Paragraph(
        f"Importes visualizados en {'Dólares USA' if moneda == 'USD' else 'Pesos ARS'}",
        s("mon", fontName="Helvetica", fontSize=7, textColor=colors.grey, alignment=TA_RIGHT)
    ))
    elements.append(Spacer(1, 1*mm))
    elements.append(items_t)

    doc.build(elements)
    print(f"PDF generado: {output_path}")


# ── DATOS DE PRUEBA ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    datos_prueba = {
        "numero":          "PR2606-1159",
        "ref_cliente":     "Notebook LENOVO",
        "fecha":           "29/06/2026",
        "fecha_validez":   "29/07/2026",
        "codigo_cliente":  "C-0013",
        "moneda":          "USD",
        "condiciones_pago": "A la recepción de la factura",
        "cliente": {
            "nombre":    "TOYOTA BOSHOKU ARGENTINA",
            "direccion": "Ruta 9 - Campana",
            "ciudad":    "2804 Campana",
        },
        "items": [
            {
                "descripcion":    'LENOVO THINKBOOK 16 G8 IRL Intel® Core 7 240H 16GB 512GB 16" WUXGA (1920x1200) IPS WIN 11 PRO Teclado español\n\nTODOS LOS EQUIPOS TIENEN ENTREGA EN MENOS DE 48 HORAS Y GARANTÍA ORIGINAL LENOVO DE 12 MESES.',
                "precio_unitario": 2173.57,
                "cantidad":        1,
                "iva_pct":         10.5,
            }
        ],
    }
    out = r"J:\Mi unidad\Gateway\Software-gestion\presupuestos\PRUEBA_PR2606-1159.pdf"
    generar_presupuesto(datos_prueba, out)
