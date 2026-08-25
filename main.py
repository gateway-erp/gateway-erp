from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from datetime import date, timedelta
from typing import Optional
import os, shutil

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
@app.get("/debug-error")
async def debug_error():
    import traceback
    try:
        historial = db.load_historial()
        facturas  = db.load_facturas()
        return JSONResponse({"ok": True, "historial_count": len(historial), "facturas_count": len(facturas)})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e), "trace": traceback.format_exc()}, status_code=200)


@app.get("/debug-drive")
async def debug_drive():
    """Diagnostica la conexión con Google Drive."""
    import traceback
    try:
        import drive as drive_mod
        svc = drive_mod._service()
        # Verificar que la carpeta raíz existe y es accesible
        root = svc.files().get(fileId=drive_mod.DRIVE_ROOT_ID, fields="id,name").execute()
        # Listar carpetas dentro de la raíz
        q = f"'{drive_mod.DRIVE_ROOT_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        res = svc.files().list(q=q, fields="files(id,name)").execute()
        subcarpetas = [f["name"] for f in res.get("files", [])]
        return JSONResponse({
            "ok": True,
            "root_id": drive_mod.DRIVE_ROOT_ID,
            "root_name": root.get("name"),
            "subcarpetas": subcarpetas,
        })
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e), "trace": traceback.format_exc()})


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    historial  = db.load_historial()
    try:
        todas_facs = db.load_facturas()
    except Exception as e:
        print(f"[Dashboard] Error cargando facturas: {e}")
        todas_facs = []
    hoy        = date.today()
    mes_actual = f"{str(hoy.year)[2:]}{hoy.month:02d}"

    def fmt(n):
        try:
            return f"{float(n):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return "—"

    # Indexar facturas por presupuesto
    facs_por_presup = {}
    for f in todas_facs:
        k = str(f.get("presupuesto_numero", ""))
        facs_por_presup.setdefault(k, []).append(f)

    for p in historial:
        p["total_fmt"] = fmt(p.get("total", 0))
        numero = str(p.get("numero", ""))
        facs   = facs_por_presup.get(numero, [])
        p["facturas"] = facs
        if facs:
            p["cobro_ok"] = all(str(f.get("cobro_ok", "no")).lower() == "si" for f in facs)
        else:
            p["cobro_ok"] = None  # sin facturas

    stats = {
        "mes":        sum(1 for p in historial if mes_actual in p.get("numero", "")),
        "pendientes": sum(1 for p in historial if p.get("estado") in ("generado", "enviado")),
        "aprobados":  sum(1 for p in historial if p.get("estado") == "aprobado" and mes_actual in p.get("numero", "")),
    }

    historial_rev = list(reversed(historial))
    enviados   = [p for p in historial_rev if p.get("estado") in ("enviado", "generado")]
    aprobados  = [p for p in historial_rev if p.get("estado") == "aprobado"]
    facturados = [p for p in historial_rev if p.get("estado") == "facturado"]
    rechazados = [p for p in historial_rev if p.get("estado") == "rechazado"]

    return templates.TemplateResponse("dashboard.html", {
        "request":        request,
        "historial":      historial_rev,
        "enviados":       enviados,
        "aprobados":      aprobados,
        "facturados":     facturados,
        "rechazados":     rechazados,
        "stats":          stats,
        "proximo_numero": db.peek_numero(),
    })

@app.get("/editar/{numero}", response_class=HTMLResponse)
async def editar_form(numero: str, request: Request):
    import json as _json
    historial = db.load_historial()
    row = next((r for r in historial if str(r["numero"]) == numero), None)
    if not row:
        return HTMLResponse(f"<h3>Presupuesto {numero} no encontrado.</h3>", status_code=404)

    datos_json = row.get("datos_json", "")
    if datos_json:
        try:
            datos = _json.loads(datos_json)
        except Exception:
            datos = {}
    else:
        datos = {}

    cliente = datos.get("cliente", {})
    items   = datos.get("items", [])

    return templates.TemplateResponse("nuevo_presupuesto.html", {
        "request":                  request,
        "fecha":                    row.get("fecha", ""),
        "validez":                  row.get("fecha_validez", ""),
        "numero":                   numero,
        "edit_mode":                True,
        "cliente_id":               str(cliente.get("codigo", "")),
        "cliente_nombre":           cliente.get("nombre", row.get("cliente_nombre", "")),
        "cliente_cuit":             cliente.get("cuit", ""),
        "cliente_direccion":        cliente.get("direccion", ""),
        "cliente_ciudad":           cliente.get("ciudad", ""),
        "moneda_inicial":           row.get("moneda", "USD"),
        "ref_inicial":              row.get("ref_cliente", ""),
        "condiciones_pago_inicial": row.get("condiciones_pago", ""),
        "condiciones_presupuesto_inicial": datos.get("condiciones_presupuesto", ""),
        "items_precargados":        [
            {"desc": i["descripcion"], "pu": i["precio_unitario"],
             "cant": i["cantidad"], "iva": i["iva_pct"]}
            for i in items
        ],
    })

@app.post("/editar/{numero}")
async def editar_generar(numero: str, request: Request):
    import json as _json
    form_data = await request.form()
    clientes  = db.load_clientes()

    cliente_id = form_data.get("cliente_id", "").strip()
    if cliente_id and cliente_id.isdigit():
        cliente = next((c for c in clientes if str(c["codigo"]) == cliente_id), None)
        if not cliente:
            return HTMLResponse("<h3>Error: cliente no encontrado.</h3>", status_code=400)
    else:
        nombre_nuevo = form_data.get("cliente_nombre", "").strip()
        existente = db.buscar_cliente_por_nombre(nombre_nuevo)
        if existente:
            cliente = existente
        else:
            return HTMLResponse("<h3>Error: cliente no encontrado.</h3>", status_code=400)

    descripciones = form_data.getlist("desc[]")
    precios       = form_data.getlist("pu[]")
    cantidades    = form_data.getlist("cant[]")
    ivas          = form_data.getlist("iva[]")
    items = []
    for desc, pu, cant, iva in zip(descripciones, precios, cantidades, ivas):
        if not desc.strip():
            continue
        items.append({
            "descripcion":     desc.strip(),
            "precio_unitario": float(pu or 0),
            "cantidad":        int(cant or 1),
            "iva_pct":         float(iva or 21),
        })

    ref = form_data.get("ref", "").strip()
    datos = {
        "numero":                    numero,
        "ref_cliente":               ref,
        "fecha":                     form_data.get("fecha", ""),
        "fecha_validez":             form_data.get("validez", ""),
        "codigo_cliente":            f"C-{cliente['codigo']:04d}",
        "moneda":                    form_data.get("moneda", "ARS"),
        "condiciones_pago":          form_data.get("condiciones_pago", ""),
        "condiciones_presupuesto":   form_data.get("condiciones_presupuesto", ""),
        "cliente":                   cliente,
        "items":                     items,
    }

    nombre_archivo = f"{numero} - {ref}.pdf" if ref else f"{numero}.pdf"
    output_path    = os.path.join("presupuestos", "output", nombre_archivo)

    from presupuestos.generar_pdf import generar_presupuesto
    generar_presupuesto(datos, output_path)

    drive_link = None
    try:
        import drive as drive_mod
        drive_link = drive_mod.subir_presupuesto(
            pdf_path       = output_path,
            nombre_archivo = nombre_archivo,
            codigo_cliente = cliente["codigo"],
            nombre_cliente = cliente["nombre"],
        )
    except Exception as e:
        import traceback
        print(f"[Drive] Error al subir PDF (editar): {e}\n{traceback.format_exc()}")

    db.actualizar_historial(numero, datos, nombre_archivo, drive_link=drive_link)

    return FileResponse(output_path, media_type="application/pdf", filename=nombre_archivo)

@app.get("/reutilizar/{numero}", response_class=HTMLResponse)
async def reutilizar_form(numero: str, request: Request):
    import json as _json
    historial = db.load_historial()
    row = next((r for r in historial if str(r["numero"]) == numero), None)
    if not row:
        return HTMLResponse(f"<h3>Presupuesto {numero} no encontrado.</h3>", status_code=404)

    datos_json = row.get("datos_json", "")
    datos = {}
    if datos_json:
        try:
            datos = _json.loads(datos_json)
        except Exception:
            pass

    cliente = datos.get("cliente", {})
    items   = datos.get("items", [])
    hoy     = date.today()
    validez = hoy + timedelta(days=30)

    return templates.TemplateResponse("nuevo_presupuesto.html", {
        "request":                  request,
        "fecha":                    hoy.strftime("%Y-%m-%d"),
        "validez":                  validez.strftime("%Y-%m-%d"),
        "numero":                   db.peek_numero(),
        "edit_mode":                False,
        "cliente_id":               str(cliente.get("codigo", "")),
        "cliente_nombre":           cliente.get("nombre", row.get("cliente_nombre", "")),
        "cliente_cuit":             cliente.get("cuit", ""),
        "cliente_direccion":        cliente.get("direccion", ""),
        "cliente_ciudad":           cliente.get("ciudad", ""),
        "moneda_inicial":           row.get("moneda", "USD"),
        "ref_inicial":              row.get("ref_cliente", ""),
        "condiciones_pago_inicial": row.get("condiciones_pago", ""),
        "condiciones_presupuesto_inicial": datos.get("condiciones_presupuesto", ""),
        "items_precargados":        [
            {"desc": i["descripcion"], "pu": i["precio_unitario"],
             "cant": i["cantidad"], "iva": i["iva_pct"]}
            for i in items
        ],
    })

@app.get("/nuevo", response_class=HTMLResponse)
async def form(request: Request):
    hoy     = date.today()
    validez = hoy + timedelta(days=30)
    numero  = db.peek_numero()
    params  = dict(request.query_params)

    # Pre-carga desde matriz de cálculo
    items_precargados = []
    if params.get("from_matriz"):
        descs    = request.query_params.getlist("desc[]")
        precios  = request.query_params.getlist("pu[]")
        cantids  = request.query_params.getlist("cant[]")
        ivas     = request.query_params.getlist("iva[]")
        for d, p, c, i in zip(descs, precios, cantids, ivas):
            items_precargados.append({"desc": d, "pu": p, "cant": c, "iva": i})

    return templates.TemplateResponse("nuevo_presupuesto.html", {
        "request":           request,
        "fecha":             hoy.strftime("%Y-%m-%d"),
        "validez":           validez.strftime("%Y-%m-%d"),
        "numero":            numero,
        "cliente_nombre":    params.get("cliente_nombre", ""),
        "moneda_inicial":    params.get("moneda", "USD"),
        "items_precargados": items_precargados,
    })

@app.get("/pdf/{nombre_archivo:path}")
async def ver_pdf(nombre_archivo: str):
    path = os.path.join("presupuestos", "output", nombre_archivo)
    if not os.path.exists(path):
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "PDF no encontrado"}, status_code=404)
    return FileResponse(path, media_type="application/pdf", filename=nombre_archivo)

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
        if not cliente:
            return HTMLResponse("<h3>Error: cliente no encontrado. Volvé atrás e intentá de nuevo.</h3>", status_code=400)
        if form_data.get("cliente_cuit"):
            cliente["cuit"] = form_data.get("cliente_cuit", "")
            db.actualizar_cuit(cliente_id, cliente["cuit"])
    else:
        nombre_nuevo = form_data.get("cliente_nombre", "").strip()
        if not nombre_nuevo:
            return HTMLResponse(
                "<h3>Error: ingresá el nombre del cliente antes de generar.</h3>"
                "<p><a href='/nuevo'>← Volver</a></p>",
                status_code=400
            )
        # Reusar cliente si ya existe con ese nombre (evita duplicados)
        existente = db.buscar_cliente_por_nombre(nombre_nuevo)
        if existente:
            cliente = existente
            if form_data.get("cliente_cuit"):
                cliente["cuit"] = form_data.get("cliente_cuit", "")
                db.actualizar_cuit(str(cliente["codigo"]), cliente["cuit"])
        else:
            codigo  = db.next_codigo_cliente()
            cliente = {
                "codigo":    codigo,
                "nombre":    nombre_nuevo,
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
        "condiciones_pago":           form_data.get("condiciones_pago", ""),
        "condiciones_presupuesto":    form_data.get("condiciones_presupuesto", ""),
        "cliente":          cliente,
        "items":            items,
    }

    nombre_archivo = f"{numero} - {ref}.pdf" if ref else f"{numero}.pdf"
    output_path    = os.path.join("presupuestos", "output", nombre_archivo)

    from presupuestos.generar_pdf import generar_presupuesto
    generar_presupuesto(datos, output_path)

    # Subir a Google Drive
    drive_link = None
    try:
        import drive as drive_mod
        drive_link = drive_mod.subir_presupuesto(
            pdf_path       = output_path,
            nombre_archivo = nombre_archivo,
            codigo_cliente = cliente["codigo"],
            nombre_cliente = cliente["nombre"],
        )
    except Exception as e:
        import traceback
        print(f"[Drive] Error al subir PDF: {e}\n{traceback.format_exc()}")

    db.guardar_historial(datos, nombre_archivo, drive_link=drive_link)

    return FileResponse(output_path, media_type="application/pdf", filename=nombre_archivo)


# ── PIPELINE — cambio de estado ───────────────────────────────────────────────
@app.post("/api/rechazar/{numero}")
async def rechazar(numero: str):
    ok = db.actualizar_estado(numero, "rechazado")
    if ok:
        historial = db.load_historial()
        row = next((r for r in historial if str(r["numero"]) == numero), None)
        if row and row.get("archivo"):
            try:
                import drive as drive_mod, json as _json
                clientes = db.load_clientes()
                datos_json = row.get("datos_json", "")
                codigo = None
                nombre = row.get("cliente_nombre", "")
                if datos_json:
                    datos = _json.loads(datos_json)
                    codigo = datos.get("cliente", {}).get("codigo")
                if not codigo:
                    cod_str = row.get("codigo_cliente", "").replace("C-", "")
                    codigo = int(cod_str) if cod_str.isdigit() else None
                if codigo:
                    drive_mod.mover_a_rechazados(row["archivo"], codigo, nombre)
            except Exception as e:
                import traceback
                print(f"[Drive] Error al mover a Rechazados: {e}\n{traceback.format_exc()}")
    return JSONResponse({"ok": ok})


@app.post("/api/aprobar/{numero}")
async def aprobar(
    numero: str,
    oc_numero: str = Form(""),
    oc_fecha: str = Form(""),
    oc_monto: str = Form(""),
    archivo: Optional[UploadFile] = File(None),
):
    drive_link = ""
    if archivo and archivo.filename:
        tmp = f"presupuestos/output/OC_{numero}_{archivo.filename}"
        with open(tmp, "wb") as f:
            shutil.copyfileobj(archivo.file, f)
        try:
            import drive as drive_mod
            # Extraer codigo_cliente del historial
            historial = db.load_historial()
            p = next((x for x in historial if str(x["numero"]) == numero), {})
            cod = str(p.get("codigo_cliente", "")).replace("C-", "")
            nombre_cli = p.get("cliente_nombre", "")
            drive_link = drive_mod.subir_documento(
                pdf_path=tmp, nombre_archivo=archivo.filename,
                codigo_cliente=cod, nombre_cliente=nombre_cli,
                subcarpeta="Ordenes de Compra",
            )
        except Exception as e:
            print(f"[Drive] Error OC: {e}")

    ok = db.guardar_oc(numero, oc_numero, oc_fecha, oc_monto, drive_link)
    return JSONResponse({"ok": ok, "drive_link": drive_link})


@app.post("/api/facturar/{numero}")
async def facturar(
    numero: str,
    fact_numero: str = Form(""),
    fact_fecha: str = Form(""),
    fact_vto_pago: str = Form(""),
    fact_monto: str = Form(""),
    archivo: Optional[UploadFile] = File(None),
):
    drive_link = ""
    if archivo and archivo.filename:
        tmp = f"presupuestos/output/FAC_{numero}_{archivo.filename}"
        with open(tmp, "wb") as f:
            shutil.copyfileobj(archivo.file, f)
        try:
            import drive as drive_mod
            historial = db.load_historial()
            p = next((x for x in historial if str(x["numero"]) == numero), {})
            cod = str(p.get("codigo_cliente", "")).replace("C-", "")
            nombre_cli = p.get("cliente_nombre", "")
            drive_link = drive_mod.subir_documento(
                pdf_path=tmp, nombre_archivo=archivo.filename,
                codigo_cliente=cod, nombre_cliente=nombre_cli,
                subcarpeta="Facturas",
            )
        except Exception as e:
            print(f"[Drive] Error FAC: {e}")

    db.guardar_factura(numero, fact_numero, fact_fecha, fact_vto_pago, fact_monto, drive_link)
    db.actualizar_estado(numero, "facturado")
    return JSONResponse({"ok": True, "drive_link": drive_link})


@app.post("/api/cobrar/{numero}")
async def cobrar(
    numero: str,
    fact_numero: str = Form(""),
    op_numero: str = Form(""),
    op_fecha: str = Form(""),
    op_monto_bruto: str = Form(""),
    ret_ganancias: str = Form("0"),
    ret_iibb: str = Form("0"),
    ret_seghigiene: str = Form("0"),
    ret_otros: str = Form("0"),
    archivo_op: Optional[UploadFile] = File(None),
    archivo_ret1: Optional[UploadFile] = File(None),
    archivo_ret2: Optional[UploadFile] = File(None),
):
    historial = db.load_historial()
    p = next((x for x in historial if str(x["numero"]) == numero), {})
    cod = str(p.get("codigo_cliente", "")).replace("C-", "")
    nombre_cli = p.get("cliente_nombre", "")

    def _subir(upl, prefijo):
        if not upl or not upl.filename:
            return ""
        tmp = f"presupuestos/output/{prefijo}_{numero}_{upl.filename}"
        with open(tmp, "wb") as f:
            shutil.copyfileobj(upl.file, f)
        try:
            import drive as drive_mod
            return drive_mod.subir_documento(
                pdf_path=tmp, nombre_archivo=upl.filename,
                codigo_cliente=cod, nombre_cliente=nombre_cli,
                subcarpeta="Ordenes de Pago",
            )
        except Exception as e:
            print(f"[Drive] Error {prefijo}: {e}")
            return ""

    op_link   = _subir(archivo_op,   "OP")
    ret1_link = _subir(archivo_ret1, "RET1")
    ret2_link = _subir(archivo_ret2, "RET2")

    ok = db.guardar_cobro(
        numero, fact_numero, op_numero, op_fecha, op_monto_bruto,
        ret_ganancias, ret_iibb, ret_seghigiene, ret_otros,
        op_link, ret1_link, ret2_link,
    )
    return JSONResponse({"ok": ok})


@app.get("/api/facturas/{numero}")
async def get_facturas(numero: str):
    return db.load_facturas_por_presupuesto(numero)


# ── MATRICES DE CÁLCULO ───────────────────────────────────────────────────────
@app.get("/matrices", response_class=HTMLResponse)
async def lista_matrices(request: Request):
    matrices = db.load_matrices()
    return templates.TemplateResponse("matrices.html", {
        "request": request,
        "matrices": list(reversed(matrices)),
    })

@app.get("/matriz/nueva", response_class=HTMLResponse)
async def nueva_matriz(request: Request):
    return templates.TemplateResponse("matriz.html", {
        "request": request,
        "matriz": None,
        "proximo_numero": db.peek_numero(),
    })

@app.get("/matriz/{mid}", response_class=HTMLResponse)
async def ver_matriz(request: Request, mid: str):
    matriz = db.load_matriz(mid)
    if not matriz:
        return HTMLResponse("<h3>Matriz no encontrada.</h3>", status_code=404)
    return templates.TemplateResponse("matriz.html", {
        "request": request,
        "matriz": matriz,
        "proximo_numero": db.peek_numero(),
    })

@app.post("/api/matriz/guardar")
async def api_guardar_matriz(request: Request):
    import json as _json
    body = await request.json()
    mid = body.get("id")
    nombre       = body.get("nombre", "Sin nombre")
    cliente      = body.get("cliente_nombre", "")
    moneda       = body.get("moneda", "USD")
    datos        = body.get("datos", {})
    proveedores  = body.get("proveedores", [])

    # Guardar proveedores nuevos para autocomplete
    for prv in proveedores:
        if prv.get("nombre"):
            db.guardar_proveedor(prv["nombre"], prv.get("entrega", ""))

    if mid:
        db.actualizar_matriz(mid, nombre, cliente, moneda, datos)
        return JSONResponse({"ok": True, "id": int(mid)})
    else:
        nuevo_id = db.guardar_matriz(nombre, cliente, moneda, datos)
        return JSONResponse({"ok": True, "id": nuevo_id})

@app.get("/api/proveedores")
async def api_proveedores(q: str = ""):
    prvs = db.load_proveedores()
    q = q.lower()
    return [p for p in prvs if q in p["nombre"].lower()][:10]
