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

        # Buscar todas las filas de la página que contengan "Dólar" o "Dollar"
        dollar_rows = []
        for tr in soup.find_all("tr"):
            celdas = tr.find_all("td")
            if not celdas:
                continue
            texto = celdas[0].get_text(strip=True).lower()
            if "dolar" in texto or "dólar" in texto or "u.s" in texto or "dollar" in texto:
                compra = _parse_num(celdas[1].get_text(strip=True)) if len(celdas) > 1 else None
                venta  = _parse_num(celdas[2].get_text(strip=True)) if len(celdas) > 2 else None
                if compra and venta:
                    dollar_rows.append({"compra": compra, "venta": venta, "tr": tr})

        # Asignar por orden de aparición: primera = billete, segunda = divisa
        # También intentar detectar por contexto del contenedor
        for row in dollar_rows:
            tr = row["tr"]
            # Subir en el DOM buscando un encabezado que identifique la sección
            seccion = ""
            node = tr.parent  # tbody o table
            while node and node.name not in ("body", "html"):
                # buscar el hermano/ancestro anterior con texto de sección
                prev = node.find_previous_sibling()
                if prev:
                    txt = prev.get_text(" ", strip=True).lower()
                    if "billete" in txt:
                        seccion = "billete"
                        break
                    if "divisa" in txt:
                        seccion = "divisa"
                        break
                # también buscar h2/h3/h4 cerca
                for tag in ("h2", "h3", "h4", "h5", "div"):
                    heading = node.find_previous(tag)
                    if heading:
                        txt = heading.get_text(strip=True).lower()
                        if "billete" in txt:
                            seccion = "billete"
                            break
                        if "divisa" in txt:
                            seccion = "divisa"
                            break
                if seccion:
                    break
                node = node.parent

            if seccion == "billete" and resultado["billete"]["venta"] is None:
                resultado["billete"]["compra"] = row["compra"]
                resultado["billete"]["venta"]  = row["venta"]
            elif seccion == "divisa" and resultado["divisa"]["venta"] is None:
                resultado["divisa"]["compra"] = row["compra"]
                resultado["divisa"]["venta"]  = row["venta"]

        # Fallback: si no se pudo detectar por sección, usar orden de aparición
        if resultado["billete"]["venta"] is None and resultado["divisa"]["venta"] is None:
            if len(dollar_rows) >= 1:
                resultado["billete"]["compra"] = dollar_rows[0]["compra"]
                resultado["billete"]["venta"]  = dollar_rows[0]["venta"]
            if len(dollar_rows) >= 2:
                resultado["divisa"]["compra"] = dollar_rows[1]["compra"]
                resultado["divisa"]["venta"]  = dollar_rows[1]["venta"]
        elif resultado["billete"]["venta"] is None and len(dollar_rows) >= 1:
            # Tenemos divisa pero no billete — asignar la primera fila encontrada
            for row in dollar_rows:
                if row["compra"] != resultado["divisa"]["compra"]:
                    resultado["billete"]["compra"] = row["compra"]
                    resultado["billete"]["venta"]  = row["venta"]
                    break

        # Fecha/hora
        resultado["fecha"] = datetime.now().strftime("%d/%m/%Y")
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
