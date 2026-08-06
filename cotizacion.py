import requests
from datetime import datetime, timedelta

_cache = {"data": None, "expires": datetime.min}

HEADERS = {"User-Agent": "Mozilla/5.0"}

def _fetch_tipo(tipo_slug):
    """Consulta dolarapi.com para un tipo de dólar. Retorna dict con compra/venta o None."""
    try:
        r = requests.get(f"https://dolarapi.com/v1/dolares/{tipo_slug}", headers=HEADERS, timeout=8)
        r.raise_for_status()
        d = r.json()
        return {"compra": d.get("compra"), "venta": d.get("venta")}
    except Exception:
        return None

def _scrape():
    resultado = {
        "billete": {"compra": None, "venta": None},
        "divisa":  {"compra": None, "venta": None},
        "fecha":   datetime.now().strftime("%d/%m/%Y"),
        "hora":    datetime.now().strftime("%H:%M"),
        "error":   None,
    }
    try:
        # dolarapi.com expone los tipos del BNA:
        #   "oficial"  → Dólar Billete BNA
        #   "mayorista" → Dólar Divisa BNA (tipo de cambio de referencia BCRA / divisas)
        billete = _fetch_tipo("oficial")
        divisa  = _fetch_tipo("mayorista")

        if billete:
            resultado["billete"] = billete
        if divisa:
            resultado["divisa"] = divisa

        if not billete and not divisa:
            resultado["error"] = "No se pudo obtener la cotización"

    except Exception as e:
        resultado["error"] = str(e)

    return resultado


def get_cotizacion():
    global _cache
    if _cache["data"] and datetime.now() < _cache["expires"]:
        return _cache["data"]
    data = _scrape()
    _cache["data"]    = data
    _cache["expires"] = datetime.now() + timedelta(minutes=30)
    return data
