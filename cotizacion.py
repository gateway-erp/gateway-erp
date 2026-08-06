import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

_cache = {"data": None, "expires": datetime.min}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "es-AR,es;q=0.9",
}

def _parse_num(s):
    try:
        return float(s.strip().replace(".", "").replace(",", "."))
    except Exception:
        return None

def _scrape():
    resultado = {
        "billete": {"compra": None, "venta": None},
        "divisa":  {"compra": None, "venta": None},
        "fecha":   datetime.now().strftime("%d/%m/%Y"),
        "hora":    None,
        "error":   None,
    }
    try:
        r = requests.get("https://www.bna.com.ar/Personas", headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Recolectar todos los pares (compra, venta) de filas con "dólar"
        # filtrando valores absurdos (> 100.000 son claramente erróneos para USD/ARS)
        pares = []
        vistas = set()  # evitar duplicados exactos

        for tr in soup.find_all("tr"):
            celdas = tr.find_all("td")
            if len(celdas) < 3:
                continue
            nombre = celdas[0].get_text(strip=True).lower()
            if not ("dolar" in nombre or "dólar" in nombre or "u.s" in nombre):
                continue
            compra = _parse_num(celdas[1].get_text(strip=True))
            venta  = _parse_num(celdas[2].get_text(strip=True))
            if not compra or not venta:
                continue
            if compra > 100_000 or venta > 100_000:
                continue
            clave = (compra, venta)
            if clave in vistas:
                continue
            vistas.add(clave)
            pares.append({"compra": compra, "venta": venta})

        # El BNA muestra primero Billetes y luego Divisas en el HTML
        if len(pares) >= 1:
            resultado["billete"]["compra"] = pares[0]["compra"]
            resultado["billete"]["venta"]  = pares[0]["venta"]
        if len(pares) >= 2:
            resultado["divisa"]["compra"] = pares[1]["compra"]
            resultado["divisa"]["venta"]  = pares[1]["venta"]

        # Si solo hay un par, replicarlo en divisa (mejor que mostrar vacío)
        if len(pares) == 1:
            resultado["divisa"] = dict(resultado["billete"])

        # Hora de actualización
        hora_tag = soup.find(string=lambda t: t and "Hora Actualización" in str(t))
        if hora_tag:
            resultado["hora"] = str(hora_tag).replace("Hora Actualización:", "").strip()

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
