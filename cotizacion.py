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

def _dolar_de_tabla(tabla):
    """Devuelve (compra, venta) del dólar en una tabla, o (None, None)."""
    for tr in tabla.find_all("tr"):
        celdas = tr.find_all("td")
        if len(celdas) < 3:
            continue
        nombre = celdas[0].get_text(strip=True).lower()
        if "dolar" in nombre or "dólar" in nombre or "u.s" in nombre:
            compra = _parse_num(celdas[1].get_text(strip=True))
            venta  = _parse_num(celdas[2].get_text(strip=True))
            if compra and venta and compra < 100_000 and venta < 100_000:
                return compra, venta
    return None, None

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

        # Estrategia: buscar los contenedores que tienen "Billete" y "Divisa" en su heading
        secciones = {"billete": None, "divisa": None}

        # Intentar por encabezados h2/h3/h4 o divs con el texto
        for heading in soup.find_all(["h2", "h3", "h4", "th", "div", "span"]):
            txt = heading.get_text(strip=True).lower()
            if "billete" in txt and secciones["billete"] is None:
                # Buscar la tabla más cercana después de este heading
                tabla = heading.find_next("table")
                if tabla:
                    secciones["billete"] = tabla
            elif "divisa" in txt and secciones["divisa"] is None:
                tabla = heading.find_next("table")
                if tabla:
                    secciones["divisa"] = tabla

        # Extraer valores de cada sección
        for tipo, tabla in secciones.items():
            if tabla is None:
                continue
            compra, venta = _dolar_de_tabla(tabla)
            if compra and venta:
                resultado[tipo]["compra"] = compra
                resultado[tipo]["venta"]  = venta

        # Fallback: si siguen vacíos, tomar las dos primeras tablas de la página en orden
        if resultado["billete"]["venta"] is None and resultado["divisa"]["venta"] is None:
            tablas = soup.find_all("table")
            pares = []
            for t in tablas:
                c, v = _dolar_de_tabla(t)
                if c and v:
                    pares.append((c, v))
                if len(pares) == 2:
                    break
            if len(pares) >= 1:
                resultado["billete"]["compra"] = pares[0][0]
                resultado["billete"]["venta"]  = pares[0][1]
            if len(pares) >= 2:
                resultado["divisa"]["compra"] = pares[1][0]
                resultado["divisa"]["venta"]  = pares[1][1]

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
