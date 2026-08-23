"""
Módulo de integración con Google Drive.
- Carpetas: service account (no consumen cuota)
- Archivos PDF: OAuth del usuario (cuenta contra su cuota, no la del bot)
"""

import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as UserCredentials
from google.auth.transport.requests import Request

DRIVE_ROOT_ID = os.environ.get("DRIVE_FOLDER_ID", "14UwyCzQ0CvKF6vFQHEeqfWiHbs2PoMwI")
SCOPES = ["https://www.googleapis.com/auth/drive"]


def _service():
    """Service account: para operaciones de carpeta (no consumen cuota)."""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        info = json.loads(creds_json)
    else:
        with open("credentials.json") as f:
            info = json.load(f)
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _user_service():
    """
    OAuth del usuario real: para subir archivos (cuenta contra su cuota de Drive).
    Requiere las env vars GOOGLE_USER_REFRESH_TOKEN, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET.
    Si no están configuradas, cae al service account (fallback, puede fallar por cuota).
    """
    refresh_token = os.environ.get("GOOGLE_USER_REFRESH_TOKEN")
    client_id     = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

    if not refresh_token:
        print("[Drive] GOOGLE_USER_REFRESH_TOKEN no configurado, usando service account (puede fallar por cuota)")
        return _service()

    creds = UserCredentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _buscar_carpeta(service, nombre, parent_id):
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
    meta = {
        "name": nombre,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    carpeta = service.files().create(body=meta, fields="id").execute()
    return carpeta["id"]


def _obtener_o_crear(service, nombre, parent_id):
    folder_id = _buscar_carpeta(service, nombre, parent_id)
    if not folder_id:
        folder_id = _crear_carpeta(service, nombre, parent_id)
    return folder_id


def subir_presupuesto(pdf_path, nombre_archivo, codigo_cliente, nombre_cliente):
    """
    Sube el PDF a:
      Documentos/ → Clientes/ → C-XXXX - Nombre/ → Presupuestos/

    Carpetas: service account | Archivo: OAuth del usuario
    """
    # Carpetas con service account (sin cuota)
    svc_bot = _service()
    clientes_id = _obtener_o_crear(svc_bot, "Clientes", DRIVE_ROOT_ID)
    nombre_carpeta_cliente = f"C-{int(codigo_cliente):04d} - {nombre_cliente}"
    cliente_id = _obtener_o_crear(svc_bot, nombre_carpeta_cliente, clientes_id)
    presup_id  = _obtener_o_crear(svc_bot, "Presupuestos", cliente_id)

    # Subida del PDF con cuenta del usuario (tiene cuota)
    svc_user = _user_service()
    media = MediaFileUpload(pdf_path, mimetype="application/pdf", resumable=False)
    archivo = svc_user.files().create(
        body={"name": nombre_archivo, "parents": [presup_id]},
        media_body=media,
        fields="id",
    ).execute()

    file_id = archivo["id"]
    svc_user.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()

    return f"https://drive.google.com/file/d/{file_id}/view"


def subir_documento(pdf_path, nombre_archivo, codigo_cliente, nombre_cliente, subcarpeta="Presupuestos"):
    """Sube cualquier documento a la estructura de Drive."""
    svc_bot = _service()
    clientes_id = _obtener_o_crear(svc_bot, "Clientes", DRIVE_ROOT_ID)
    nombre_carpeta_cliente = f"C-{int(codigo_cliente):04d} - {nombre_cliente}"
    cliente_id = _obtener_o_crear(svc_bot, nombre_carpeta_cliente, clientes_id)
    sub_id = _obtener_o_crear(svc_bot, subcarpeta, cliente_id)

    svc_user = _user_service()
    media = MediaFileUpload(pdf_path, mimetype="application/pdf", resumable=False)
    archivo = svc_user.files().create(
        body={"name": nombre_archivo, "parents": [sub_id]},
        media_body=media,
        fields="id",
    ).execute()

    file_id = archivo["id"]
    svc_user.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()

    return f"https://drive.google.com/file/d/{file_id}/view"
