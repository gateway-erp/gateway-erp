from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
from datetime import date, timedelta
import json, os, re

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Workaround Python 3.14 + Jinja2 cache bug: caché desactivada
_jinja_env = Environment(loader=FileSystemLoader("templates"), cache_size=0)

class _Templates:
    def TemplateResponse(self, name, context):
        t = _jinja_env.get_template(name)
        html = t.render(**{k: v for k, v in context.items() if k != "request"})
        return HTMLResponse(html)

templates = _Templates()

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs("presupuestos/output", exist_ok=True)

# ── helpers de datos ──────────────────────────────────────────────────────────
def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def next_numero():
    today = date.today()
    prefix = f"PR{str(today.year)[2:]}{today.month:02d}"
    counters = load_json(f"{DATA_DIR}/counters.json", {})
    n = counters.get(prefix, 0) + 1
    counters[prefix] = n
    save_json(f"{DATA_DIR}/counters.json", counters)
    return f"{prefix}-{n:04d}"

def peek_numero():
    """Devuelve el próximo número sin incrementar el contador."""
    today = date.today()
    prefix = f"PR{str(today.year)[2:]}{today.month:02d}"
    counters = load_json(f"{DATA_DIR}/counters.json", {})
    n = counters.get(prefix, 0) + 1
    return f"{prefix}-{n:04d}"

# ── rutas ─────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def form(request: Request):
    hoy       = date.today()
    validez   = hoy + timedelta(days=30)
    numero    = peek_numero()
    clientes  = load_json(f"{DATA_DIR}/clientes.json", [])
    return templates.TemplateResponse("nuevo_presupuesto.html", {
        "request":  request,
        "fecha":    hoy.strftime("%Y-%m-%d"),
        "validez":  validez.strftime("%Y-%m-%d"),
        "numero":   numero,
        "clientes": clientes,
    })

@app.get("/api/clientes")
async def buscar_clientes(q: str = ""):
    clientes = load_json(f"{DATA_DIR}/clientes.json", [])
    q = q.lower()
    return [c for c in clientes if q in c["nombre"].lower() or q in str(c["codigo"])]

@app.get("/api/items-sugeridos")
async def items_sugeridos(q: str = ""):
    items = load_json(f"{DATA_DIR}/items_sugeridos.json", [])
    q = q.lower()
    return [i for i in items if q in i["descripcion"].lower()][:8]

@app.post("/generar")
async def generar(request: Request):
    form_data = await request.form()

    # cliente: buscar existente o crear nuevo
    cliente_id = form_data.get("cliente_id", "").strip()
    clientes   = load_json(f"{DATA_DIR}/clientes.json", [])

    if cliente_id and cliente_id.isdigit():
        cliente = next((c for c in clientes if str(c["codigo"]) == cliente_id), None)
        # actualizar CUIT si se modificó
        if cliente and form_data.get("cliente_cuit"):
            cliente["cuit"] = form_data.get("cliente_cuit", "")
            save_json(f"{DATA_DIR}/clientes.json", clientes)
    else:
        # cliente nuevo
        nuevo_codigo = (max((c["codigo"] for c in clientes), default=0) + 1)
        cliente = {
            "codigo":    nuevo_codigo,
            "nombre":    form_data.get("cliente_nombre", ""),
            "cuit":      form_data.get("cliente_cuit", ""),
            "direccion": form_data.get("cliente_direccion", ""),
            "ciudad":    form_data.get("cliente_ciudad", ""),
        }
        clientes.append(cliente)
        save_json(f"{DATA_DIR}/clientes.json", clientes)

    # ítems
    descripciones = form_data.getlist("desc[]")
    precios       = form_data.getlist("pu[]")
    cantidades    = form_data.getlist("cant[]")
    ivas          = form_data.getlist("iva[]")

    items = []
    items_sugeridos = load_json(f"{DATA_DIR}/items_sugeridos.json", [])
    descripciones_existentes = {i["descripcion"] for i in items_sugeridos}

    for desc, pu, cant, iva in zip(descripciones, precios, cantidades, ivas):
        if not desc.strip():
            continue
        item = {
            "descripcion":     desc.strip(),
            "precio_unitario": float(pu or 0),
            "cantidad":        int(cant or 1),
            "iva_pct":         float(iva or 10.5),
        }
        items.append(item)
        # aprender ítem si es nuevo
        if desc.strip() not in descripciones_existentes:
            items_sugeridos.append({"descripcion": desc.strip(), "precio_unitario": float(pu or 0), "iva_pct": float(iva or 10.5)})
            descripciones_existentes.add(desc.strip())

    save_json(f"{DATA_DIR}/items_sugeridos.json", items_sugeridos)

    numero = next_numero()
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

    # guardar en historial
    historial = load_json(f"{DATA_DIR}/historial.json", [])
    historial.append({**datos, "archivo": nombre_archivo, "estado": "generado"})
    save_json(f"{DATA_DIR}/historial.json", historial)

    return FileResponse(output_path, media_type="application/pdf", filename=nombre_archivo)
