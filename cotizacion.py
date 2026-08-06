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
        return float(s.replace(".", "").replace(",", ".").strip())
    except Exception:
        return None

def _scrape():
    resultado = {
        "billete": {"compra": None, "venta": None},
        "divisa":  {"compra": None, "venta": None},
        "fecha":   None,
        "hora":    None,
        "error":   None,
    }
    try:
        r = requests.get("https://www.bna.com.ar/Personas", headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # BNA tiene dos tablas: una para billetes y otra para divisas
        tablas = soup.select("table.table")

        for tabla in tablas:
            filas = tabla.select("tr")
            for fila in filas:
                celdas = [td.get_text(strip=True) for td in fila.select("td")]
                if not celdas:
                    continue
                nombre = celdas[0].lower()
                if "dolar" in nombre or "u.s" in nombre or "usa" in nombre:
                    compra = _parse_num(celdas[1]) if len(celdas) > 1 else None
                    venta  = _parse_num(celdas[2]) if len(celdas) > 2 else None

                    # Determinar si es billetes o divisas por el contexto del thead
                    thead = tabla.find_previous("h2") or tabla.find_previous("h3") or tabla.find_previous("div", class_="col-sm-4")
                    titulo = thead.get_text(strip=True).lower() if thead else ""

                    if "billete" in titulo and resultado["billete"]["venta"] is None:
                        resultado["billete"]["compra"] = compra
                        resultado["billete"]["venta"]  = venta
                    elif "divisa" in titulo and resultado["divisa"]["venta"] is None:
                        resultado["divisa"]["compra"] = compra
                        resultado["divisa"]["venta"]  = venta

        # Intentar sacar fecha/hora de actualización
        hora_tag = soup.find(string=lambda t: t and "Hora Actualización" in t)
        if hora_tag:
            resultado["hora"] = hora_tag.strip().replace("Hora Actualización:", "").strip()

        fecha_tag = soup.find("td", string=lambda t: t and "/" in str(t) and len(str(t)) < 12)
        if fecha_tag:
            resultado["fecha"] = fecha_tag.get_text(strip=True)
        else:
            resultado["fecha"] = datetime.now().strftime("%d/%m/%Y")

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
