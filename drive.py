"""
Módulo de integración con Google Drive.
Sube PDFs a la estructura: Documentos/Clientes/C-XXXX - Nombre/Presupuestos/
"""

import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

DRIVE_ROOT_ID = os.environ.get("DRIVE_FOLDER_ID", "14UwyCzQ0CvKF6vFQHEeqfWiHbs2PoMwI")
SCOPES = ["https://www.googleapis.com/auth/drive"]

def _service():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        info = json.loads(creds_json)
    else:
        with open("credentials.json") as f:
            info = json.load(f)
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _buscar_carpeta(service, nombre, parent_id):
    """Retorna el ID de una carpeta si existe, o None."""
    nombre_esc = nombre.replace("'", "\\'")
    q = (
        f"name='{nombre_esc}' and "
        f"'{parent_id}' in parents and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"trashed=false"
    )
    res = service.files().list(q=q, fields="files(id)").execute()
    archivos = res.get("files", [])
    return archivos[0]["id"] if archivos else None


def _crear_carpeta(service, nombre, parent_id):
    """Crea una carpeta y retorna su ID."""
    meta = {
        "name": nombre,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    carpeta = service.files().create(body=meta, fields="id").execute()
    return carpeta["id"]


def _obtener_o_crear(service, nombre, parent_id):
    """Busca la carpeta; si no existe la crea."""
    folder_id = _buscar_carpeta(service, nombre, parent_id)
    if not folder_id:
        folder_id = _crear_carpeta(service, nombre, parent_id)
    return folder_id


def subir_documento(pdf_path, nombre_archivo, codigo_cliente, nombre_cliente, subcarpeta="Presupuestos"):
    """
    Sube cualquier documento a:
      Documentos/ → Clientes/ → C-XXXX - Nombre/ → {subcarpeta}/
    """
    service = _service()
    clientes_id = _obtener_o_crear(service, "Clientes", DRIVE_ROOT_ID)
    nombre_carpeta_cliente = f"C-{int(codigo_cliente):04d} - {nombre_cliente}"
    cliente_id = _obtener_o_crear(service, nombre_carpeta_cliente, clientes_id)
    sub_id = _obtener_o_crear(service, subcarpeta, cliente_id)

    media = MediaFileUpload(pdf_path, mimetype="application/pdf", resumable=False)
    archivo = service.files().create(
        body={"name": nombre_archivo, "parents": [sub_id]},
        media_body=media,
        fields="id",
    ).execute()
    file_id = archivo["id"]
    service.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()
    return f"https://drive.google.com/file/d/{file_id}/view"


def subir_presupuesto(pdf_path, nombre_archivo, codigo_cliente, nombre_cliente):
    """
    Sube el PDF a:
      Documentos/ → Clientes/ → C-XXXX - Nombre/ → Presupuestos/

    Retorna el link directo de Drive para abrir el PDF.
    """
    service = _service()

    # Carpeta Clientes (dentro de la raíz Documentos)
    clientes_id = _obtener_o_crear(service, "Clientes", DRIVE_ROOT_ID)

    # Carpeta del cliente: "C-0001 - TOYOTA BOSHOKU"
    nombre_carpeta_cliente = f"C-{int(codigo_cliente):04d} - {nombre_cliente}"
    cliente_id = _obtener_o_crear(service, nombre_carpeta_cliente, clientes_id)

    # Subcarpeta Presupuestos
    presup_id = _obtener_o_crear(service, "Presupuestos", cliente_id)

    # Subir el PDF
    media = MediaFileUpload(pdf_path, mimetype="application/pdf", resumable=False)
    archivo = service.files().create(
        body={"name": nombre_archivo, "parents": [presup_id]},
        media_body=media,
        fields="id",
    ).execute()

    file_id = archivo["id"]

    # Hacer el archivo accesible con el link (cualquiera con el link puede ver)
    service.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()

    link = f"https://drive.google.com/file/d/{file_id}/view"
    return link
