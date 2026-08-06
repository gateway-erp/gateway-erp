from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from datetime import date, timedelta
import os

import db
import cotizacion

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

os.makedirs("presupuestos/output", exist_ok=True)

# Workaround Python 3.14 + Jinja2 cache bug
_jinja_env = Environment(loader=FileSystemLoader("templates"), cache_size=0)

class _Templates:
    def TemplateResponse(self, name, context):
        t = _jinja_env.get_template(name)
        html = t.render(**{k: v for k, v in context.items() if k != "request"})
        return HTMLResponse(html)

templates = _Templates()


# ── rutas ─────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    historial = db.load_historial()
    hoy = date.today()
    mes_actual = f"{str(hoy.year)[2:]}{hoy.month:02d}"

    # calcular totales por presupuesto
    def calcular_total(p):
        items = p.get("items", [])
        if isinstance(items, list):
            base = sum(i.get("precio_unitario", 0) * i.get("cantidad", 1) for i in items)
            iva  = sum(i.get("precio_unitario", 0) * i.get("cantidad", 1) * i.get("iva_pct", 0) / 100 for i in items)
            return base + iva
        return 0

    def fmt(n):
        return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    for p in historial:
        p["total_fmt"] = fmt(p.get("total", 0))

    stats = {
        "mes":        sum(1 for p in historial if mes_actual in p.get("numero", "")),
        "pendientes": sum(1 for p in historial if p.get("estado") in ("generado", "enviado")),
        "aprobados":  sum(1 for p in historial if p.get("estado") == "aprobado" and mes_actual in p.get("numero", "")),
    }

    return templates.TemplateResponse("dashboard.html", {
        "request":        request,
        "historial":      list(reversed(historial)),
        "stats":          stats,
        "proximo_numero": db.peek_numero(),
    })

@app.get("/nuevo", response_class=HTMLResponse)
async def form(request: Request):
    hoy     = date.today()
    validez = hoy + timedelta(days=30)
    numero  = db.peek_numero()
    return templates.TemplateResponse("nuevo_presupuesto.html", {
        "request": request,
        "fecha":   hoy.strftime("%Y-%m-%d"),
        "validez": validez.strftime("%Y-%m-%d"),
        "numero":  numero,
    })

@app.get("/api/cotizacion")
async def api_cotizacion():
    return cotizacion.get_cotizacion()

@app.get("/api/clientes")
async def buscar_clientes(q: str = ""):
    clientes = db.load_clientes()
    q = q.lower()
    return [c for c in clientes if q in str(c["nombre"]).lower() or q in str(c["codigo"])]

@app.get("/api/items-sugeridos")
async def items_sugeridos(q: str = ""):
    items = db.load_items()
    q = q.lower()
    return [i for i in items if q in str(i["descripcion"]).lower()][:8]

@app.post("/generar")
async def generar(request: Request):
    form_data = await request.form()

    # ── cliente ───────────────────────────────────────────────────────────────
    cliente_id = form_data.get("cliente_id", "").strip()
    clientes   = db.load_clientes()

    if cliente_id and cliente_id.isdigit():
        cliente = next((c for c in clientes if str(c["codigo"]) == cliente_id), None)
        if cliente and form_data.get("cliente_cuit"):
            cliente["cuit"] = form_data.get("cliente_cuit", "")
            db.actualizar_cuit(cliente_id, cliente["cuit"])
    else:
        codigo  = db.next_codigo_cliente()
        cliente = {
            "codigo":    codigo,
            "nombre":    form_data.get("cliente_nombre", ""),
            "cuit":      form_data.get("cliente_cuit", ""),
            "direccion": form_data.get("cliente_direccion", ""),
            "ciudad":    form_data.get("cliente_ciudad", ""),
        }
        db.crear_cliente(cliente)

    # ── ítems ─────────────────────────────────────────────────────────────────
    descripciones = form_data.getlist("desc[]")
    precios       = form_data.getlist("pu[]")
    cantidades    = form_data.getlist("cant[]")
    ivas          = form_data.getlist("iva[]")

    items_existentes = {i["descripcion"] for i in db.load_items()}
    items = []

    for desc, pu, cant, iva in zip(descripciones, precios, cantidades, ivas):
        if not desc.strip():
            continue
        item = {
            "descripcion":     desc.strip(),
            "precio_unitario": float(pu or 0),
            "cantidad":        int(cant or 1),
            "iva_pct":         float(iva or 21),
        }
        items.append(item)
        if desc.strip() not in items_existentes:
            db.guardar_item(item)
            items_existentes.add(desc.strip())

    # ── generar PDF ───────────────────────────────────────────────────────────
    numero = db.next_numero()
    ref    = form_data.get("ref", "").strip()

    datos = {
        "numero":           numero,
        "ref_cliente":      ref,
        "fecha":            form_data.get("fecha", ""),
        "fecha_validez":    form_data.get("validez", ""),
        "codigo_cliente":   f"C-{cliente['codigo']:04d}",
        "moneda":           form_data.get("moneda", "ARS"),
        "condiciones_pago": form_data.get("condiciones_pago", ""),
        "cliente":          cliente,
        "items":            items,
    }

    nombre_archivo = f"{numero} - {ref}.pdf" if ref else f"{numero}.pdf"
    output_path    = os.path.join("presupuestos", "output", nombre_archivo)

    from presupuestos.generar_pdf import generar_presupuesto
    generar_presupuesto(datos, output_path)

    db.guardar_historial(datos, nombre_archivo)

    return FileResponse(output_path, media_type="application/pdf", filename=nombre_archivo)
