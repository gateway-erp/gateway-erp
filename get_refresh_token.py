"""
Ejecutar UNA SOLA VEZ en tu PC para obtener el refresh token de Google.
Requiere: pip install google-auth-oauthlib

Pasos:
1. Ve a https://console.cloud.google.com/apis/credentials
2. Proyecto: gateway-erp-504713
3. Crear credencial → ID de cliente OAuth 2.0 → Aplicación de escritorio
4. Descargar JSON → guardarlo como client_secret.json en esta misma carpeta
5. Ejecutar: python get_refresh_token.py
6. Se abrirá el navegador → aceptar con servidorgatewaycampana@gmail.com
7. Copiar el refresh_token que aparece en consola → pegarlo en Render como GOOGLE_USER_REFRESH_TOKEN
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=0)

print("\n=== COPIÁ ESTOS VALORES A RENDER ===")
print(f"GOOGLE_USER_REFRESH_TOKEN={creds.refresh_token}")

# Guardar también en archivo por si acaso
with open("user_token.json", "w") as f:
    json.dump({
        "refresh_token": creds.refresh_token,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
    }, f, indent=2)
print("\nTambién guardado en user_token.json")
print("(NO subas user_token.json a git)")
