"""
TEST DE COMENTARIO AUTOMÁTICO — UN SOLO ALUMNO
================================================
Abre la entrega del alumno elegido en Chrome y pega el comentario con pyautogui.
Usalo para verificar que el pegado automático funciona antes de correr el lote completo.
"""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from flujo_completo_correccion import pegar_comentario_en_classroom, copiar_texto_portapapeles
import webbrowser
import time

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
COURSE_ID   = "851018360586"   # Sist. Operativos
WORK_ID     = "851018360619"   # TP7
BUSCAR_NOMBRE = "german"       # parte del nombre del alumno (insensible a mayúsculas)

COMENTARIO_PRUEBA = (
    "✅ PRUEBA AUTOMÁTICA — Este comentario fue pegado automáticamente "
    "por el sistema de corrección. Si lo ves acá, el pegado funciona correctamente."
)
# ──────────────────────────────────────────────────────────────────────────────

creds   = Credentials.from_authorized_user_file("token.json")
service = build("classroom", "v1", credentials=creds)

# Buscar el alumno por nombre
print(f"\n🔍 Buscando alumno que contenga '{BUSCAR_NOMBRE}'...")
subs = service.courses().courseWork().studentSubmissions().list(
    courseId=COURSE_ID, courseWorkId=WORK_ID, pageSize=50
).execute().get("studentSubmissions", [])

# Obtener nómina para nombres
roster = service.courses().students().list(courseId=COURSE_ID, pageSize=100).execute()
mapa = {
    s["userId"]: s.get("profile", {}).get("name", {}).get("fullName", "?")
    for s in roster.get("students", [])
}

alumno_encontrado = None
for sub in subs:
    nombre = mapa.get(sub.get("userId"), "").lower()
    if BUSCAR_NOMBRE.lower() in nombre:
        alumno_encontrado = {
            "nombre": mapa.get(sub.get("userId"), "?"),
            "submission_id": sub.get("id"),
            "alternate_link": sub.get("alternateLink"),
            "user_id": sub.get("userId"),
        }
        break

if not alumno_encontrado:
    print(f"❌ No se encontró ningún alumno con '{BUSCAR_NOMBRE}' en el curso.")
    print("   Alumnos disponibles:")
    for sub in subs[:10]:
        print(f"   - {mapa.get(sub.get('userId'), sub.get('userId'))}")
    exit(1)

nombre   = alumno_encontrado["nombre"]
link     = alumno_encontrado["alternate_link"]
user_id  = alumno_encontrado["user_id"]

# Construir URL web si el link es de la API
if not link or "classroom.googleapis.com" in (link or ""):
    link = (
        f"https://classroom.google.com/c/{COURSE_ID}"
        f"/a/{WORK_ID}/submissions/by-status/and-sort-last-name"
        f"/student/{user_id}"
    )

print(f"\n✅ Alumno encontrado: {nombre}")
print(f"   Link: {link}")
print(f"\n📋 Comentario a pegar:")
print(f"   {COMENTARIO_PRUEBA}")

print(f"\n{'='*55}")
print(f"  INSTRUCCIONES:")
print(f"  1. Presioná Enter → Chrome abre la entrega")
print(f"  2. Tenés 5 segundos para hacer clic en")
print(f"     'Agregar comentario privado' (panel derecho)")
print(f"  3. El script pega solo con Ctrl+V + Ctrl+Enter")
print(f"{'='*55}")
input("\n  👉 Presioná Enter cuando estés listo...")

webbrowser.open(link)

print(f"\n  ⏳ Abriendo Chrome... tenés 5 segundos para hacer clic en el cuadro de comentario...")
exito = pegar_comentario_en_classroom(COMENTARIO_PRUEBA, delay_inicial=5.0)

if exito:
    print(f"\n  ✅ Comentario pegado y enviado.")
    print(f"     Verificá en Classroom que aparezca el comentario de prueba.")
    print(f"     Si lo ves, el sistema funciona para todos los alumnos.")
else:
    print(f"\n  ⚠️ pyautogui no disponible o falló el pegado.")
    print(f"     Instalá pyautogui: pip install pyautogui")
    # Fallback: copiar al portapapeles
    if copiar_texto_portapapeles(COMENTARIO_PRUEBA):
        print(f"     El comentario fue copiado al portapapeles — pegalo con Ctrl+V.")
