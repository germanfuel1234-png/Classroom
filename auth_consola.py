"""
Auth OAuth por consola: sin localhost, sin callback.
Te da un URL, autorizás en el browser, copiás el código y lo pegás acá.
"""
import os, json
from dotenv import load_dotenv
load_dotenv()

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

CREDENTIALS_FILE = "classroom_nuevo.json"
TOKEN_FILE       = "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.topics.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students",
    "https://www.googleapis.com/auth/classroom.profile.emails",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

if os.path.exists(TOKEN_FILE):
    os.remove(TOKEN_FILE)
    print("✅ Token viejo borrado.")

flow = InstalledAppFlow.from_client_secrets_file(
    CREDENTIALS_FILE, SCOPES,
    redirect_uri="urn:ietf:wg:oauth:2.0:oob"
)

auth_url, _ = flow.authorization_url(
    prompt="consent",
    access_type="offline",
    login_hint="germanrodriguezciclo2026@gmail.com",
)

print("\n" + "="*70)
print("  Abrí este URL en tu navegador y autorizá:")
print("="*70)
print(f"\n{auth_url}\n")
print("="*70)

code = input("\nPegá aquí el código que te dio Google: ").strip()
flow.fetch_token(code=code)
creds = flow.credentials

with open(TOKEN_FILE, "w") as f:
    f.write(creds.to_json())

print(f"\n✅ Token guardado en {TOKEN_FILE}")
print("   Ahora podés correr: python explorar_entregas.py")
