import ssl, json, os
from datetime import date

# Workaround Python 3.12+: urllib3 es más estricto con TLS EOF.
# oauth2.googleapis.com cierra la conexión sin close_notify y eso rompe la auth.
# Parcheamos create_urllib3_context para agregar OP_IGNORE_UNEXPECTED_EOF.
if hasattr(ssl, "OP_IGNORE_UNEXPECTED_EOF"):
    import urllib3.util.ssl_ as _u3ssl
    _orig_ctx = _u3ssl.create_urllib3_context
    def _patched_ctx(*args, **kwargs):
        ctx = _orig_ctx(*args, **kwargs)
        ctx.options |= ssl.OP_IGNORE_UNEXPECTED_EOF
        return ctx
    _u3ssl.create_urllib3_context = _patched_ctx

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SPREADSHEET_ID = "1dGgARZE2Ow-4yibOX6IM1mNd6VOLSmrPS1F4SceYrYI"

_gc = None

def _client():
    global _gc
    if _gc is None:
        creds_json = os.environ.get("GOOGLE_CREDENTIALS")
        if creds_json:
            info = json.loads(creds_json)
        else:
            with open("credentials.json") as f:
                info = json.load(f)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        _gc = gspread.authorize(creds)
    return _gc

def _ws(name, headers):
    sh = _client().open_by_key(SPREADSHEET_ID)
    try:
        ws = sh.worksheet(name)
        current = ws.row_values(1)
        nuevas = [h for h in headers if h not in current]
        if nuevas:
            # Expandir la hoja si faltan columnas
            needed_cols = len(headers)
            if ws.col_count < needed_cols:
                ws.resize(rows=ws.row_count, cols=needed_cols)
            for i, h in enumerate(headers):
                if h not in current:
                    ws.update_cell(1, i + 1, h)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=name, rows=1000, cols=len(headers))
        ws.append_row(headers)
    return ws


# ── CLIENTES ──────────────────────────────────────────────────────────────────
_H_CLI = ["codigo", "nombre", "cuit", "direccion", "ciudad"]

_cache_clientes = {"data": None, "ts": 0}

def load_clientes():
    import time
    if _cache_clientes["data"] is not None and time.time() - _cache_clientes["ts"] < 300:
        return _cache_clientes["data"]
    data = _ws("clientes", _H_CLI).get_all_records()
    _cache_clientes["data"] = data
    _cache_clientes["ts"]   = time.time()
    return data

def _invalidar_cache_clientes():
    _cache_clientes["data"] = None

def buscar_cliente_por_nombre(nombre):
    """Retorna el cliente si ya existe con ese nombre (case-insensitive), o None."""
    nombre_lower = nombre.strip().lower()
    for c in load_clientes():
        if str(c.get("nombre", "")).strip().lower() == nombre_lower:
            return c
    return None

def crear_cliente(cliente):
    ws = _ws("clientes", _H_CLI)
    ws.append_row([
        cliente["codigo"],
        cliente["nombre"],
        cliente.get("cuit", ""),
        cliente.get("direccion", ""),
        cliente.get("ciudad", ""),
    ])
    _invalidar_cache_clientes()

def crear_cliente_nuevo(nombre, cuit="", direccion="", ciudad=""):
    """Crea un cliente auto-asignando el próximo código. Retorna el código asignado."""
    clientes = load_clientes()
    codigos = [int(c.get("codigo", 0)) for c in clientes if str(c.get("codigo","")).isdigit()]
    nuevo_codigo = max(codigos, default=0) + 1
    crear_cliente({"codigo": nuevo_codigo, "nombre": nombre, "cuit": cuit, "direccion": direccion, "ciudad": ciudad})
    return nuevo_codigo

def actualizar_cuit(codigo, cuit):
    ws = _ws("clientes", _H_CLI)
    for i, r in enumerate(ws.get_all_records(), start=2):
        if str(r["codigo"]) == str(codigo):
            ws.update_cell(i, _H_CLI.index("cuit") + 1, cuit)
            break

def actualizar_cliente(codigo, nombre, cuit, direccion, ciudad):
    ws = _ws("clientes", _H_CLI)
    for i, r in enumerate(ws.get_all_records(), start=2):
        if str(r["codigo"]) == str(codigo):
            ws.update_cell(i, _H_CLI.index("nombre") + 1,    nombre)
            ws.update_cell(i, _H_CLI.index("cuit") + 1,      cuit)
            ws.update_cell(i, _H_CLI.index("direccion") + 1, direccion)
            ws.update_cell(i, _H_CLI.index("ciudad") + 1,    ciudad)
            _invalidar_cache_clientes()
            return True
    return False

def next_codigo_cliente():
    records = load_clientes()
    if not records:
        return 1
    return max(r["codigo"] for r in records) + 1


# ── ÍTEMS SUGERIDOS ───────────────────────────────────────────────────────────
_H_ITE = ["descripcion", "precio_unitario", "iva_pct"]

def load_items():
    return _ws("items_sugeridos", _H_ITE).get_all_records()

def guardar_item(item):
    ws = _ws("items_sugeridos", _H_ITE)
    ws.append_row([item["descripcion"], item["precio_unitario"], item["iva_pct"]])


# ── NUMERACIÓN ────────────────────────────────────────────────────────────────
_H_CNT = ["prefix", "valor"]

def _prefix_hoy():
    t = date.today()
    return f"PR{str(t.year)[2:]}{t.month:02d}"

def peek_numero():
    prefix = _prefix_hoy()
    ws = _ws("counters", _H_CNT)
    for r in ws.get_all_records():
        if r["prefix"] == prefix:
            return f"{prefix}-{(r['valor'] + 1):04d}"
    return f"{prefix}-0001"

def next_numero():
    prefix = _prefix_hoy()
    ws = _ws("counters", _H_CNT)
    records = ws.get_all_records()
    for i, r in enumerate(records, start=2):
        if r["prefix"] == prefix:
            nuevo = r["valor"] + 1
            ws.update_cell(i, 2, nuevo)
            return f"{prefix}-{nuevo:04d}"
    ws.append_row([prefix, 1])
    return f"{prefix}-0001"


# ── HISTORIAL ─────────────────────────────────────────────────────────────────
_H_HIS = [
    "numero", "ref_cliente", "fecha", "fecha_validez", "codigo_cliente",
    "moneda", "condiciones_pago", "cliente_nombre", "archivo", "estado", "total", "drive_link",
    "oc_numero", "oc_fecha", "oc_monto", "oc_drive_link", "datos_json",
]

def guardar_historial(datos, nombre_archivo, drive_link=None):
    import json as _json
    items = datos.get("items", [])
    base  = sum(i["precio_unitario"] * i["cantidad"] for i in items)
    iva   = sum(i["precio_unitario"] * i["cantidad"] * i["iva_pct"] / 100 for i in items)
    total = round(base + iva, 2)

    ws = _ws("historial", _H_HIS)
    ws.append_row([
        datos["numero"],
        datos["ref_cliente"],
        datos["fecha"],
        datos["fecha_validez"],
        datos["codigo_cliente"],
        datos["moneda"],
        datos["condiciones_pago"],
        datos["cliente"]["nombre"],
        nombre_archivo,
        "enviado",
        total,
        drive_link or "",
        "", "", "", "",  # OC columns vacíos
        _json.dumps(datos, ensure_ascii=False),
    ])

def actualizar_historial(numero, datos, nombre_archivo, drive_link=None):
    import json as _json
    items = datos.get("items", [])
    base  = sum(i["precio_unitario"] * i["cantidad"] for i in items)
    iva   = sum(i["precio_unitario"] * i["cantidad"] * i["iva_pct"] / 100 for i in items)
    total = round(base + iva, 2)

    ws = _ws("historial", _H_HIS)
    for i, r in enumerate(ws.get_all_records(), start=2):
        if str(r["numero"]) == str(numero):
            ws.update_cell(i, _H_HIS.index("ref_cliente") + 1,   datos["ref_cliente"])
            ws.update_cell(i, _H_HIS.index("fecha") + 1,         datos["fecha"])
            ws.update_cell(i, _H_HIS.index("fecha_validez") + 1, datos["fecha_validez"])
            ws.update_cell(i, _H_HIS.index("moneda") + 1,        datos["moneda"])
            ws.update_cell(i, _H_HIS.index("condiciones_pago") + 1, datos["condiciones_pago"])
            ws.update_cell(i, _H_HIS.index("archivo") + 1,       nombre_archivo)
            ws.update_cell(i, _H_HIS.index("total") + 1,         total)
            ws.update_cell(i, _H_HIS.index("datos_json") + 1,    _json.dumps(datos, ensure_ascii=False))
            if drive_link:
                ws.update_cell(i, _H_HIS.index("drive_link") + 1, drive_link)
            return True
    return False

def eliminar_presupuesto(numero):
    ws = _ws("historial", _H_HIS)
    for i, r in enumerate(ws.get_all_records(), start=2):
        if str(r["numero"]) == str(numero):
            ws.delete_rows(i)
            return True
    return False

def load_historial():
    return _ws("historial", _H_HIS).get_all_records()

def actualizar_estado(numero, estado):
    ws = _ws("historial", _H_HIS)
    col = _H_HIS.index("estado") + 1
    for i, r in enumerate(ws.get_all_records(), start=2):
        if str(r["numero"]) == str(numero):
            ws.update_cell(i, col, estado)
            return True
    return False

def guardar_oc(numero, oc_numero, oc_fecha, oc_monto, oc_drive_link=""):
    ws = _ws("historial", _H_HIS)
    records = ws.get_all_records()
    for i, r in enumerate(records, start=2):
        if str(r["numero"]) == str(numero):
            col_base = _H_HIS.index("oc_numero") + 1
            ws.update_cell(i, col_base,     oc_numero)
            ws.update_cell(i, col_base + 1, oc_fecha)
            ws.update_cell(i, col_base + 2, oc_monto)
            ws.update_cell(i, col_base + 3, oc_drive_link)
            ws.update_cell(i, _H_HIS.index("estado") + 1, "aprobado")
            return True
    return False


# ── FACTURAS ──────────────────────────────────────────────────────────────────
_H_FAC = [
    "presupuesto_numero", "fact_numero", "fact_fecha", "fact_vto_pago", "fact_monto",
    "fact_drive_link", "op_numero", "op_fecha", "op_monto_bruto",
    "ret_ganancias", "ret_iibb", "ret_seghigiene", "ret_otros",
    "op_monto_neto", "op_drive_link", "ret_drive_link_1", "ret_drive_link_2", "cobro_ok",
]

def load_facturas():
    return _ws("facturas", _H_FAC).get_all_records()

def load_facturas_por_presupuesto(numero):
    return [f for f in load_facturas() if str(f["presupuesto_numero"]) == str(numero)]

def guardar_factura(presupuesto_numero, fact_numero, fact_fecha, fact_vto_pago, fact_monto, fact_drive_link=""):
    ws = _ws("facturas", _H_FAC)
    ws.append_row([
        presupuesto_numero, fact_numero, fact_fecha, fact_vto_pago, fact_monto,
        fact_drive_link, "", "", "",
        "", "", "", "",
        "", "", "", "", "no",
    ])

def guardar_cobro(presupuesto_numero, fact_numero, op_numero, op_fecha, op_monto_bruto,
                  ret_ganancias, ret_iibb, ret_seghigiene, ret_otros,
                  op_drive_link="", ret_drive_link_1="", ret_drive_link_2=""):
    ws = _ws("facturas", _H_FAC)
    op_monto_neto = round(
        float(op_monto_bruto or 0)
        - float(ret_ganancias or 0)
        - float(ret_iibb or 0)
        - float(ret_seghigiene or 0)
        - float(ret_otros or 0),
        2
    )
    for i, r in enumerate(ws.get_all_records(), start=2):
        if (str(r["presupuesto_numero"]) == str(presupuesto_numero)
                and str(r["fact_numero"]) == str(fact_numero)):
            col_op = _H_FAC.index("op_numero") + 1
            ws.update_cell(i, col_op,      op_numero)
            ws.update_cell(i, col_op + 1,  op_fecha)
            ws.update_cell(i, col_op + 2,  op_monto_bruto)
            col_ret = _H_FAC.index("ret_ganancias") + 1
            ws.update_cell(i, col_ret,     ret_ganancias)
            ws.update_cell(i, col_ret + 1, ret_iibb)
            ws.update_cell(i, col_ret + 2, ret_seghigiene)
            ws.update_cell(i, col_ret + 3, ret_otros)
            col_neto = _H_FAC.index("op_monto_neto") + 1
            ws.update_cell(i, col_neto,     op_monto_neto)
            ws.update_cell(i, col_neto + 1, op_drive_link)
            ws.update_cell(i, col_neto + 2, ret_drive_link_1)
            ws.update_cell(i, col_neto + 3, ret_drive_link_2)
            ws.update_cell(i, _H_FAC.index("cobro_ok") + 1, "si")
            return True
    return False

# ── PROVEEDORES ───────────────────────────────────────────────────────────────
_H_PRV = ["nombre", "entrega"]

def load_proveedores():
    return _ws("proveedores", _H_PRV).get_all_records()

def guardar_proveedor(nombre, entrega=""):
    existentes = {r["nombre"].strip().lower() for r in load_proveedores()}
    if nombre.strip().lower() not in existentes:
        _ws("proveedores", _H_PRV).append_row([nombre.strip(), entrega.strip()])


# ── MATRICES DE CÁLCULO ───────────────────────────────────────────────────────
_H_MAT = ["id", "nombre", "fecha", "cliente_nombre", "moneda", "datos_json"]

def _next_matriz_id():
    records = _ws("matrices", _H_MAT).get_all_records()
    if not records:
        return 1
    return max(int(r["id"]) for r in records if str(r["id"]).isdigit()) + 1

def guardar_matriz(nombre, cliente_nombre, moneda, datos_json):
    import json as _json
    mid = _next_matriz_id()
    _ws("matrices", _H_MAT).append_row([
        mid, nombre, date.today().isoformat(),
        cliente_nombre, moneda,
        _json.dumps(datos_json, ensure_ascii=False),
    ])
    return mid

def actualizar_matriz(mid, nombre, cliente_nombre, moneda, datos_json):
    import json as _json
    ws = _ws("matrices", _H_MAT)
    for i, r in enumerate(ws.get_all_records(), start=2):
        if str(r["id"]) == str(mid):
            ws.update_cell(i, 2, nombre)
            ws.update_cell(i, 4, cliente_nombre)
            ws.update_cell(i, 5, moneda)
            ws.update_cell(i, 6, _json.dumps(datos_json, ensure_ascii=False))
            return True
    return False

def load_matrices():
    import json as _json
    rows = _ws("matrices", _H_MAT).get_all_records()
    result = []
    for r in rows:
        try:
            r["datos"] = _json.loads(r["datos_json"]) if r.get("datos_json") else {}
        except Exception:
            r["datos"] = {}
        result.append(r)
    return result

def load_matriz(mid):
    import json as _json
    for r in _ws("matrices", _H_MAT).get_all_records():
        if str(r["id"]) == str(mid):
            try:
                r["datos"] = _json.loads(r["datos_json"]) if r.get("datos_json") else {}
            except Exception:
                r["datos"] = {}
            return r
    return None


# ── AGENDA ────────────────────────────────────────────────────────────────────
_H_AGENDA_CEL = ["año", "mes", "dia", "turno", "texto", "color", "negrita"]

def load_agenda_celdas(año, mes):
    ws = _ws("agenda_celdas", _H_AGENDA_CEL)
    return [r for r in ws.get_all_records()
            if str(r.get("año")) == str(año) and str(r.get("mes")) == str(mes)]

def guardar_celda_agenda(año, mes, dia, turno, texto, color, negrita):
    ws = _ws("agenda_celdas", _H_AGENDA_CEL)
    records = ws.get_all_records()
    for i, r in enumerate(records, start=2):
        if (str(r.get("año")) == str(año) and str(r.get("mes")) == str(mes)
                and str(r.get("dia")) == str(dia) and str(r.get("turno")) == turno):
            ws.update_cell(i, _H_AGENDA_CEL.index("texto") + 1, texto)
            ws.update_cell(i, _H_AGENDA_CEL.index("color") + 1, color)
            ws.update_cell(i, _H_AGENDA_CEL.index("negrita") + 1, "si" if negrita else "no")
            return
    ws.append_row([año, mes, dia, turno, texto, color, "si" if negrita else "no"])


_H_MANT = ["id", "nombre", "cliente", "horas_plan", "semanas_mes"]
_mant_seeded = False

def load_mantenimientos():
    return _ws("mantenimientos", _H_MANT).get_all_records()

def crear_mantenimiento_if_missing():
    global _mant_seeded
    if _mant_seeded:
        return
    ws = _ws("mantenimientos", _H_MANT)
    records = ws.get_all_records()
    if not any(str(r.get("nombre")) == "TBAR CCTV" for r in records):
        ws.append_row([1, "TBAR CCTV", "Toyota Boshoku", 8, 4])
    _mant_seeded = True


# ── REMITOS ───────────────────────────────────────────────────────────────────
_H_REM = ["numero", "fecha", "entrega", "cuit_dest", "domicilio", "items_json", "archivo", "drive_link"]

def _next_remito_numero():
    from datetime import date as _date
    prefix = f"REM{str(_date.today().year)[2:]}{_date.today().month:02d}"
    ws = _ws("remitos", _H_REM)
    records = ws.get_all_records()
    maxn = 0
    for r in records:
        n = str(r.get("numero", ""))
        if n.startswith(prefix):
            try:
                maxn = max(maxn, int(n.split("-")[-1]))
            except ValueError:
                pass
    return f"{prefix}-{maxn+1:04d}"

def guardar_remito(numero, fecha, entrega, cuit_dest, domicilio, items, archivo, drive_link=""):
    import json as _json
    _ws("remitos", _H_REM).append_row([
        numero, fecha, entrega, cuit_dest, domicilio,
        _json.dumps(items, ensure_ascii=False), archivo, drive_link,
    ])

def load_remitos():
    import json as _json
    rows = _ws("remitos", _H_REM).get_all_records()
    result = []
    for r in rows:
        try:
            r["items"] = _json.loads(r.get("items_json") or "[]")
        except Exception:
            r["items"] = []
        result.append(r)
    return result


_H_MVIS = ["mant_id", "año", "mes", "semana", "fecha_real", "estado"]

def load_visitas_mes(año, mes):
    ws = _ws("mant_visitas", _H_MVIS)
    return [r for r in ws.get_all_records()
            if str(r.get("año")) == str(año) and str(r.get("mes")) == str(mes)]

def guardar_visita(mant_id, año, mes, semana, fecha_real, estado):
    ws = _ws("mant_visitas", _H_MVIS)
    records = ws.get_all_records()
    for i, r in enumerate(records, start=2):
        if (str(r.get("mant_id")) == str(mant_id) and str(r.get("año")) == str(año)
                and str(r.get("mes")) == str(mes) and str(r.get("semana")) == str(semana)):
            ws.update_cell(i, _H_MVIS.index("fecha_real") + 1, fecha_real)
            ws.update_cell(i, _H_MVIS.index("estado") + 1, estado)
            return
    ws.append_row([mant_id, año, mes, semana, fecha_real, estado])


def presupuesto_cobrado_ok(numero):
    facturas = load_facturas_por_presupuesto(numero)
    if not facturas:
        return None  # sin facturas registradas
    return all(str(f.get("cobro_ok", "no")).lower() == "si" for f in facturas)
