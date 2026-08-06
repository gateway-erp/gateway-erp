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
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=name, rows=1000, cols=len(headers))
        ws.append_row(headers)
    return ws


# ── CLIENTES ──────────────────────────────────────────────────────────────────
_H_CLI = ["codigo", "nombre", "cuit", "direccion", "ciudad"]

def load_clientes():
    return _ws("clientes", _H_CLI).get_all_records()

def crear_cliente(cliente):
    ws = _ws("clientes", _H_CLI)
    ws.append_row([
        cliente["codigo"],
        cliente["nombre"],
        cliente.get("cuit", ""),
        cliente.get("direccion", ""),
        cliente.get("ciudad", ""),
    ])

def actualizar_cuit(codigo, cuit):
    ws = _ws("clientes", _H_CLI)
    for i, r in enumerate(ws.get_all_records(), start=2):
        if str(r["codigo"]) == str(codigo):
            ws.update_cell(i, _H_CLI.index("cuit") + 1, cuit)
            break

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
_H_HIS = ["numero", "ref_cliente", "fecha", "fecha_validez", "codigo_cliente",
          "moneda", "condiciones_pago", "cliente_nombre", "archivo", "estado"]

def guardar_historial(datos, nombre_archivo):
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
        "generado",
    ])
