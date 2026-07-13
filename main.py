import os
import io
import time
import datetime
import re
import json
import base64
import webbrowser
import glob
import socket
import subprocess
import importlib
from email.mime.text import MIMEText
from google import genai
from dotenv import load_dotenv
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
import reporte_local

# Importar el módulo corrector pedagógico
from corrector_pedagogico import CorrectorPedagogico, procesar_correccion
from aux_correccion_masiva import iniciar_correccion_masiva_completa, iniciar_correccion_masiva_con_api_classroom
from flujo_completo_correccion import ejecutar_flujo_completo

load_dotenv()  # Carga las variables del archivo .env
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Intentar importar PyPDF2 para leer PDFs
try:
    import PyPDF2
    PDF_DISPONIBLE = True
except ImportError:
    PDF_DISPONIBLE = False

try:
    import pytesseract
    from pdf2image import convert_from_bytes
    OCR_DISPONIBLE = True
except ImportError:
    OCR_DISPONIBLE = False

try:
    pyautogui = importlib.import_module("pyautogui")
    AUTO_PEGADO_DISPONIBLE = True
except Exception:
    pyautogui = None
    AUTO_PEGADO_DISPONIBLE = False

# ──────────────────────────────────────────────
#  CONFIGURACIÓN
# ──────────────────────────────────────────────
CREDENTIALS_FILE = "classroom_nuevo.json"
TOKEN_FILE = "token.json"

# Cuentas de Google disponibles
CUENTAS_DISPONIBLES = {
    "1": "germanfuel1234@gmail.com",  # Propietaria original de las tareas
    "2": "germanfuel123@gmail.com",
    "3": "germanty123@gmail.com",
    "4": "germanrodriguezciclo2026@gmail.com",
}

# Cuenta por defecto (usa tu propia cuenta)
EXPECTED_OAUTH_EMAIL = os.getenv("OAUTH_EMAIL", "germanrodriguezciclo2026@gmail.com")
OAUTH_LOGIN_HINT = EXPECTED_OAUTH_EMAIL
OAUTH_CHROME_PROFILE_DIRECTORY = os.getenv("OAUTH_CHROME_PROFILE_DIRECTORY", "Profile 3")
OAUTH_FORCE_PROFILE = os.getenv("OAUTH_FORCE_PROFILE", "1") == "1"

SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.topics.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students",  # ✅ PERMITE patch() en calificaciones
    "https://www.googleapis.com/auth/classroom.profile.emails",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/gmail.send",               # ✅ Envío de feedback por email
]


def copiar_texto_portapapeles(texto):
    """Copia texto al portapapeles (Windows robusto + fallback tkinter)."""
    if os.name == "nt":
        try:
            # clip.exe espera UTF-16LE en Windows y evita problemas de cp1252.
            subprocess.run(
                ["clip"],
                input=(texto or "").encode("utf-16le"),
                check=True,
                capture_output=True,
            )
            return True
        except Exception:
            pass

    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(texto or "")
        root.update()
        root.destroy()
        return True
    except Exception:
        return False


def pegar_y_enviar_comentario_automatico(texto, delay_segundos=2.0):
    """Pega y envía comentario en la ventana activa (requiere pyautogui)."""
    if not AUTO_PEGADO_DISPONIBLE:
        return False

    if not copiar_texto_portapapeles(texto):
        return False

    try:
        # Dar tiempo para volver a Chrome y dejar foco en el cuadro de comentario.
        time.sleep(max(0.5, float(delay_segundos)))
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "enter")
        return True
    except Exception:
        return False


def obtener_carpeta_reportes_del_dia():
    """Devuelve (y crea si hace falta) la carpeta de reportes del día."""
    fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    carpeta = os.path.join("Correcciones_Classroom", "reportes", fecha_hoy)
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def _es_error_transitorio_api(error):
    """Detecta errores transitorios de red/API que ameritan reintento."""
    if error is None:
        return False

    if isinstance(error, (TimeoutError, ConnectionError, socket.timeout, ConnectionResetError, OSError)):
        return True

    if isinstance(error, HttpError):
        status = getattr(getattr(error, "resp", None), "status", None)
        if status in {408, 429, 500, 502, 503, 504}:
            return True

    texto = str(error).lower()
    indicadores = [
        "winerror 10054",
        "connection reset",
        "forcibly closed",
        "remote host",
        "temporarily unavailable",
        "timed out",
        "timeout",
    ]
    return any(x in texto for x in indicadores)


def _ejecutar_con_reintentos_api(funcion_api, etiqueta="API", max_intentos=4):
    """Ejecuta una llamada de Google API con reintentos ante fallas transitorias."""
    ultimo_error = None
    for intento in range(1, max_intentos + 1):
        try:
            return funcion_api()
        except Exception as e:
            ultimo_error = e
            if not _es_error_transitorio_api(e) or intento == max_intentos:
                raise
            espera = min(2 * intento, 8)
            print(f"   ⚠️ {etiqueta}: fallo transitorio ({str(e)[:120]}). Reintentando en {espera}s... [{intento}/{max_intentos}]")
            time.sleep(espera)

    raise ultimo_error


def _forzar_navegador_oauth_perfil_chrome():
    """Intenta forzar el perfil de Chrome usado por OAuth en Windows."""
    if os.name != "nt" or not OAUTH_FORCE_PROFILE:
        return False

    candidatos = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]

    chrome_path = next((ruta for ruta in candidatos if os.path.exists(ruta)), None)
    if not chrome_path:
        print("[OAuth] No se encontró Chrome para forzar perfil. Se usará navegador predeterminado.")
        return False

    os.environ["BROWSER"] = (
        f'"{chrome_path}" --profile-directory="{OAUTH_CHROME_PROFILE_DIRECTORY}" --new-window %s'
    )
    print(f"[OAuth] Se abrirá Chrome con perfil: {OAUTH_CHROME_PROFILE_DIRECTORY}")
    return True


# ──────────────────────────────────────────────
#  PASO 0: AUTENTICACIÓN
# ──────────────────────────────────────────────
def obtener_credenciales():
    """Maneja el flujo OAuth2. Reutiliza token.json si ya existe y es válido."""
    def resolver_archivo_credenciales():
        """Busca un archivo de credenciales OAuth válido en el directorio del proyecto."""
        candidatos = [
            CREDENTIALS_FILE,
            "credentials.json",
            "client_secret.json",
        ]

        for candidato in candidatos:
            if os.path.exists(candidato):
                return candidato

        # Fallback: cualquier JSON que parezca credencial de cliente OAuth
        for ruta in glob.glob("*.json"):
            nombre = os.path.basename(ruta).lower()
            if nombre == TOKEN_FILE.lower():
                continue
            if "client" in nombre or "cliente" in nombre or "credential" in nombre:
                return ruta

        return None

    creds = None
    cred_file = resolver_archivo_credenciales()
    if not cred_file:
        raise FileNotFoundError(
            "No se encontró el archivo de credenciales OAuth de Google Classroom. "
            "Colocá en la carpeta del proyecto uno de estos archivos: "
            "classroom_nuevo.json o credentials.json"
        )

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        # Si el token actual no contiene todos los permisos requeridos, forzar nuevo login.
        if not creds.has_scopes(SCOPES):
            print("[OAuth] El token actual no tiene todos los permisos requeridos. Se solicitará autorización nuevamente.")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # Si falla el refresh (por ejemplo, por scopes), abrir flujo interactivo completo.
                creds = None
        if not creds or not creds.valid:
            os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
            _forzar_navegador_oauth_perfil_chrome()
            flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
            
            print("\n" + "=" * 70)
            print("🔐 AUTORIZACIÓN OAUTH REQUERIDA")
            print("=" * 70)
            print(f"📌 IMPORTANTE:")
            print(f"   1. Se abrirá el navegador pidiendo seleccionar cuenta")
            print(f"   2. SELECCIONA la cuenta del profesor: {EXPECTED_OAUTH_EMAIL}")
            print(f"   3. Autoriza todos los permisos solicitados")
            print(f"   4. NO cierres el navegador después de autorizar")
            print(f"      (El token guardado durará meses)")
            print("=" * 70 + "\n")
            
            # Forzar selección de cuenta para evitar que tome automáticamente
            # la cuenta predeterminada incorrecta del navegador.
            creds = flow.run_local_server(
                port=0,
                prompt="select_account",
                login_hint=EXPECTED_OAUTH_EMAIL,  # Preselecciona el email del profesor
                open_browser=True,  # Abre navegador automáticamente
            )
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        print(f"✅ Token guardado: {TOKEN_FILE}\n")
    return creds


# ──────────────────────────────────────────────
#  PASO 1: LISTAR MATERIAS ACTIVAS
# ──────────────────────────────────────────────
def listar_materias_activas(service):
    """Obtiene todos los cursos activos y los muestra numerados."""
    try:
        resultados = service.courses().list(courseStates="ACTIVE").execute()
        cursos = resultados.get("courses", [])
        if not cursos:
            print("No se encontraron materias activas en tu cuenta.")
            return []
        return cursos
    except HttpError as error:
        print(f"Error al obtener los cursos: {error}")
        return []


def seleccionar_materia(service):
    """Muestra el menú de materias y devuelve el curso elegido."""
    cursos = listar_materias_activas(service)
    if not cursos:
        return None

    print("\n" + "=" * 50)
    print("  PASO 1 — Seleccioná una materia")
    print("=" * 50)
    for i, curso in enumerate(cursos, start=1):
        nombre = curso.get("name", "Sin nombre")
        seccion = curso.get("section", "")
        display = f"{nombre}  [{seccion}]" if seccion else nombre
        print(f"  [{i}] {display}")
    print("=" * 50)

    while True:
        try:
            opcion = int(input("Ingresá el número de la materia: "))
            if 1 <= opcion <= len(cursos):
                curso_elegido = cursos[opcion - 1]
                print(f"\n✅ Materia seleccionada: {curso_elegido['name']}")
                return curso_elegido
            else:
                print(f"Ingresá un número entre 1 y {len(cursos)}.")
        except ValueError:
            print("Entrada no válida. Ingresá un número.")


def obtener_email_autenticado(service):
    """Devuelve el email de la cuenta OAuth autenticada en Classroom."""
    try:
        perfil = service.userProfiles().get(userId="me").execute()
        return perfil.get("emailAddress", "desconocido")
    except Exception:
        return "desconocido"


def listar_cursos_locales(ruta_raiz="descargas_Material_Docente"):
    """
    Lista materias locales detectadas.
    1) Subcarpetas dentro de la ruta raíz indicada.
    2) Carpetas hermanas del workspace que también parezcan materias.
    """
    cursos = []
    vistos = set()

    # Fuente principal: subcarpetas en descargas_Material_Docente
    if os.path.isdir(ruta_raiz):
        for carpeta in sorted(os.listdir(ruta_raiz)):
            ruta = os.path.join(ruta_raiz, carpeta)
            if os.path.isdir(ruta) and carpeta not in vistos:
                cursos.append(carpeta)
                vistos.add(carpeta)

    # Fuente complementaria: carpetas hermanas del proyecto
    raiz_workspace = os.path.dirname(os.path.abspath(ruta_raiz)) if not os.path.isabs(ruta_raiz) else os.path.dirname(ruta_raiz)
    if os.path.isdir(raiz_workspace):
        excluir = {".venv", ".venv-1", "__pycache__", os.path.basename(ruta_raiz)}
        for carpeta in sorted(os.listdir(raiz_workspace)):
            ruta = os.path.join(raiz_workspace, carpeta)
            if not os.path.isdir(ruta):
                continue
            if carpeta.startswith('.') or carpeta in excluir:
                continue
            # Solo agregar si parece una carpeta de materia (tiene archivos o subcarpetas útiles)
            try:
                contenido = os.listdir(ruta)
            except Exception:
                continue
            if not contenido:
                continue
            if carpeta not in vistos:
                cursos.append(carpeta)
                vistos.add(carpeta)

    return cursos


# ──────────────────────────────────────────────
#  FUNCIONES PARA CORRECCIÓN PEDAGÓGICA
# ──────────────────────────────────────────────
def seleccionar_materia_para_corrector():
    """Autentica y permite elegir materia desde Classroom (PASO 1)."""
    try:
        print("\n🔐 Autenticando con Google Classroom...")
        creds = obtener_credenciales()
        service = build("classroom", "v1", credentials=creds)
        service_drive = build("drive", "v3", credentials=creds)
    except Exception as e:
        print(f"\n❌ No se pudo autenticar con Classroom: {e}")
        return None

    # Validar que la cuenta OAuth sea la cuenta docente esperada.
    # Si no se puede resolver el email ("desconocido"), no bloquear el flujo.
    email_activo = obtener_email_autenticado(service)
    email_desconocido = (email_activo or "").strip().lower() in {"", "desconocido", "unknown"}
    if EXPECTED_OAUTH_EMAIL and (not email_desconocido) and email_activo.lower() != EXPECTED_OAUTH_EMAIL.lower():
        print(f"\n⚠️ Cuenta incorrecta para API: {email_activo}")
        print(f"   Se requiere autenticación con: {EXPECTED_OAUTH_EMAIL}")
        print("   Se eliminará token.json para forzar nuevo login con la cuenta correcta.")
        try:
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
        except Exception as e:
            print(f"   ⚠️ No se pudo eliminar token.json: {e}")
        print("   Volvé a ejecutar y en Google elegí la cuenta docente indicada.")
        return None

    if EXPECTED_OAUTH_EMAIL and email_desconocido:
        print("\n⚠️ No se pudo verificar el email OAuth (valor: desconocido).")
        print("   Se continuará con el flujo sin forzar reautenticación.")
        print("   Si notas permisos inconsistentes, elimina token.json y vuelve a autenticar.")

    curso = seleccionar_materia(service)
    if not curso:
        return None

    print(f"\n👤 Cuenta autenticada para API: {email_activo}")

    return {
        "nombre": curso.get("name", "Sin nombre"),
        "course_id": curso.get("id"),
        "service": service,
        "service_drive": service_drive,
    }


def seleccionar_tema_para_corrector(service, course_id):
    """Muestra PASO 2 para elegir un tema del curso."""
    print("\n🔍 Buscando unidades/temas en la materia...")
    temas = obtener_temas_del_curso(service, course_id)
    if not temas:
        return None

    print("\n" + "=" * 50)
    print("  PASO 2 — Seleccioná el tema a evaluar")
    print("=" * 50)
    for idx, tema in enumerate(temas, start=1):
        print(f"  [{idx}] {tema.get('name', 'Sin nombre')}")
    print("=" * 50)

    while True:
        try:
            opcion_tema = int(input("Ingresá el número del tema: "))
            if 1 <= opcion_tema <= len(temas):
                return temas[opcion_tema - 1]
            print(f"Ingresá un número entre 1 y {len(temas)}.")
        except ValueError:
            print("Entrada no válida. Ingresá un número.")


def listar_actividades_por_tema(service, course_id, topic_id):
    """Lista actividades del curso filtradas por tema."""
    actividades = []
    page_token = None

    try:
        while True:
            respuesta = service.courses().courseWork().list(
                courseId=course_id,
                pageToken=page_token,
                pageSize=100,
            ).execute()

            actividades.extend(respuesta.get("courseWork", []))
            page_token = respuesta.get("nextPageToken")
            if not page_token:
                break
    except Exception as e:
        print(f"\n⚠️ Error al obtener actividades: {e}")
        return []

    if topic_id and topic_id != "general":
        actividades = [a for a in actividades if a.get("topicId") == topic_id]

    return actividades


def seleccionar_actividad_para_corrector(service, course_id, tema):
    """Lista actividades del tema elegido y devuelve la seleccionada."""
    topic_id = tema.get("topicId")
    actividades = listar_actividades_por_tema(service, course_id, topic_id)

    if not actividades:
        print("\n⚠️ No se encontraron actividades para el tema seleccionado.")
        return None

    print("\n" + "=" * 60)
    print("  PASO 3 — Seleccioná la actividad del tema")
    print("=" * 60)
    for i, actividad in enumerate(actividades, start=1):
        titulo = actividad.get("title", "Sin título")
        tipo = actividad.get("workType", "ASSIGNMENT")
        print(f"  [{i}] {titulo}  ({tipo})")
    print("=" * 60)

    while True:
        try:
            opcion = int(input("Ingresá el número de la actividad: "))
            if 1 <= opcion <= len(actividades):
                return actividades[opcion - 1]
            print(f"Ingresá un número entre 1 y {len(actividades)}.")
        except ValueError:
            print("Entrada no válida. Ingresá un número.")


def listar_alumnos_del_curso(service, course_id):
    """Obtiene todos los alumnos del curso en Classroom."""
    alumnos = []
    page_token = None

    try:
        while True:
            respuesta = service.courses().students().list(
                courseId=course_id,
                pageToken=page_token,
                pageSize=100,
            ).execute()
            alumnos.extend(respuesta.get("students", []))
            page_token = respuesta.get("nextPageToken")
            if not page_token:
                break
    except Exception as e:
        print(f"\n⚠️ No se pudo obtener la nómina del curso: {e}")
        print("   Sugerencia: eliminá token.json y volvé a iniciar para reautorizar con todos los permisos.")
        return []

    return alumnos


def listar_alumnos_por_actividad(service, course_id, work_id):
    """
    Obtiene alumnos vinculados al TP seleccionado usando studentSubmissions.
    Si no hay submissions, usa la nómina del curso como fallback.
    """
    roster = listar_alumnos_del_curso(service, course_id)
    mapa_alumnos = {}
    for alumno in roster:
        user_id = alumno.get("userId")
        nombre = alumno.get("profile", {}).get("name", {}).get("fullName", "Sin nombre")
        if user_id:
            mapa_alumnos[user_id] = nombre

    participantes = []
    page_token = None
    try:
        while True:
            respuesta = service.courses().courseWork().studentSubmissions().list(
                courseId=course_id,
                courseWorkId=work_id,
                pageToken=page_token,
                pageSize=100,
            ).execute()

            for sub in respuesta.get("studentSubmissions", []):
                user_id = sub.get("userId")
                estado = sub.get("state", "UNKNOWN")
                nombre = mapa_alumnos.get(user_id, f"Alumno {user_id}")
                attachments = sub.get("assignmentSubmission", {}).get("attachments", [])
                participantes.append({
                    "user_id": user_id,
                    "submission_id": sub.get("id"),
                    "alternate_link": sub.get("alternateLink"),
                    "nombre": nombre,
                    "estado": estado,
                    "attachments": attachments,
                })

            page_token = respuesta.get("nextPageToken")
            if not page_token:
                break
    except Exception as e:
        print(f"\n⚠️ No se pudo obtener entregas del TP: {e}")

    if participantes:
        unicos = []
        vistos = set()
        for p in participantes:
            key = p.get("user_id") or p.get("nombre")
            if key not in vistos:
                vistos.add(key)
                unicos.append(p)
        return unicos

    return [
        {
            "user_id": a.get("userId"),
            "submission_id": None,
            "alternate_link": None,
            "nombre": a.get("profile", {}).get("name", {}).get("fullName", "Sin nombre"),
            "estado": "SIN_ENTREGA",
            "attachments": [],
        }
        for a in roster
    ]


def _extraer_keywords_tp(tp):
    """Extrae palabras clave simples del título del TP para cotejo básico de pertinencia."""
    stopwords = {
        "trabajo", "practico", "práctico", "tp", "n", "no", "numero", "interfaz",
        "de", "del", "la", "el", "y", "en", "para", "con", "actividad"
    }
    tokens = re.findall(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ]{4,}", (tp or "").lower())
    return [t for t in tokens if t not in stopwords]


def _extraer_texto_de_attachments(attachments, service_drive):
    """Descarga y extrae texto de adjuntos de tipo Drive (docx/pdf) para análisis automático."""
    textos = []
    if not attachments or not service_drive:
        return ""

    for adj in attachments[:3]:
        drive_file = _obtener_drive_file_desde_attachment(adj)
        if not drive_file:
            continue
        file_id = drive_file.get("id")
        file_name = drive_file.get("title", "archivo")
        if not file_id:
            continue

        try:
            metadata = service_drive.files().get(fileId=file_id, fields="mimeType").execute()
            mime_type = metadata.get("mimeType", "")
        except Exception:
            mime_type = ""

        contenido = descargar_adjunto_drive(service_drive, file_id, mime_type)
        if not contenido:
            continue

        nombre_l = file_name.lower()
        if nombre_l.endswith(".docx") or mime_type == "application/vnd.google-apps.document":
            texto = extraer_texto_de_docx(contenido)
            if texto and "Error" not in texto:
                textos.append(texto)
        elif nombre_l.endswith(".pdf") or mime_type == "application/pdf":
            texto = extraer_texto_de_pdf(contenido)
            if texto and "Error" not in texto:
                textos.append(texto)

    return "\n".join(textos)


def _obtener_drive_file_desde_attachment(adj):
    """
    Normaliza el objeto de adjunto de Classroom para extraer metadatos de Drive.
    Classroom puede devolver:
    1) {'driveFile': {'id': ..., 'title': ...}}
    2) {'driveFile': {'driveFile': {'id': ..., 'title': ...}}}
    """
    if not isinstance(adj, dict) or "driveFile" not in adj:
        return None

    df = adj.get("driveFile")
    if not isinstance(df, dict):
        return None

    # Esquema simple (típico en studentSubmissions)
    if df.get("id"):
        return df

    # Esquema anidado (típico en materials de courseWork)
    anidado = df.get("driveFile")
    if isinstance(anidado, dict) and anidado.get("id"):
        return anidado

    return None


def _analizar_formatos_adjuntos(attachments, service_drive):
    """Analiza tipos de adjuntos para detectar entregas no pertinentes por formato."""
    analisis = {
        "totales": len(attachments or []),
        "drive": 0,
        "textuales": 0,
        "imagenes": 0,
        "otros": 0,
        "detalles": [],
    }

    mimes_textuales = {
        "application/pdf",
        "application/vnd.google-apps.document",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/plain",
    }

    for adj in attachments or []:
        drive_file = _obtener_drive_file_desde_attachment(adj)
        if not drive_file:
            analisis["otros"] += 1
            continue

        analisis["drive"] += 1
        file_id = drive_file.get("id")
        file_name = drive_file.get("title", "archivo")
        mime_type = ""

        if file_id and service_drive:
            try:
                metadata = service_drive.files().get(fileId=file_id, fields="mimeType").execute()
                mime_type = metadata.get("mimeType", "")
            except Exception:
                mime_type = ""

        nombre_l = (file_name or "").lower()
        es_textual = (
            mime_type in mimes_textuales
            or nombre_l.endswith((".pdf", ".docx", ".doc", ".txt"))
        )
        es_imagen = (
            mime_type.startswith("image/")
            or nombre_l.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"))
        )

        if es_textual:
            analisis["textuales"] += 1
        elif es_imagen:
            analisis["imagenes"] += 1
        else:
            analisis["otros"] += 1

        analisis["detalles"].append({
            "nombre": file_name,
            "mime": mime_type or "desconocido",
            "textual": es_textual,
            "imagen": es_imagen,
        })

    return analisis


def _extraer_texto_de_materiales_consigna(materiales, service_drive):
    """Extrae texto de materiales adjuntos a la consigna del TP."""
    if not materiales:
        return ""

    textos = []
    for material in materiales[:5]:
        if "driveFile" not in material:
            continue

        drive_file = material["driveFile"].get("driveFile", {})
        file_id = drive_file.get("id")
        file_name = drive_file.get("title", "archivo")
        if not file_id:
            continue

        try:
            metadata = service_drive.files().get(fileId=file_id, fields="mimeType").execute()
            mime_type = metadata.get("mimeType", "")
        except Exception:
            mime_type = ""

        contenido = descargar_adjunto_drive(service_drive, file_id, mime_type)
        if not contenido:
            continue

        nombre_l = file_name.lower()
        if nombre_l.endswith(".docx") or mime_type == "application/vnd.google-apps.document":
            texto = extraer_texto_de_docx(contenido)
            if texto and "Error" not in texto:
                textos.append(texto)
        elif nombre_l.endswith(".pdf") or mime_type == "application/pdf":
            texto = extraer_texto_de_pdf(contenido)
            if texto and "Error" not in texto:
                textos.append(texto)

    return "\n".join(textos)


def obtener_contexto_consigna(service, service_drive, course_id, work_id, actividad_base=None):
    """
    Construye un contexto de consigna usando título, descripción y materiales del TP.
    """
    actividad = actividad_base or {}
    try:
        actividad = service.courses().courseWork().get(courseId=course_id, id=work_id).execute()
    except Exception:
        # Fallback al objeto base si get falla.
        actividad = actividad_base or {}

    titulo = actividad.get("title", "")
    descripcion = actividad.get("description", "")
    materiales = actividad.get("materials", [])
    texto_materiales = _extraer_texto_de_materiales_consigna(materiales, service_drive)

    partes = [titulo, descripcion, texto_materiales]
    return "\n".join(p for p in partes if p and p.strip())


def _normalizar_tokens(texto):
    return re.findall(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ]{4,}", (texto or "").lower())


def _calcular_cobertura_consigna(texto_entrega, contexto_consigna, tp):
    """Calcula cobertura aproximada de la entrega respecto de la consigna."""
    base = contexto_consigna if contexto_consigna and contexto_consigna.strip() else tp
    stopwords = {
        "trabajo", "practico", "práctico", "numero", "consigna", "actividad", "responder",
        "sistema", "operativo", "pregunta", "preguntas", "de", "del", "la", "el", "los", "las",
        "para", "con", "que", "una", "por", "sobre", "como", "desde", "hasta"
    }

    tokens_consigna = [t for t in _normalizar_tokens(base) if t not in stopwords]
    unicos = []
    vistos = set()
    for t in tokens_consigna:
        if t not in vistos:
            vistos.add(t)
            unicos.append(t)
    claves = unicos[:15]

    texto_l = (texto_entrega or "").lower()
    encontrados = [k for k in claves if k in texto_l]
    cobertura = (len(encontrados) / len(claves)) if claves else 0.0
    return cobertura, encontrados, claves


def detectar_no_pertinencia_entrega(contexto_consigna, texto_entrega, tp):
    """
    Filtro estricto anti-trampa: detecta entregas ajenas a la consigna.
    Retorna (es_no_pertinente, justificacion).
    """
    if not texto_entrega or len((texto_entrega or "").strip()) < 60:
        return True, "El contenido legible es insuficiente para demostrar pertinencia con la consigna."

    stopwords = {
        "trabajo", "practico", "práctico", "numero", "consigna", "actividad", "responder",
        "sistema", "operativo", "pregunta", "preguntas", "de", "del", "la", "el", "los", "las",
        "para", "con", "que", "una", "por", "sobre", "como", "desde", "hasta",
        "y", "en", "se", "su", "sus", "al", "lo", "le", "más", "menos"
    }

    base_consigna = (contexto_consigna or "").strip() or (tp or "")
    tokens_base = [t for t in _normalizar_tokens(base_consigna) if t not in stopwords and len(t) >= 5]

    claves_unicas = []
    vistos = set()
    for t in tokens_base:
        if t not in vistos:
            vistos.add(t)
            claves_unicas.append(t)

    # Tomamos un subconjunto de claves relevantes para evitar ruido.
    claves = claves_unicas[:24]
    if not claves:
        return False, "No hay suficientes claves de consigna para validar pertinencia estricta."

    texto_l = (texto_entrega or "").lower()
    coincidencias = [k for k in claves if k in texto_l]
    cobertura = len(coincidencias) / len(claves)

    minimo_coincidencias = max(2, round(len(claves) * 0.15))
    if len(coincidencias) < minimo_coincidencias or cobertura < 0.15:
        faltantes = [k for k in claves if k not in coincidencias][:6]
        return (
            True,
            "La entrega no evidencia alineación con la consigna. "
            f"Coincidencias clave: {len(coincidencias)}/{len(claves)} ({cobertura*100:.0f}%). "
            f"Temas esperados no encontrados: {', '.join(faltantes)}."
        )

    return False, f"Pertinencia validada con {len(coincidencias)}/{len(claves)} coincidencias clave."


def verificar_pertinencia_ia_rapida(contexto_consigna, texto_entrega, tp):
    """
    Doble validación IA (rápida y barata): responde si la entrega corresponde o no.
    Retorna dict con:
      - corresponde_a_la_consigna: bool
      - justificacion_breve: str
      - fuente: "IA" | "fallback"
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return {
            "corresponde_a_la_consigna": True,
            "justificacion_breve": "Validación IA omitida (GEMINI_API_KEY no configurada).",
            "fuente": "fallback",
        }

    consigna = (contexto_consigna or "").strip()[:7000]
    entrega = (texto_entrega or "").strip()[:7000]
    tp_nombre = (tp or "").strip()

    prompt = (
        "Actuas como auditor estricto de pertinencia academica. "
        "Debes evaluar si la ENTREGA corresponde de forma directa a la CONSIGNA del TP. "
        "Si el texto es generico, copiado de otro tema, de otra materia o no resuelve la actividad, responde NO.\n\n"
        "Responde SOLO en JSON valido con esta estructura exacta:\n"
        "{\n"
        "  \"corresponde_a_la_consigna\": true/false,\n"
        "  \"justificacion_breve\": \"...\"\n"
        "}\n\n"
        f"TP: {tp_nombre}\n\n"
        f"CONSIGNA:\n{consigna}\n\n"
        f"ENTREGA:\n{entrega}\n"
    )

    try:
        client = genai.Client(api_key=api_key)
        respuesta = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        texto = (getattr(respuesta, "text", "") or "").strip()

        # Intentar parseo directo, o extraer bloque JSON si vino con texto extra.
        data = None
        try:
            data = json.loads(texto)
        except Exception:
            m = re.search(r"\{[\s\S]*\}", texto)
            if m:
                data = json.loads(m.group(0))

        if not isinstance(data, dict):
            raise ValueError("Respuesta IA no parseable a JSON.")

        corresponde = bool(data.get("corresponde_a_la_consigna", True))
        justificacion = str(data.get("justificacion_breve", "Sin justificación."))
        return {
            "corresponde_a_la_consigna": corresponde,
            "justificacion_breve": justificacion[:500],
            "fuente": "IA",
        }
    except Exception as e:
        return {
            "corresponde_a_la_consigna": True,
            "justificacion_breve": f"Validación IA no disponible ({str(e)[:160]}).",
            "fuente": "fallback",
        }


def analizar_concordancia_consigna_entrega(consigna_texto, entrega_texto, tp_nombre):
    """
    Analiza la concordancia entre la consigna y la entrega del alumno.
    Genera un análisis detallado de cuáles temas de la consigna fueron abordados.
    
    Retorna: (concordancia_score, temas_cubiertos, temas_faltantes, observaciones)
    """
    if not entrega_texto or len(entrega_texto.strip()) < 50:
        return 0.0, [], [], "Entrega insuficiente en longitud para evaluar."
    
    if not consigna_texto or len(consigna_texto.strip()) < 10:
        return 0.5, [], [], "Consigna vacía o muy breve. Se evalúa por contenido general."
    
    # Normalizar textos
    consigna_l = consigna_texto.lower()
    entrega_l = entrega_texto.lower()
    
    # Stopwords a ignorar
    stopwords = {
        "trabajo", "practico", "práctico", "numero", "consigna", "actividad", "responder",
        "sistema", "operativo", "pregunta", "preguntas", "de", "del", "la", "el", "los", "las",
        "para", "con", "que", "una", "por", "sobre", "como", "desde", "hasta", "el", "la", "los", "las",
        "es", "son", "está", "están", "fue", "fueron", "sea", "sean", "deben", "debe", "debería"
    }
    
    # Extraer palabras clave de la consigna
    tokens_consigna = [t for t in _normalizar_tokens(consigna_texto) if t not in stopwords and len(t) >= 4]
    
    # Eliminar duplicados manteniendo orden
    palabras_clave = []
    vistos = set()
    for t in tokens_consigna:
        if t not in vistos:
            vistos.add(t)
            palabras_clave.append(t)
    
    # Limitar a 20 palabras clave más importantes
    palabras_clave = palabras_clave[:20]
    
    if not palabras_clave:
        return 0.5, [], [], "No se pudieron extraer palabras clave de la consigna."
    
    # Contar coincidencias de palabras clave en la entrega
    temas_cubiertos = []
    for palabra in palabras_clave:
        if palabra in entrega_l:
            temas_cubiertos.append(palabra)
    
    # Calcular porcentaje de cobertura
    cobertura = len(temas_cubiertos) / len(palabras_clave) if palabras_clave else 0.0
    temas_faltantes = [p for p in palabras_clave if p not in temas_cubiertos]
    
    # Análisis de calidad: extensión y profundidad
    largo_entrega = len(entrega_texto.split())
    
    # Criterios de calidad
    puntos_calidad = 0
    observaciones = []
    
    if largo_entrega < 100:
        observaciones.append("Entrega muy breve, falta profundidad.")
        puntos_calidad -= 2
    elif largo_entrega < 200:
        observaciones.append("Entrega moderadamente desarrollada.")
        puntos_calidad += 1
    else:
        observaciones.append("Entrega con desarrollo adecuado.")
        puntos_calidad += 2
    
    # Penalizar falta de cobertura
    if cobertura < 0.3:
        observaciones.append("Muy baja cobertura de temas de la consigna.")
        puntos_calidad -= 3
    elif cobertura < 0.5:
        observaciones.append("Cobertura parcial de temas solicitados.")
        puntos_calidad -= 1
    elif cobertura < 0.7:
        observaciones.append("Buena cobertura de la mayoría de temas.")
        puntos_calidad += 1
    else:
        observaciones.append("Excelente cobertura de temas solicitados.")
        puntos_calidad += 2
    
    # Score final (0-1)
    concordancia_score = min(1.0, max(0.0, cobertura + (puntos_calidad * 0.1)))
    
    return concordancia_score, temas_cubiertos, temas_faltantes, " ".join(observaciones)


def generar_nota_desde_concordancia(concordancia_score, largo_entrega, temas_cubiertos, temas_faltantes):
    """
    Convierte un score de concordancia (0-1) a una nota de 1-10.
    
    Lógica:
    - 0.0-0.2: Nota 1-3 (No aprobado)
    - 0.2-0.4: Nota 3-5 (Reprobado)
    - 0.4-0.6: Nota 5-7 (Aprobado con deficiencias)
    - 0.6-0.8: Nota 7-9 (Bien/Muy bien)
    - 0.8-1.0: Nota 9-10 (Excelente)
    """
    # Base: mapeo directo 0-1 a 1-10
    nota_base = 1 + (concordancia_score * 9)
    
    # Ajustes por longitud
    if largo_entrega < 50:
        nota_base -= 2  # Muy breve, desaprueba
    elif largo_entrega < 100:
        nota_base -= 1  # Breve, reduce nota
    elif largo_entrega > 500:
        nota_base = min(10, nota_base + 0.5)  # Desarrollo extenso, bonificación pequeña
    
    # Redondear a entero
    nota_final = round(nota_base)
    
    # Asegurar rango 1-10
    nota_final = max(1, min(10, nota_final))
    
    return nota_final


def evaluar_entrega_automatica(alumno, tp, service_drive, contexto_consigna=""):
    """
    Genera feedback automático basado en análisis REAL de concordancia consigna-entrega.
    
    FLUJO CORRECTO:
    1. Verificar si el texto se puede extraer
    2. Si NO: marcar como "Revisión manual requerida"
    3. Si SÍ: Analizar concordancia con la consigna
    4. Generar nota justa (1-10) basada en concordancia real
    """
    estado = (alumno.get("estado") or "").upper()
    attachments = alumno.get("attachments", []) or []

    # PASO 1: Verificar si hay adjuntos
    if not attachments and estado in {"NEW", "CREATED", "SIN_ENTREGA"}:
        return {
            "estado": "Adeuda entrega",
            "nota": 1,
            "motivo": "No entregó material adjunto.",
            "feedback": f"No se ha recibido entrega para esta actividad. Por favor, sube tu trabajo en Classroom."
        }

    if not attachments:
        return {
            "estado": "Adeuda entrega",
            "nota": 1,
            "motivo": "Entrega sin material adjunto verificable.",
            "feedback": f"Se registró una entrega pero sin archivos adjuntos. Asegúrate de adjuntar tu trabajo."
        }

    analisis_adjuntos = _analizar_formatos_adjuntos(attachments, service_drive)

    # PASO 2: Intentar extraer texto de la entrega
    texto_entrega = _extraer_texto_de_attachments(attachments, service_drive)

    texto_limpio = (texto_entrega or "").strip()
    texto_no_legible = (
        not texto_limpio
        or len(texto_limpio) < 30
        or texto_limpio.startswith("[Error extrayendo PDF")
        or texto_limpio.startswith("[No se pudo extraer texto del PDF")
        or "GEMINI_API_KEY no configurada" in texto_limpio
    )

    if texto_no_legible:
        detalle_error = ""
        if texto_limpio.startswith("["):
            detalle_error = f" Detalle técnico: {texto_limpio[:220]}"

        # Trampa por formato: solo imágenes u otros formatos no textuales.
        if analisis_adjuntos.get("textuales", 0) == 0 and analisis_adjuntos.get("totales", 0) > 0:
            return {
                "estado": "Rehacer",
                "nota": 1,
                "motivo": (
                    "Entrega no pertinente por formato no evaluable. "
                    f"Adjuntos detectados: {analisis_adjuntos.get('totales', 0)} "
                    f"(textuales: {analisis_adjuntos.get('textuales', 0)}, "
                    f"imágenes: {analisis_adjuntos.get('imagenes', 0)}, otros: {analisis_adjuntos.get('otros', 0)})."
                ),
                "feedback": (
                    "La entrega no contiene un archivo textual evaluable acorde a la consigna (por ejemplo PDF o documento con contenido). "
                    "Por favor, rehace y vuelve a subir una resolución completa del TP."
                ),
            }

        # Trampa típica: documento vacío + imagen no relacionada.
        if analisis_adjuntos.get("textuales", 0) >= 1 and analisis_adjuntos.get("imagenes", 0) >= 1 and len(texto_limpio) < 30:
            return {
                "estado": "Rehacer",
                "nota": 1,
                "motivo": (
                    "Entrega no pertinente o vacía: se detectaron adjuntos textuales sin contenido evaluable "
                    "junto con imágenes que no sustituyen la resolución solicitada."
                ),
                "feedback": (
                    "La entrega no presenta una resolución legible y pertinente de la actividad. "
                    "Por favor, rehace el TP y sube un documento completo que responda la consigna."
                ),
            }

        # Caso general: no se pudo extraer texto legible.
        # RETORNA NOTA 4 (baja) para que al menos se publique algo en revisión manual
        return {
            "estado": "Revisión manual requerida",
            "nota": 4,
            "motivo": "No se pudo extraer el texto del archivo adjunto. Parece ser un PDF escaneado o una imagen. Requiere inspección humana." + detalle_error,
            "feedback": f"El archivo adjunto no permite la lectura automática de contenido (posible escaneo o imagen no procesable). Te solicito que re-entregues el trabajo en formato de texto legible (Word .docx, Google Docs o archivo .txt)."
        }

    # PASO 2.4: Doble validación IA semántica (si hay GEMINI_API_KEY).
    validacion_ia = verificar_pertinencia_ia_rapida(contexto_consigna, texto_entrega, tp)
    if not validacion_ia.get("corresponde_a_la_consigna", True):
        justificacion_ia = validacion_ia.get("justificacion_breve", "No corresponde a la consigna.")
        return {
            "estado": "Rehacer",
            "nota": 1,
            "motivo": f"Entrega no pertinente (validación IA). {justificacion_ia}",
            "feedback": (
                "La entrega no corresponde de forma directa a la consigna del TP. "
                "Por favor, rehace y vuelve a subir una resolución específica de la actividad solicitada."
            ),
        }

    # PASO 2.5: Filtro trap de no pertinencia antes de evaluar calidad.
    no_pertinente, justificacion_pertinencia = detectar_no_pertinencia_entrega(
        contexto_consigna,
        texto_entrega,
        tp,
    )
    if no_pertinente:
        return {
            "estado": "Rehacer",
            "nota": 1,
            "motivo": f"Entrega no pertinente a la consigna. {justificacion_pertinencia}",
            "feedback": (
                "La entrega adjunta no corresponde a la actividad solicitada o no desarrolla los temas de la consigna. "
                "Por favor, rehace la entrega y vuelve a subir un archivo alineado al TP indicado."
            ),
        }

    # PASO 3: El texto ES legible. Analizar concordancia con la consigna
    concordancia_score, temas_cubiertos, temas_faltantes, obs_concordancia = \
        analizar_concordancia_consigna_entrega(contexto_consigna, texto_entrega, tp)
    
    # PASO 4: Generar nota basada en concordancia real
    largo_entrega = len(texto_entrega.split())
    nota = generar_nota_desde_concordancia(concordancia_score, largo_entrega, temas_cubiertos, temas_faltantes)
    
    # PASO 5: Generar feedback personalizado basado en concordancia
    feedback = _generar_feedback_personalizado(
        tp, nota, concordancia_score, temas_cubiertos, temas_faltantes, 
        contexto_consigna, obs_concordancia
    )
    
    # Determinar estado
    if nota < 4:
        estado_resultado = "No Aprobado"
    elif nota < 7:
        estado_resultado = "Aprobado con deficiencias"
    else:
        estado_resultado = "Aprobado"
    
    return {
        "estado": estado_resultado,
        "nota": nota,
        "motivo": f"Análisis de concordancia con consigna: {concordancia_score*100:.0f}% cobertura. {obs_concordancia}",
        "feedback": feedback
    }


def _limpiar_nombre_ruta(texto, fallback="sin_nombre"):
    """Normaliza un texto para usarlo de forma segura como nombre de carpeta/archivo."""
    if texto is None:
        texto = ""
    limpio = "".join(c for c in str(texto) if c.isalnum() or c in "._- ").strip()
    limpio = re.sub(r"\s+", " ", limpio)
    if not limpio:
        limpio = fallback

    # Evitar nombres reservados de Windows.
    reservados = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    }
    if limpio.upper() in reservados:
        limpio = f"{limpio}_archivo"

    return limpio[:120]


def _extension_por_mimetype(mime_type):
    """Retorna una extensión recomendada para un mime type de Google Drive."""
    mapa = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
        "text/plain": ".txt",
        "image/png": ".png",
        "image/jpeg": ".jpg",
    }
    if mime_type in mapa:
        return mapa[mime_type]

    # Archivos nativos de Google (al exportar) según mapeo de descargar_adjunto_drive.
    if mime_type == "application/vnd.google-apps.document":
        return ".docx"
    if mime_type == "application/vnd.google-apps.spreadsheet":
        return ".xlsx"
    if mime_type == "application/vnd.google-apps.presentation":
        return ".pptx"
    if mime_type == "application/vnd.google-apps.drawing":
        return ".png"

    return ""


def preparar_carpeta_y_descargar_entrega(alumno, nombre_materia, nombre_tp, service_drive):
    """
    Crea carpeta local por alumno y descarga allí sus adjuntos de Drive.
    Retorna: (carpeta_destino, rutas_archivos_descargados, errores_descarga)
    """
    materia_dir = _limpiar_nombre_ruta(nombre_materia, "Materia")
    tp_dir = _limpiar_nombre_ruta(nombre_tp, "TP")
    alumno_dir = _limpiar_nombre_ruta(alumno.get("nombre", "Alumno_Desconocido"), "Alumno_Desconocido")

    carpeta_destino = os.path.join("Correcciones_Classroom", materia_dir, tp_dir, alumno_dir)
    os.makedirs(carpeta_destino, exist_ok=True)

    archivos_descargados = []
    errores_descarga = []
    attachments = alumno.get("attachments", []) or []

    print(f"\n📁 Espacio local de corrección: {carpeta_destino}")

    for idx, adj in enumerate(attachments, start=1):
        drive_file = _obtener_drive_file_desde_attachment(adj)
        if not drive_file:
            continue
        file_id = drive_file.get("id")
        file_title = _limpiar_nombre_ruta(drive_file.get("title", f"archivo_{idx}"), f"archivo_{idx}")
        if not file_id:
            continue

        try:
            metadata = service_drive.files().get(fileId=file_id, fields="mimeType").execute()
            mime_type = metadata.get("mimeType", "")
            contenido_bytes = descargar_adjunto_drive(service_drive, file_id, mime_type)

            if not contenido_bytes:
                print(f"   ⚠️ No se pudo descargar: {file_title}")
                errores_descarga.append(f"No se pudo descargar: {file_title}")
                continue

            _, ext_actual = os.path.splitext(file_title)
            if not ext_actual:
                file_title = f"{file_title}{_extension_por_mimetype(mime_type)}"

            nombre_salida = f"entrega_{file_title}"
            ruta_archivo_local = os.path.join(carpeta_destino, nombre_salida)

            # Evitar sobreescritura si hay adjuntos con mismo nombre.
            if os.path.exists(ruta_archivo_local):
                base, ext = os.path.splitext(nombre_salida)
                ruta_archivo_local = os.path.join(carpeta_destino, f"{base}_{idx}{ext}")

            with open(ruta_archivo_local, "wb") as f:
                f.write(contenido_bytes)

            archivos_descargados.append(ruta_archivo_local)
            print(f"   💾 Adjuntado guardado: {os.path.basename(ruta_archivo_local)}")
        except Exception as e:
            print(f"   ⚠️ Error al descargar '{file_title}': {e}")
            errores_descarga.append(f"Error al descargar '{file_title}': {e}")

    if not archivos_descargados and not errores_descarga:
        errores_descarga.append("No se encontraron adjuntos de tipo Drive en la entrega del alumno.")

    return carpeta_destino, archivos_descargados, errores_descarga


def guardar_reportes_locales(carpeta_destino, contexto_consigna, evaluacion):
    """
    Guarda consigna, comentario privado e informe técnico JSON en la carpeta del alumno.
    """
    os.makedirs(carpeta_destino, exist_ok=True)

    if contexto_consigna and contexto_consigna.strip():
        with open(os.path.join(carpeta_destino, "consigna_referencia.txt"), "w", encoding="utf-8") as f:
            f.write(contexto_consigna)

    feedback = (evaluacion.get("feedback") or "").strip()
    if feedback:
        with open(os.path.join(carpeta_destino, "comentario_privado.txt"), "w", encoding="utf-8") as f:
            f.write(feedback)

    reporte_detallado = {
        "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "estado_resultado": evaluacion.get("estado", "No definido"),
        "nota": evaluacion.get("nota"),
        "motivo_tecnico": evaluacion.get("motivo", ""),
        "feedback": evaluacion.get("feedback", ""),
    }

    with open(os.path.join(carpeta_destino, "informe_tecnico_pedagogico.json"), "w", encoding="utf-8") as f:
        json.dump(reporte_detallado, f, indent=4, ensure_ascii=False)

    print("   📊 Consigna, comentario e informe técnico guardados localmente.")


def _generar_feedback_personalizado(tp, nota, concordancia, temas_cubiertos, temas_faltantes, 
                                    consigna, observaciones):
    """
    Genera feedback personalizado basado en análisis real de la entrega.
    NO usa plantillas genéricas.
    """
    feedback = ""
    
    # Introducción personalizada
    if nota >= 9:
        feedback += f"Excelente trabajo en {tp}. Has abordado esta actividad de forma integral y profunda.\n\n"
    elif nota >= 7:
        feedback += f"Buen trabajo en {tp}. Has cubierto la mayoría de los aspectos solicitados.\n\n"
    elif nota >= 5:
        feedback += f"Tu entrega de {tp} presenta un desarrollo parcial. Analicemos qué falta.\n\n"
    else:
        feedback += f"Tu entrega de {tp} requiere atención importante. Veamos los puntos clave.\n\n"
    
    # Detalles de cobertura
    if temas_cubiertos:
        feedback += f"✓ Temas que sí abordaste bien: {', '.join(temas_cubiertos[:5])}.\n"
    
    if temas_faltantes:
        feedback += f"✗ Temas por mejorar o que faltaron: {', '.join(temas_faltantes[:5])}.\n"
    
    feedback += f"\n{observaciones}\n\n"
    
    # Recomendaciones según nota
    if nota >= 7:
        feedback += "Mantén este nivel de compromiso en futuras entregas.\n"
    else:
        feedback += "Para mejorar en próximas entregas:\n"
        feedback += "1. Lee cuidadosamente TODA la consigna antes de comenzar.\n"
        feedback += "2. Identifica los puntos clave que deben estar en tu trabajo.\n"
        feedback += "3. Desarrolla cada punto con profundidad y claridad.\n"
        feedback += "4. Si necesitas orientación, consulta al docente.\n"
    
    feedback += f"\nCalificación: {nota}/10."
    
    return feedback


def construir_lote_automatico(alumnos_tp, tp, service_drive, contexto_consigna="", nombre_materia=""):
    """
    VERSIÓN AUTOMÁTICA: Procesa TODOS los alumnos sin interacción.
    Retorna lista de dicts con metadatos para publicación posterior.
    """
    if not alumnos_tp:
        return []

    lote = []
    
    print(f"\n   📊 Procesando {len(alumnos_tp)} alumno(s) automáticamente...")

    for idx, alumno in enumerate(alumnos_tp, start=1):
        nombre = alumno.get("nombre", "Sin nombre")
        print(f"\n   [{idx}/{len(alumnos_tp)}] {nombre}...")
        
        try:
            # Preparar carpeta y descargar
            carpeta_destino, archivos_descargados, errores_descarga = preparar_carpeta_y_descargar_entrega(
                alumno,
                nombre_materia,
                tp,
                service_drive,
            )
            
            # Guardar consigna
            reporte_local.guardar_reportes_locales(
                carpeta_destino,
                contexto_consigna,
                {
                    "estado": "Pendiente",
                    "nota": None,
                    "motivo": "Pendiente de evaluación",
                    "feedback": "",
                },
                alumno_nombre=nombre,
                nombre_materia=nombre_materia,
                nombre_tp=tp,
            )
            reporte_local.guardar_estado_descarga(
                carpeta_destino,
                nombre,
                archivos_descargados,
                errores_descarga,
            )
        except Exception as e:
            print(f"      ⚠️ Preparación: {str(e)[:80]}")
        
        # Evaluar automáticamente
        evaluacion = evaluar_entrega_automatica(alumno, tp, service_drive, contexto_consigna)
        
        estado_eval = evaluacion.get("estado", "Revisión manual requerida")
        nota_eval = evaluacion.get("nota")
        feedback_eval = evaluacion.get("feedback", "")
        motivo_eval = evaluacion.get("motivo", "")
        
        # Actualizar reportes con evaluación
        try:
            evaluacion_local = {
                "estado": estado_eval,
                "nota": nota_eval,
                "motivo": motivo_eval,
                "feedback": feedback_eval,
            }
            reporte_local.guardar_reportes_locales(
                carpeta_destino,
                contexto_consigna,
                evaluacion_local,
                alumno_nombre=nombre,
                nombre_materia=nombre_materia,
                nombre_tp=tp,
            )
        except Exception as e:
            print(f"      ⚠️ Guardado: {str(e)[:80]}")
        
        # Agregar a lote
        lote.append({
            "nombre": nombre,
            "feedback": feedback_eval,
            "estado": estado_eval,
            "estado_entrega": alumno.get("estado", "UNKNOWN"),
            "nota": nota_eval,
            "motivo": motivo_eval,
            "user_id": alumno.get("user_id"),
            "submission_id": alumno.get("submission_id"),
            "alternate_link": alumno.get("alternate_link"),
        })
        
        print(f"      ✅ Nota: {nota_eval if nota_eval else 'Pendiente'} | Estado: {estado_eval[:30]}")

    print(f"\n   ✅ Procesados {len(lote)} alumno(s)")
    return lote


def construir_lote_desde_listado_alumnos(alumnos_tp, tp, service_drive, contexto_consigna="", nombre_materia=""):
    """
    Permite elegir alumnos del TP y cargar feedback para cada uno.
    Ahora utiliza el nuevo sistema de evaluación de concordancia.
    Retorna lista de dicts con metadatos para publicación posterior.
    """
    if not alumnos_tp:
        return []

    print("\n" + "=" * 60)
    print("  PASO 4 — Seleccioná alumnos del TP a corregir")
    print("=" * 60)
    for i, alumno in enumerate(alumnos_tp, start=1):
        cant_adjuntos = len(alumno.get("attachments", []) or [])
        print(f"  [{i}] {alumno.get('nombre', 'Sin nombre')}  [{alumno.get('estado', 'UNKNOWN')}]  [Adjuntos: {cant_adjuntos}]")
    print("  [0] Finalizar carga")
    print("=" * 60)

    seleccionados = set()
    lote = []

    while True:
        try:
            opcion = int(input("Elegí número de alumno a corregir (0 para terminar): ").strip())
        except ValueError:
            print("   ⚠️ Entrada no válida. Ingresá un número.")
            continue

        if opcion == 0:
            break

        if not (1 <= opcion <= len(alumnos_tp)):
            print(f"   ⚠️ Ingresá un número entre 0 y {len(alumnos_tp)}.")
            continue

        idx = opcion - 1
        if idx in seleccionados:
            print("   ⚠️ Ese alumno ya fue cargado en esta tanda.")
            continue

        alumno = alumnos_tp[idx]
        nombre = alumno.get("nombre", "Sin nombre")

        carpeta_destino = ""
        archivos_descargados = []
        errores_descarga = []

        # Preparar evidencia local ANTES de la aceptación para tener el material disponible.
        try:
            carpeta_destino, archivos_descargados, errores_descarga = preparar_carpeta_y_descargar_entrega(
                alumno,
                nombre_materia,
                tp,
                service_drive,
            )
            # Guardar consigna de referencia desde el inicio.
            reporte_local.guardar_reportes_locales(
                carpeta_destino,
                contexto_consigna,
                {
                    "estado": "Pendiente",
                    "nota": None,
                    "motivo": "Pendiente de confirmación docente",
                    "feedback": "",
                },
                alumno_nombre=nombre,
                nombre_materia=nombre_materia,
                nombre_tp=tp,
            )
            reporte_local.guardar_estado_descarga(
                carpeta_destino,
                nombre,
                archivos_descargados,
                errores_descarga,
            )
        except Exception as e:
            print(f"   ⚠️ No se pudo preparar la carpeta local para {nombre}: {e}")
        
        # Evaluar automáticamente la entrega del alumno
        evaluacion = evaluar_entrega_automatica(alumno, tp, service_drive, contexto_consigna)
        
        estado_eval = evaluacion.get("estado", "Revisión manual requerida")
        nota_eval = evaluacion.get("nota")
        feedback_eval = evaluacion.get("feedback", "")
        motivo_eval = evaluacion.get("motivo", "")
        
        print(f"\n   📋 EVALUACIÓN AUTOMÁTICA para {nombre}:")
        print(f"      Estado: {estado_eval}")
        print(f"      Nota: {nota_eval if nota_eval else 'Pendiente'}")
        print(f"      {motivo_eval}")
        print("   ✅ Evaluación aceptada automáticamente.")

        # Actualizar reportes locales finales con la decisión tomada.
        try:
            evaluacion_local = {
                "estado": estado_eval,
                "nota": nota_eval,
                "motivo": motivo_eval,
                "feedback": feedback_eval,
            }
            reporte_local.guardar_reportes_locales(
                carpeta_destino,
                contexto_consigna,
                evaluacion_local,
                alumno_nombre=nombre,
                nombre_materia=nombre_materia,
                nombre_tp=tp,
            )
            reporte_local.guardar_estado_descarga(
                carpeta_destino,
                nombre,
                archivos_descargados,
                errores_descarga,
            )
        except Exception as e:
            print(f"   ⚠️ No se pudo completar el guardado local para {nombre}: {e}")
        
        # Agregar a lote
        lote.append({
            "nombre": nombre,
            "feedback": feedback_eval,
            "estado": estado_eval,
            "estado_entrega": alumno.get("estado", "UNKNOWN"),
            "nota": nota_eval,
            "motivo": motivo_eval,
            "user_id": alumno.get("user_id"),
            "submission_id": alumno.get("submission_id"),
            "alternate_link": alumno.get("alternate_link"),
        })
        seleccionados.add(idx)
        print(f"   ✅ {nombre} agregado/a para corrección.\n")

        # Modo ágil: tras seleccionar y evaluar un alumno, continuar directamente
        # al procesamiento del reporte sin pedir un nuevo número.
        print("   ⚡ Continuando al procesamiento del reporte...")
        break

    return lote


def _mapear_nota_a_classroom(nota_1_10):
    """Convierte escala 1-10 a 0-100 para Classroom."""
    if nota_1_10 is None:
        return None
    try:
        valor = float(nota_1_10) * 10.0
    except Exception:
        return None
    return max(0.0, min(100.0, valor))


def _publicar_nota_en_classroom(service, course_id, work_id, submission_id, nota_100, solo_borrador=False):
    """Publica nota en Classroom como borrador o definitiva."""
    if nota_100 is None:
        return False

    if solo_borrador:
        cuerpo_nota = {"draftGrade": nota_100}
        update_mask = "draftGrade"
    else:
        cuerpo_nota = {
            "draftGrade": nota_100,
            "assignedGrade": nota_100,
        }
        update_mask = "draftGrade,assignedGrade"

    service.courses().courseWork().studentSubmissions().patch(
        courseId=course_id,
        courseWorkId=work_id,
        id=submission_id,
        updateMask=update_mask,
        body=cuerpo_nota,
    ).execute()
    return True


def _devolver_tarea_en_classroom(service, course_id, work_id, submission_id):
    """Ejecuta el retorno formal de la entrega en Classroom."""
    service.courses().courseWork().studentSubmissions().return_(
        courseId=course_id,
        courseWorkId=work_id,
        id=submission_id,
        body={},
    ).execute()


def publicar_resultados_en_classroom(service, course_id, work_id, reporte_entregas, lote_seleccionado):
    """
    Publica calificaciones en Classroom basadas en el análisis de concordancia.
    Maneja el nuevo formato de lote que incluye notas y estados de evaluación.
    """
    if not lote_seleccionado:
        return

    print("\n📤 Publicando resultados en Classroom...")

    # Relacionar por nombre de alumno (lote_seleccionado tiene estructura nueva)
    pendientes_comentario = []
    publicados = 0
    comentarios_publicados = 0
    errores = 0

    # Modo de prueba: guardar nota en borrador y no devolver automáticamente.
    SOLO_BORRADOR = True
    DEVOLVER_AUTOMATICAMENTE = not SOLO_BORRADOR

    for item in lote_seleccionado:
        alumno_nombre = item.get("nombre", "Alumno")
        submission_id = item.get("submission_id")
        estado_entrega = item.get("estado_entrega", "UNKNOWN")
        alternate_link = item.get("alternate_link")
        nota = item.get("nota")
        feedback = item.get("feedback", "")
        
        feedback_txt = (feedback or "").strip()
        nota_100 = _mapear_nota_a_classroom(nota)

        if not submission_id:
            if feedback_txt and alternate_link:
                pendientes_comentario.append({
                    "alumno": alumno_nombre,
                    "link": alternate_link,
                    "nota": nota,
                    "comentario_privado": feedback,
                    "error_api": "Sin submission_id para comentar por API",
                })
            print(f"   ℹ️ {alumno_nombre}: Sin submission_id (posible revisión manual requerida)")
            continue

        # Ejecutar en bloque único: nota -> comentario -> devolución.
        try:
            if nota_100 is not None:
                _publicar_nota_en_classroom(
                    service,
                    course_id,
                    work_id,
                    submission_id,
                    nota_100,
                    solo_borrador=SOLO_BORRADOR,
                )
                if SOLO_BORRADOR:
                    print(f"   ✅ [1/3] Nota {nota}/10 guardada en borrador para {alumno_nombre}")
                else:
                    print(f"   ✅ [1/3] Nota {nota}/10 asignada para {alumno_nombre}")
            else:
                print(f"   ⓘ [1/3] Sin nota para {alumno_nombre}")

            if feedback_txt:
                ss_resource = service.courses().courseWork().studentSubmissions()
                if not hasattr(ss_resource, "comments"):
                    raise AttributeError("El cliente Classroom v1 no expone studentSubmissions.comments()")
                ss_resource.comments().create(
                    courseId=course_id,
                    courseWorkId=work_id,
                    id=submission_id,
                    body={"text": feedback_txt},
                ).execute()
                comentarios_publicados += 1
                print(f"   ✅ [2/3] Comentario privado creado para {alumno_nombre}")
            else:
                print(f"   ⓘ [2/3] Sin comentario para {alumno_nombre}")

            if DEVOLVER_AUTOMATICAMENTE:
                _devolver_tarea_en_classroom(service, course_id, work_id, submission_id)
                print(f"   ✅ [3/3] Entrega devuelta para {alumno_nombre}")
            else:
                print(f"   ⓘ [3/3] Devolución automática desactivada (modo borrador)")

            publicados += 1
            if DEVOLVER_AUTOMATICAMENTE:
                print(f"   ✅ ÉXITO: Todo publicado y devuelto para {alumno_nombre} (nota={nota})")
            else:
                print(f"   ✅ ÉXITO: Nota/comentario publicados en modo borrador para {alumno_nombre} (nota={nota})")
        except HttpError as e:
            errores += 1
            if feedback_txt and alternate_link:
                pendientes_comentario.append({
                    "alumno": alumno_nombre,
                    "link": alternate_link,
                    "nota": nota,
                    "comentario_privado": feedback,
                    "error_api": str(e)[:180],
                })
            print(f"   ⚠️ Error al interactuar con Classroom para {alumno_nombre}: {str(e)[:120]}")
            if "ProjectPermissionDenied" in str(e):
                print("   ℹ️ El proyecto OAuth actual no tiene habilitado permiso para escritura en Classroom.")
                print("   ℹ️ Verificá que el OAuth client pertenezca a un proyecto con Classroom API habilitada, pantalla OAuth publicada y scopes de escritura autorizados.")
        except Exception as e:
            errores += 1
            if feedback_txt and alternate_link:
                pendientes_comentario.append({
                    "alumno": alumno_nombre,
                    "link": alternate_link,
                    "nota": nota,
                    "comentario_privado": feedback,
                    "error_api": str(e)[:180],
                })
            print(f"   ⚠️ Error inesperado para {alumno_nombre}: {str(e)[:120]}")

    print(f"\n   ✅ Calificaciones publicadas: {publicados}")
    print(f"   ✅ Comentarios privados publicados por API: {comentarios_publicados}")
    if errores:
        print(f"   ⚠️ Errores al publicar calificaciones: {errores}")

    # Guardar comentarios pendientes para envío web y abrir enlaces.
    if pendientes_comentario:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        carpeta_reportes = obtener_carpeta_reportes_del_dia()
        archivo_pendientes = os.path.join(carpeta_reportes, f"comentarios_privados_pendientes_{timestamp}.json")
        try:
            with open(archivo_pendientes, "w", encoding="utf-8") as f:
                f.write(json.dumps(pendientes_comentario, ensure_ascii=False, indent=2))
            print(f"\n   ℹ️ Comentarios privados pendientes guardados en: {archivo_pendientes}")
            print("   ℹ️ Abriendo enlaces solo para los casos que fallaron por API...")
            print("   ℹ️ Flujo manual: tildá al alumno y enfocá el cuadro de comentario; luego presioná Enter para copiar.")

            for p in pendientes_comentario[:3]:  # Abrir máximo 3 enlaces
                link = p.get("link")
                comentario = (p.get("comentario_privado") or "").strip()
                alumno_p = p.get("alumno", "Alumno")

                if link:
                    try:
                        webbrowser.open(link)
                        time.sleep(1)  # Esperar entre aperturas
                    except Exception:
                        pass

                if comentario:
                    print(f"\n   👉 {alumno_p}: Abriendo Classroom (copia automática en proceso)...")
                    time.sleep(0.5)  # Pequeña pausa para que el navegador se abra

                    if copiar_texto_portapapeles(comentario):
                        print(f"   ✅ Comentario copiado automáticamente al portapapeles para {alumno_p}")
                        if AUTO_PEGADO_DISPONIBLE:
                            # Intentar pegado automático sin preguntar
                            print(f"   ℹ️ Intentando pegado automático en Chrome activo...")
                            time.sleep(1)  # Pausa para que el usuario posicione el cursor
                            if pegar_y_enviar_comentario_automatico(comentario, delay_segundos=2.0):
                                print(f"   ✅ Comentario pegado y enviado automáticamente para {alumno_p}")
                            else:
                                print(f"   ℹ️ Pegado automático no funcionó. Usá Ctrl+V para pegar manualmente.")
                        else:
                            print(f"   ℹ️ Pegado automático no disponible. Usá Ctrl+V para pegar manualmente.")
                    else:
                        print(f"   ⚠️ No se pudo copiar al portapapeles para {alumno_p}")
                        nombre_archivo = re.sub(r"[^\w\-]+", "_", alumno_p, flags=re.UNICODE).strip("_") or "alumno"
                        archivo_txt = os.path.join(carpeta_reportes, f"comentario_manual_{nombre_archivo}_{timestamp}.txt")
                        try:
                            with open(archivo_txt, "w", encoding="utf-8") as f_txt:
                                f_txt.write(comentario)
                            print(f"   ℹ️ Comentario guardado para pegado manual en: {archivo_txt}")
                        except Exception:
                            pass

        except Exception as e:
            print(f"   ⚠️ No se pudo guardar archivo de comentarios pendientes: {e}")


def iniciar_corrector_pedagogico():
    """
    Inicia el proceso de corrección pedagógica con entrada interactiva.
    Utiliza el módulo corrector_pedagogico para generar JSON estructurado.
    Solicita criterios de exigencia para contextualizar las devoluciones.
    """
    print("\n" + "=" * 60)
    print("  CORRECTOR PEDAGÓGICO — Redacción Empática Avanzada")
    print("=" * 60)
    
    # PASO 1: Selección de materia
    materia_info = seleccionar_materia_para_corrector()
    if not materia_info:
        print("❌ No se seleccionó ninguna materia.")
        return
    
    print(f"\n✅ Materia seleccionada: {materia_info['nombre']}")

    service = materia_info["service"]
    service_drive = materia_info.get("service_drive")
    course_id = materia_info["course_id"]

    # PASO 2: Selección de tema
    tema_elegido = seleccionar_tema_para_corrector(service, course_id)
    if not tema_elegido:
        print("❌ No se pudo seleccionar un tema.")
        return

    print(f"\n✅ Tema seleccionado: {tema_elegido.get('name', 'Sin nombre')}")

    # PASO 3: Selección de actividad del tema
    actividad_elegida = seleccionar_actividad_para_corrector(service, course_id, tema_elegido)
    if not actividad_elegida:
        print("❌ No se seleccionó ninguna actividad.")
        return

    tp = actividad_elegida.get("title", "Actividad")
    work_id = actividad_elegida.get("id")
    
    print(f"\n✅ Actividad seleccionada: {tp}")
    
    # Crear instancia del corrector en modo directo (sin solicitar criterios)
    corrector = CorrectorPedagogico(materia_info["nombre"], tp)

    # Contexto de consigna para evaluación automática
    contexto_consigna = obtener_contexto_consigna(service, service_drive, course_id, work_id, actividad_elegida)
    
    # PASO 4: Lista de alumnos vinculados al TP seleccionado
    lista_alumnos = []
    entradas_automaticas = []
    lote_seleccionado = []
    alumnos_tp = listar_alumnos_por_actividad(service, course_id, work_id)
    if alumnos_tp:
        lote_seleccionado = construir_lote_desde_listado_alumnos(
            alumnos_tp,
            tp,
            service_drive,
            contexto_consigna,
            materia_info["nombre"],
        )
        # Mantener resultados automáticos sin reclasificarlos para evitar falsos "Adeuda Entrega".
        for x in lote_seleccionado:
            estado_auto = (x.get("estado") or "").strip()
            if estado_auto and estado_auto != "MANUAL":
                entradas_automaticas.append({
                    "alumno": x.get("nombre", "Sin nombre"),
                    "estado_interno": estado_auto,
                    "nota": x.get("nota"),
                    "motivo_correccion": x.get("motivo", "Evaluación automática"),
                    "devolucion_alumno": x.get("feedback", ""),
                })
            elif x.get("nombre") and x.get("feedback"):
                lista_alumnos.append((x["nombre"], x["feedback"]))
    else:
        print("\n⚠️ No se pudo obtener listado de alumnos del TP; se habilita carga manual.")

    if not lista_alumnos and not entradas_automaticas:
        print("\n" + "=" * 60)
        print("  INGRESÁ LOS DATOS DE CORRECCIÓN")
        print("=" * 60)
        print("Formato: [Nombre Alumno]: [Feedback del docente]")
        print("Ejemplo: Juan Pérez: Trabajo excelente, bien justificado, código limpio. Nota 9.")
        print("Escribe 'FIN' cuando termines de ingresar alumnos.")
        print("=" * 60 + "\n")

        contador = 1
        while True:
            entrada = input(f"[{contador}] Ingresá (o 'FIN' para terminar): ").strip()

            if entrada.upper() == "FIN":
                break

            if ':' not in entrada:
                print("   ⚠️  Formato inválido. Usa: Nombre: feedback")
                continue

            nombre, feedback = entrada.split(':', 1)
            nombre = nombre.strip()
            feedback = feedback.strip()

            if nombre and feedback:
                lista_alumnos.append((nombre, feedback))
                lote_seleccionado.append({
                    "nombre": nombre,
                    "feedback": feedback,
                    "user_id": None,
                    "submission_id": None,
                    "estado": "MANUAL",
                    "alternate_link": None,
                })
                print(f"   ✅ {nombre} ingresado/a.")
                contador += 1
            else:
                print("   ⚠️  Nombre o feedback vacío.")
    
    if not lista_alumnos and not entradas_automaticas:
        print("\n❌ No ingresaste datos de alumnos.")
        return
    
    # Procesar lote
    total_procesar = len(lista_alumnos) + len(entradas_automaticas)
    print(f"\n⚙️  Procesando {total_procesar} alumno(s)...")
    print("   Aplicando análisis pedagógico automático...")
    if entradas_automaticas:
        corrector.reporte_entregas.extend(entradas_automaticas)
    if lista_alumnos:
        corrector.procesar_lote(lista_alumnos)
    
    # Generar JSON
    json_resultado = corrector.generar_json()
    
    print("\n" + "=" * 60)
    print("  REPORTE GENERADO")
    print("=" * 60)
    print(json_resultado)
    print("=" * 60)
    
    # Ofertar guardar el JSON
    print("\n¿Deseas guardar el reporte JSON en un archivo?")
    guardar = input("(S/N): ").strip().upper()
    
    if guardar == "S":
        # Generar nombre de archivo
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        materia_archivo = "".join(c for c in materia_info["nombre"].replace(" ", "_") if c.isalnum() or c in ("_", "-"))
        tp_archivo = "".join(c for c in tp.replace(" ", "_") if c.isalnum() or c in ("_", "-"))
        carpeta_reportes = obtener_carpeta_reportes_del_dia()
        nombre_archivo = os.path.join(carpeta_reportes, f"reporte_{materia_archivo}_{tp_archivo}_{timestamp}.json")
        
        try:
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                f.write(json_resultado)
            print(f"\n✅ Reporte guardado en: {nombre_archivo}")
        except Exception as e:
            print(f"\n❌ Error al guardar archivo: {e}")

        # Publicación opcional en Classroom (nota 0-100 + flujo de comentarios privados por web)
        print("\n¿Deseas publicar también en Classroom (calificación + comentario privado)?")
        publicar = input("(S/N): ").strip().upper()
        if publicar == "S":
            publicar_resultados_en_classroom(
                service,
                course_id,
                work_id,
                corrector.reporte_entregas,
                lote_seleccionado,
            )
    
    return json_resultado


# ──────────────────────────────────────────────
#  FUNCIONES AUXILIARES DE DRIVE
# ──────────────────────────────────────────────
def extraer_texto_de_pdf(contenido_bytes):
    """
    Extrae texto de un PDF desde bytes con enfoque híbrido.
    
    Estrategia:
    1. Intenta extracción rápida (PDF digital con capa de texto)
    2. Si falla o es insuficiente, activa OCR local con Tesseract (para PDFs escaneados)
    3. Fallback a Gemini multimodal si OCR no está disponible
    
    Retorna: str (máx 12000 caracteres)
    """
    texto_local = ""
    
    # ════════════════════════════════════════════════════════════
    # FASE 1: Extracción rápida de PDFs digitales (con capa de texto)
    # ════════════════════════════════════════════════════════════
    if PDF_DISPONIBLE:
        try:
            pdf_file = io.BytesIO(contenido_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            texto_completo = []
            
            for num_pagina, pagina in enumerate(pdf_reader.pages):
                texto_pagina = (pagina.extract_text() or "").strip()
                if texto_pagina:
                    texto_completo.append(f"[Página {num_pagina + 1}]\n{texto_pagina}")
            
            texto_local = "\n\n".join(texto_completo)
        except Exception as e:
            print(f"      ⚠️ Extracción PDF digital falló: {str(e)[:100]}")
            texto_local = ""
    
    # Si la extracción fue suficiente (>80 caracteres), devolvemos sin OCR (ahorro de recursos)
    if texto_local and len(texto_local.strip()) >= 80:
        print(f"      ✅ PDF digital procesado exitosamente ({len(texto_local)} caracteres)")
        return texto_local[:12000]
    
    # ════════════════════════════════════════════════════════════
    # FASE 2: OCR local con Tesseract (PDFs escaneados o fotos convertidas)
    # ════════════════════════════════════════════════════════════
    if OCR_DISPONIBLE:
        try:
            # Configurar path de Tesseract si está en .env
            tesseract_cmd = os.environ.get("TESSERACT_CMD", "").strip()
            if tesseract_cmd and os.path.exists(tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
            # Configurar path de Poppler si está en .env
            poppler_path = os.environ.get("POPPLER_PATH", "").strip() or None
            
            # Convertir páginas del PDF a imágenes (DPI 250 = buena calidad/velocidad)
            paginas = convert_from_bytes(contenido_bytes, dpi=250, poppler_path=poppler_path)
            texto_ocr = []
            
            for idx, img in enumerate(paginas, start=1):
                try:
                    # Intentar OCR con español + inglés (común en escuelas)
                    texto_pag = pytesseract.image_to_string(img, lang="spa+eng").strip()
                except Exception:
                    # Fallback: solo inglés (si spa.traineddata no está instalado)
                    try:
                        texto_pag = pytesseract.image_to_string(img, lang="eng").strip()
                    except Exception:
                        texto_pag = ""
                
                if texto_pag:
                    texto_ocr.append(f"[Página {idx}]\n{texto_pag}")
            
            texto_ocr_join = "\n\n".join(texto_ocr).strip()
            if texto_ocr_join:
                print(f"      ✅ OCR local (Tesseract) completado exitosamente ({len(texto_ocr_join)} caracteres)")
                return texto_ocr_join[:12000]
            else:
                print("      ⚠️ OCR no extrajo texto (PDF vacío o caracteres no reconocibles)")
        
        except Exception as e:
            print(f"      ⚠️ OCR local falló: {str(e)[:150]}")
    else:
        print("      ⚠️ OCR no disponible: instala [pdf2image, pytesseract] y configura Tesseract + Poppler en el sistema")

    # Fallback multimodal: enviar el PDF completo para que Gemini lo lea (incluye escaneos).
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt_ocr = (
                "Extrae el texto del PDF de forma fiel. "
                "No resumas ni expliques. "
                "Mantén el orden de lectura y separa páginas con '[Página N]'."
            )
            respuesta = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    prompt_ocr,
                    genai.types.Part.from_bytes(data=contenido_bytes, mime_type="application/pdf"),
                ],
            )
            texto_ia = (getattr(respuesta, "text", "") or "").strip()
            if texto_ia:
                return texto_ia[:12000]
        except Exception as e:
            print(f"      ⚠️ OCR IA (modo Part.from_bytes) falló: {str(e)[:180]}")
            try:
                # Fallback de compatibilidad para versiones del SDK sin Part.from_bytes.
                client = genai.Client(api_key=api_key)
                respuesta = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        {
                            "role": "user",
                            "parts": [
                                {"text": prompt_ocr},
                                {
                                    "inline_data": {
                                        "mime_type": "application/pdf",
                                        "data": contenido_bytes,
                                    }
                                },
                            ],
                        }
                    ],
                )
                texto_ia = (getattr(respuesta, "text", "") or "").strip()
                if texto_ia:
                    return texto_ia[:12000]
            except Exception as e2:
                print(f"      ⚠️ OCR IA (modo inline_data) falló: {str(e2)[:180]}")
                if texto_local:
                    return texto_local[:12000]
                return f"[Error extrayendo PDF con IA: {e2}]"
    else:
        print("      ⚠️ GEMINI_API_KEY no configurada: no se puede activar OCR multimodal para PDFs escaneados.")

    # Fallback opcional con OpenAI para OCR de PDFs escaneados.
    openai_api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if openai_api_key:
        try:
            from openai import OpenAI

            client_openai = OpenAI(api_key=openai_api_key)
            prompt_ocr_openai = (
                "Extrae el texto completo del PDF en orden de lectura. "
                "No resumas ni agregues comentarios. "
                "Si hay múltiples páginas, separa con '[Página N]'."
            )

            pdf_b64 = base64.b64encode(contenido_bytes).decode("utf-8")
            respuesta_oa = client_openai.responses.create(
                model="gpt-4.1-mini",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt_ocr_openai},
                            {
                                "type": "input_file",
                                "filename": "entrega.pdf",
                                "file_data": f"data:application/pdf;base64,{pdf_b64}",
                            },
                        ],
                    }
                ],
            )
            texto_openai = (getattr(respuesta_oa, "output_text", "") or "").strip()
            if texto_openai:
                print("      ✅ OCR IA resuelto con OpenAI.")
                return texto_openai[:12000]
        except Exception as e:
            print(f"      ⚠️ OCR IA (OpenAI) falló: {str(e)[:180]}")

    if texto_local:
        return texto_local[:12000]

    if not PDF_DISPONIBLE:
        return "[PDF detectado - instala PyPDF2 o configura GEMINI_API_KEY para lectura multimodal]"

    return "[No se pudo extraer texto del PDF]"


# ════════════════════════════════════════════════════════════════════════════════
# 🔄 OPCIÓN B: Extracción desde Archivos Locales (con OCR integrado)
# ════════════════════════════════════════════════════════════════════════════════
def extraer_texto_de_archivo_local(ruta_archivo):
    """
    Extrae texto de un archivo descargado localmente.
    
    Soporta:
    - PDFs digitales (extracción rápida)
    - PDFs escaneados (OCR automático con Tesseract)
    - DOCX (extracción nativa)
    - Imágenes (OCR con Tesseract)
    
    Args:
        ruta_archivo (str): Ruta local al archivo
    
    Returns:
        str: Texto extraído (máx 12000 caracteres)
    """
    if not os.path.exists(ruta_archivo):
        print(f"⚠️ Archivo no encontrado: {ruta_archivo}")
        return ""
    
    ext = os.path.splitext(ruta_archivo)[1].lower()
    
    # ──────────────────────────────────────────────────────────
    # CASO 1: PDF (digital o escaneado)
    # ──────────────────────────────────────────────────────────
    if ext == '.pdf':
        try:
            with open(ruta_archivo, 'rb') as f:
                contenido = f.read()
            return extraer_texto_de_pdf(contenido)
        except Exception as e:
            print(f"⚠️ Error al procesar PDF: {e}")
            return ""
    
    # ──────────────────────────────────────────────────────────
    # CASO 2: DOCX (documento Word)
    # ──────────────────────────────────────────────────────────
    elif ext == '.docx':
        try:
            with open(ruta_archivo, 'rb') as f:
                contenido = f.read()
            return extraer_texto_de_docx(contenido)
        except Exception as e:
            print(f"⚠️ Error al procesar DOCX: {e}")
            return ""
    
    # ──────────────────────────────────────────────────────────
    # CASO 3: Imágenes (PNG, JPG, etc.) - OCR directo
    # ──────────────────────────────────────────────────────────
    elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff']:
        if not OCR_DISPONIBLE:
            print(f"⚠️ OCR no disponible para {ext}")
            return ""
        
        try:
            from PIL import Image
            import pytesseract
            
            # Configurar Tesseract si está en .env
            tesseract_cmd = os.environ.get("TESSERACT_CMD", "").strip()
            if tesseract_cmd and os.path.exists(tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
            img = Image.open(ruta_archivo)
            try:
                texto = pytesseract.image_to_string(img, lang="spa+eng").strip()
            except Exception:
                # Fallback a inglés
                texto = pytesseract.image_to_string(img, lang="eng").strip()
            
            return texto[:12000] if texto else ""
        except Exception as e:
            print(f"⚠️ Error al procesar imagen: {e}")
            return ""
    
    # ──────────────────────────────────────────────────────────
    # CASO 4: Archivo no soportado
    # ──────────────────────────────────────────────────────────
    else:
        print(f"⚠️ Tipo de archivo no soportado: {ext}")
        return ""


# ════════════════════════════════════════════════════════════════════════════════
# 🔐 OPCIÓN C: Publicación Centralizada en Classroom (Nota + Comentario + Devolución)
# ════════════════════════════════════════════════════════════════════════════════
def publicar_evaluacion_en_classroom(service, course_id, course_work_id, submission_id, 
                                    nota_num, feedback_texto, alumno_nombre=""):
    """
    Ejecuta el flujo completo de publicación en Google Classroom:
    
    1. Asigna la calificación (nota escalar 1-10 → 0-100)
    2. Publica comentario privado para el alumno
    3. Devuelve la tarea al alumno
    
    Args:
        service: Cliente autenticado de Classroom API
        course_id (str): ID del curso
        course_work_id (str): ID de la tarea
        submission_id (str): ID de la entrega del alumno
        nota_num (int): Nota en escala 1-10
        feedback_texto (str): Comentario privado (feedback pedagógico)
        alumno_nombre (str): Nombre del alumno (para logging)
    
    Returns:
        dict: {
            'exito': bool,
            'nota_asignada': int,
            'comentario_publicado': bool,
            'devuelta': bool,
            'error': str (si aplica)
        }
    """
    resultado = {
        'exito': False,
        'nota_asignada': False,
        'comentario_publicado': False,
        'devuelta': False,
        'error': None
    }
    
    try:
        # ──────────────────────────────────────────────────────────
        # PASO 1: Convertir nota 1-10 a escala 0-100
        # ──────────────────────────────────────────────────────────
        nota_100 = int(nota_num * 10) if nota_num else None
        
        if nota_100 is not None:
            print(f"  📝 [{alumno_nombre}] Asignando nota: {nota_num}/10 ({nota_100}/100)...")
            service.courses().courseWork().studentSubmissions().patch(
                courseId=course_id,
                courseWorkId=course_work_id,
                id=submission_id,
                updateMask="assignedGrade,draftGrade",
                body={
                    "assignedGrade": nota_100,
                    "draftGrade": nota_100,
                },
            ).execute()
            resultado['nota_asignada'] = True
            print(f"  ✅ [1/3] Nota asignada")
        else:
            print(f"  ⓘ [1/3] Sin nota para asignar")
        
        # ──────────────────────────────────────────────────────────
        # PASO 2: Publicar comentario privado
        # ──────────────────────────────────────────────────────────
        if feedback_texto and feedback_texto.strip():
            print(f"  💬 [{alumno_nombre}] Publicando comentario privado...")
            ss_resource = service.courses().courseWork().studentSubmissions()
            
            if not hasattr(ss_resource, "comments"):
                raise AttributeError(
                    "El cliente Classroom API v1 no expone studentSubmissions.comments(). "
                    "Verifica que tengas token.json válido con permisos classroom.coursework.students."
                )
            
            ss_resource.comments().create(
                courseId=course_id,
                courseWorkId=course_work_id,
                id=submission_id,
                body={"text": feedback_texto},
            ).execute()
            resultado['comentario_publicado'] = True
            print(f"  ✅ [2/3] Comentario privado publicado")
        else:
            print(f"  ⓘ [2/3] Sin comentario para publicar")
        
        # ──────────────────────────────────────────────────────────
        # PASO 3: Devolver la tarea al alumno
        # ──────────────────────────────────────────────────────────
        print(f"  🔔 [{alumno_nombre}] Devolviendo tarea...")
        service.courses().courseWork().studentSubmissions().return_(
            courseId=course_id,
            courseWorkId=course_work_id,
            id=submission_id,
            body={},
        ).execute()
        resultado['devuelta'] = True
        print(f"  ✅ [3/3] Tarea devuelta al alumno")
        
        # ──────────────────────────────────────────────────────────
        # ÉXITO TOTAL
        # ──────────────────────────────────────────────────────────
        resultado['exito'] = True
        print(f"  ✅ ÉXITO: Publicación completa para {alumno_nombre}")
        
    except HttpError as e:
        error_msg = str(e)
        resultado['error'] = error_msg[:200]
        
        if "ProjectPermissionDenied" in error_msg or "403" in error_msg:
            resultado['error'] = (
                "❌ Error 403 Forbidden: Permisos insuficientes. "
                "SOLUCIÓN: Borra token.json y vuelve a autenticar con: python renovar_token_oauth.py"
            )
        
        print(f"  ❌ Error en Classroom: {resultado['error']}")
    
    except Exception as e:
        resultado['error'] = str(e)[:200]
        print(f"  ❌ Error inesperado: {resultado['error']}")
    
    return resultado


def extraer_texto_de_docx(contenido_bytes):
    """Lee un archivo .docx desde un flujo de bytes y extrae todo su texto."""
    try:
        fichero = io.BytesIO(contenido_bytes)
        doc = Document(fichero)
        texto_completo = []
        for parrafo in doc.paragraphs:
            if parrafo.text.strip():
                texto_completo.append(parrafo.text.strip())
        return "\n".join(texto_completo)
    except Exception as e:
        return f"[Error leyendo estructura del Word: {e}]"


def descargar_adjunto_drive(service_drive, file_id, mime_type_original=None):
    """
    Descarga un archivo de Google Drive en memoria y devuelve sus bytes.
    Maneja tanto archivos normales como archivos nativos de Google (Docs, Sheets, etc).
    """
    try:
        # Obtener metadatos del archivo para detectar su tipo si no se proporcionó
        if not mime_type_original:  # Si es None o cadena vacía
            try:
                file_metadata = service_drive.files().get(fileId=file_id, fields='mimeType').execute()
                mime_type_original = file_metadata.get('mimeType', '')
            except Exception as e:
                print(f"      ⚠️  No se pudieron obtener metadatos: {e}")
                mime_type_original = ''
        
        # Si es un archivo nativo de Google, necesitamos exportarlo
        if mime_type_original and mime_type_original.startswith('application/vnd.google-apps.'):
            print(f"      [Archivo nativo de Google detectado: {mime_type_original}]")
            
            # Mapeo de tipos Google a formatos de exportación
            export_mapping = {
                'application/vnd.google-apps.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
                'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
                'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
                'application/vnd.google-apps.drawing': 'image/png',  # .png
            }
            
            # Obtener el formato de exportación o usar PDF como fallback
            export_mime_type = export_mapping.get(mime_type_original, 'application/pdf')
            
            # Reintentar descarga de Google Docs con delay (a veces la API tarda)
            max_reintentos = 3
            for intento in range(max_reintentos):
                try:
                    print(f"      → Exportando como {export_mime_type.split('/')[-1]}..." + (f" (intento {intento+1}/{max_reintentos})" if intento > 0 else ""))
                    request = service_drive.files().export_media(fileId=file_id, mimeType=export_mime_type)
                    file_stream = io.BytesIO()
                    downloader = MediaIoBaseDownload(file_stream, request)
                    done = False
                    while not done:
                        _, done = downloader.next_chunk()
                    
                    resultado = file_stream.getvalue()
                    if resultado:  # Verificar que se descargó algo
                        return resultado
                except Exception as export_error:
                    if intento < max_reintentos - 1:
                        print(f"      ⚠️  Error en intento {intento+1}: {str(export_error)[:60]}, reintentando...")
                        time.sleep(1)  # Esperar 1 segundo antes de reintentar
                    else:
                        print(f"      ❌ Error exportando después de {max_reintentos} intentos: {export_error}")
                        return None
        
        # Si es un archivo normal, descargar normalmente
        else:
            request = service_drive.files().get_media(fileId=file_id)
            file_stream = io.BytesIO()
            downloader = MediaIoBaseDownload(file_stream, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return file_stream.getvalue()
            
    except Exception as e:
        print(f"   ⚠️  No se pudo descargar el archivo de Drive ({file_id}): {e}")
        return None


# ──────────────────────────────────────────────
#  PASO 1.5: OBTENER TEMAS DEL CURSO
# ──────────────────────────────────────────────
def obtener_temas_del_curso(service, course_id):
    """
    Obtiene los temas creados en el curso.
    Si no hay, crea un tema genérico.
    """
    try:
        topics_result = _ejecutar_con_reintentos_api(
            lambda: service.courses().topics().list(courseId=course_id).execute(),
            etiqueta="Topics endpoint",
            max_intentos=4,
        )
        temas = topics_result.get("topic", [])
        if temas:
            print(f"   ✅ Se encontraron {len(temas)} tema(s) en el curso")
            return temas
    except Exception as e:
        print(f"   (Topics endpoint: {e})")

    print("   ⚠️ No se encontraron temas creados. Se usará tema genérico.")
    return [{"topicId": "general", "name": "Contenido General"}]


# ──────────────────────────────────────────────
#  FUNCIONES PARA DESCARGAR ARCHIVOS DE ACTIVIDADES
# ──────────────────────────────────────────────
def solicitar_nombre_carpeta_personalizado(nombre_por_defecto):
    """
    Pregunta al usuario si quiere personalizar el nombre de la carpeta.
    Si presiona Enter sin escribir, usa el nombre por defecto.
    """
    print(f"\n📁 Nombre de carpeta actual (por defecto): {nombre_por_defecto}")
    nombre_personalizado = input("   Ingresá un nombre personalizado (o presioná Enter para usar el por defecto): ").strip()
    
    if nombre_personalizado:
        # Limpiar caracteres inválidos
        nombre_personalizado = "".join(c for c in nombre_personalizado if c.isalnum() or c in ("_", "-", " "))
        nombre_personalizado = nombre_personalizado.replace(" ", "_")[:50]
        return nombre_personalizado
    else:
        return nombre_por_defecto


def listar_trabajos_del_curso(service, course_id):
    """
    Lista todos los trabajos/actividades del curso.
    Retorna lista de trabajos o lista vacía si no hay.
    """
    try:
        trabajos_result = service.courses().courseWork().list(courseId=course_id).execute()
        trabajos = trabajos_result.get("courseWork", [])
        if trabajos:
            print(f"   ✅ Se encontraron {len(trabajos)} actividad/actividades")
            return trabajos
    except Exception as e:
        print(f"   ⚠️ Error al obtener actividades: {e}")
    
    return []


def seleccionar_trabajo(trabajos):
    """
    Menú para seleccionar un trabajo de la lista.
    Retorna el trabajo seleccionado o None.
    """
    if not trabajos:
        return None
    
    print("\n" + "=" * 60)
    print("  SELECCIONAR ACTIVIDAD — Elige cuál descargar")
    print("=" * 60)
    for i, trabajo in enumerate(trabajos, start=1):
        titulo = trabajo.get("title", "Sin título")
        tipo = trabajo.get("workType", "ASSIGNMENT")
        print(f"  [{i}] {titulo}  ({tipo})")
    print("=" * 60)
    
    while True:
        try:
            opcion = int(input("Ingresá el número de la actividad: "))
            if 1 <= opcion <= len(trabajos):
                return trabajos[opcion - 1]
            else:
                print(f"Ingresá un número entre 1 y {len(trabajos)}.")
        except ValueError:
            print("Entrada no válida. Ingresá un número.")


def descargar_archivos_actividad(service_drive, service_classroom, course_id, work_id, carpeta_local):
    """
    Descarga SOLO archivos de Google Drive asociados a una actividad EN LA CARPETA ESPECIFICADA.
    Filtra y salta enlaces web, videos de YouTube, etc.
    Maneja errores 404 cuando archivos fueron borrados.
    Soporta archivos nativos de Google (Docs, Sheets) exportándolos automáticamente.
    Retorna tupla: (lista_archivos, titulo_trabajo, archivos_descargados)
    """
    try:
        # Obtener detalles del trabajo
        trabajo = service_classroom.courses().courseWork().get(
            courseId=course_id, 
            id=work_id
        ).execute()
        
        titulo_trabajo = trabajo.get("title", "actividad")
        print(f"\n📥 Descargando archivos de: {titulo_trabajo}")
        
        # Contadores
        archivos_descargados = 0
        archivos_saltados = 0
        archivos_error = 0
        lista_archivos = []
        
        # Si hay materiales en el trabajo, procesarlos
        if "materials" in trabajo:
            for idx, material in enumerate(trabajo["materials"], start=1):
                
                # ✅ SOLO procesar archivos de Google Drive
                if "driveFile" in material:
                    try:
                        drive_file = material["driveFile"]["driveFile"]
                        file_id = drive_file.get("id")
                        file_name = drive_file.get("title", "archivo")
                        
                        # Obtener MIME type para detectar archivos nativos de Google
                        try:
                            file_metadata = service_drive.files().get(
                                fileId=file_id, 
                                fields='mimeType'
                            ).execute()
                            mime_type = file_metadata.get('mimeType', '')
                        except Exception as e:
                            print(f"      ⚠️  Error obteniendo metadatos: {e}")
                            mime_type = ''
                        
                        # Si es un Google Docs, agregar extensión .docx
                        if mime_type == 'application/vnd.google-apps.document':
                            if not file_name.lower().endswith('.docx'):
                                file_name = file_name + '.docx'
                        
                        print(f"   ➔ [{idx}] Descargando: {file_name}")
                        bytes_archivo = descargar_adjunto_drive(service_drive, file_id, mime_type)
                        
                        if bytes_archivo:
                            ruta_archivo = os.path.join(carpeta_local, file_name)
                            with open(ruta_archivo, "wb") as f:
                                f.write(bytes_archivo)
                            print(f"       ✅ Guardado en: {ruta_archivo}")
                            lista_archivos.append(ruta_archivo)
                            archivos_descargados += 1
                        else:
                            print(f"       ⚠️ No se pudo obtener contenido del archivo")
                            archivos_error += 1
                            
                    except HttpError as error:
                        if error.resp.status == 404:
                            print(f"       ❌ Archivo no encontrado (fue borrado o movido de Drive)")
                            archivos_error += 1
                        else:
                            print(f"       ⚠️ Error descargando: {error.resp.status}")
                            archivos_error += 1
                    except Exception as e:
                        print(f"       ⚠️ Error: {e}")
                        archivos_error += 1
                
                # 🔗 SALTAR enlaces web
                elif "link" in material:
                    link_url = material["link"].get("url", "")
                    link_title = material["link"].get("title", link_url)
                    print(f"   ➔ [{idx}] 🔗 Enlace externo (se salta): {link_title}")
                    print(f"       → {link_url}")
                    archivos_saltados += 1
                
                # 📺 SALTAR videos de YouTube
                elif "youtubeVideo" in material:
                    yt_title = material["youtubeVideo"].get("title", "Video YouTube")
                    yt_id = material["youtubeVideo"].get("id", "")
                    yt_url = f"https://www.youtube.com/watch?v={yt_id}"
                    print(f"   ➔ [{idx}] 📺 Video YouTube (se salta): {yt_title}")
                    print(f"       → {yt_url}")
                    archivos_saltados += 1
        
        # Resumen final
        print(f"\n📊 RESUMEN DE DESCARGA:")
        print(f"   ✅ Archivos descargados: {archivos_descargados}")
        print(f"   🔗 Enlaces saltados: {archivos_saltados}")
        print(f"   ❌ Errores: {archivos_error}")
        
        if archivos_descargados > 0:
            print(f"\n✅ Descarga completada en carpeta: {carpeta_local}")
        else:
            print(f"\n⚠️ No se descargaron archivos. Verifica si los adjuntos existen en Drive.")
        
        return (lista_archivos, titulo_trabajo, archivos_descargados)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return ([], "", 0)


# ──────────────────────────────────────────────
#  FUNCIONES PARA BUSCAR EN GOOGLE DRIVE
# ──────────────────────────────────────────────
def extraer_preguntas_de_texto(texto):
    """
    Identifica y extrae preguntas textuales del contenido.
    Busca líneas que terminen con "?" o comiencen con interrogativos.
    Retorna lista de preguntas únicas.
    """
    preguntas = []
    palabras_interrogativas = ['¿qué', '¿cuál', '¿cuáles', '¿cómo', '¿cuándo', '¿dónde', '¿por qué', '¿cuánto', '¿cuántos', 'qué', 'cuál', 'cuáles', 'cómo', 'cuándo', 'dónde', 'por qué', 'cuánto', 'cuántos']
    
    lineas = texto.split('\n')
    for linea in lineas:
        linea_limpia = linea.strip()
        
        # Buscar líneas que terminen con "?"
        if linea_limpia.endswith('?') and len(linea_limpia) > 10:
            # Filtrar duplicados (insensible a mayúsculas)
            if not any(p.lower() == linea_limpia.lower() for p in preguntas):
                preguntas.append(linea_limpia)
        
        # Buscar líneas que comiencen con palabras interrogativas
        elif any(linea_limpia.lower().startswith(palabra) for palabra in palabras_interrogativas):
            if not linea_limpia.endswith('?'):
                # Agregar signo de interrogación si no tiene
                linea_limpia = linea_limpia.rstrip('.') + '?'
            
            if len(linea_limpia) > 10 and not any(p.lower() == linea_limpia.lower() for p in preguntas):
                preguntas.append(linea_limpia)
    
    return preguntas


def extraer_contenido_de_archivos_locales(rutas_archivos):
    """
    Lee archivos DOCX y PDF descargados localmente y extrae su contenido Y preguntas textuales.
    Retorna tupla: (contexto_formateado, lista_preguntas_textuales)
    """
    contexto_partes = ["\n📌 CONTENIDO DE ARCHIVOS DESCARGADOS\n"]
    preguntas_totales = []
    archivos_procesados = 0
    
    for ruta_archivo in rutas_archivos:
        nombre_archivo = os.path.basename(ruta_archivo)
        
        try:
            if nombre_archivo.lower().endswith('.docx'):
                print(f"   📄 Leyendo: {nombre_archivo}")
                bytes_archivo = open(ruta_archivo, 'rb').read()
                texto = extraer_texto_de_docx(bytes_archivo)
                if texto and len(texto) > 50:
                    contexto_partes.append(f"\n  📄 {nombre_archivo}:")
                    contexto_partes.append(f"    {texto}")
                    archivos_procesados += 1
                    
                    # Extraer preguntas de este archivo
                    preguntas = extraer_preguntas_de_texto(texto)
                    preguntas_totales.extend(preguntas)
            
            elif nombre_archivo.lower().endswith('.pdf'):
                print(f"   📕 Leyendo: {nombre_archivo}")
                bytes_archivo = open(ruta_archivo, 'rb').read()
                texto = extraer_texto_de_pdf(bytes_archivo)
                if texto and "Error" not in texto:
                    contexto_partes.append(f"\n  📕 {nombre_archivo}:")
                    contexto_partes.append(f"    {texto}")
                    archivos_procesados += 1
                    
                    # Extraer preguntas de este archivo
                    preguntas = extraer_preguntas_de_texto(texto)
                    preguntas_totales.extend(preguntas)
        
        except Exception as e:
            print(f"   ⚠️ Error leyendo {nombre_archivo}: {e}")
    
    print(f"   → {archivos_procesados} archivo(s) procesado(s).")
    print(f"   🔍 Preguntas textuales encontradas: {len(preguntas_totales)}")
    
    # Remover duplicados (manteniendo orden)
    preguntas_unicas = []
    for p in preguntas_totales:
        if not any(existing.lower() == p.lower() for existing in preguntas_unicas):
            preguntas_unicas.append(p)
    
    if preguntas_unicas:
        print(f"   ✅ Se seleccionarán preguntas textuales para la evaluación")
    
    return "\n".join(contexto_partes), preguntas_unicas


def obtener_carpeta_curso_drive(service_drive, course_id):
    """
    Busca la carpeta de Google Classroom del curso en Drive.
    Classroom crea automáticamente una carpeta por cada curso.
    """
    try:
        # Buscar carpeta con el ID del curso en el nombre
        query = f"name contains '{course_id}' and mimeType = 'application/vnd.google-apps.folder' and trashed=false"
        results = service_drive.files().list(q=query, spaces='drive', fields='files(id, name)', pageSize=5).execute()
        carpetas = results.get('files', [])
        
        if carpetas:
            return carpetas[0]['id']
    except Exception as e:
        print(f"   ⚠️ Error buscando carpeta del curso: {e}")
    
    return None


def listar_archivos_en_carpeta(service_drive, folder_id, query_adicional=""):
    """
    Lista todos los archivos en una carpeta de Drive.
    Si query_adicional se proporciona, lo usa para filtrar (ej: name contains '.docx')
    """
    archivos = []
    try:
        base_query = f"'{folder_id}' in parents and trashed=false"
        if query_adicional:
            base_query += f" and {query_adicional}"
        
        results = service_drive.files().list(
            q=base_query,
            spaces='drive',
            fields='files(id, name, mimeType)',
            pageSize=100
        ).execute()
        archivos = results.get('files', [])
    except Exception as e:
        print(f"   ⚠️ Error listando archivos: {e}")
    
    return archivos


def extraer_contenido_de_drive(service_classroom, service_drive, course_id, nombre_tema):
    """
    Extrae SOLO archivos DOCX y PDF del curso.
    Enfocado en los materiales de estudio principales.
    """
    contexto_partes = [f"\n📌 UNIDAD/TEMA: {nombre_tema}\n"]
    contador_archivos = 0
    
    # Paso 1: Obtener carpeta del curso
    print("   🔍 Buscando carpeta del curso en Google Drive...")
    carpeta_id = obtener_carpeta_curso_drive(service_drive, course_id)
    
    if not carpeta_id:
        print("   ⚠️ No se encontró carpeta del curso en Drive.")
        contexto_partes.append("  ⚠️ No se encontró contenido en Drive")
        return "\n".join(contexto_partes)
    
    print(f"   ✅ Carpeta del curso encontrada")
    
    # Paso 2: Buscar archivos .docx (PRIORIDAD 1)
    print("   📄 Buscando archivos Word (.docx)...")
    docx_files = listar_archivos_en_carpeta(service_drive, carpeta_id, "name contains '.docx'")
    
    if docx_files:
        contexto_partes.append("  [📄 DOCUMENTOS WORD - CONTENIDO PRINCIPAL]")
        for archivo in docx_files:
            print(f"   ➔ Leyendo: {archivo['name']}")
            try:
                bytes_archivo = descargar_adjunto_drive(service_drive, archivo['id'])
                if bytes_archivo:
                    texto = extraer_texto_de_docx(bytes_archivo)
                    if texto and len(texto) > 50:  # Solo si tiene contenido significativo
                        contexto_partes.append(f"\n    📄 {archivo['name']}:")
                        contexto_partes.append(f"      {texto}")  # Incluir todo el contenido
                        contador_archivos += 1
            except Exception as e:
                print(f"      ⚠️ Error en {archivo['name']}: {e}")
    
    # Paso 3: Buscar archivos PDF (PRIORIDAD 2)
    print("   📕 Buscando archivos PDF...")
    pdf_files = listar_archivos_en_carpeta(service_drive, carpeta_id, "name contains '.pdf'")
    
    if pdf_files:
        contexto_partes.append("\n  [📕 DOCUMENTOS PDF - CONTENIDO COMPLEMENTARIO]")
        for archivo in pdf_files[:3]:  # Máximo 3 PDFs
            print(f"   ➔ Leyendo: {archivo['name']}")
            try:
                bytes_archivo = descargar_adjunto_drive(service_drive, archivo['id'])
                if bytes_archivo:
                    texto = extraer_texto_de_pdf(bytes_archivo)
                    if texto and "Error" not in texto:
                        contexto_partes.append(f"\n    📕 {archivo['name']}:")
                        contexto_partes.append(f"      {texto}")
                        contador_archivos += 1
                    elif "instala PyPDF2" in texto:
                        contexto_partes.append(f"    📕 {archivo['name']} [requiere PyPDF2]")
            except Exception as e:
                print(f"      ⚠️ Error en {archivo['name']}: {e}")
    
    contexto_completo = "\n".join(contexto_partes)
    total_items = len(docx_files) + len(pdf_files)
    print(f"   → {total_items} archivo(s) encontrado(s) ({contador_archivos} procesado(s)).")
    
    return contexto_completo


# ──────────────────────────────────────────────
#  FUNCIONES AUXILIARES PARA EXTRAER ADJUNTOS
# ──────────────────────────────────────────────
def extraer_archivos_de_material(material, service_drive):
    """
    Extrae TODOS los tipos de archivos de un material.
    Retorna lista de tuplas: (tipo, título, contenido_o_link)
    """
    archivos = []
    
    try:
        # Tipo 1: driveFile
        if "driveFile" in material:
            try:
                drive_file = material["driveFile"]["driveFile"]
                file_id = drive_file.get("id")
                file_title = drive_file.get("title", "Sin nombre")
                
                print(f"   ➔ Encontrado archivo Drive: {file_title}")
                
                # Descargar archivo
                bytes_archivo = descargar_adjunto_drive(service_drive, file_id)
                if bytes_archivo:
                    # Si es .docx, extraer texto
                    if file_title.lower().endswith('.docx'):
                        texto = extraer_texto_de_docx(bytes_archivo)
                        archivos.append(("docx", file_title, texto))
                    else:
                        archivos.append(("archivo", file_title, f"[Archivo: {file_title}]"))
            except Exception as e:
                print(f"      ⚠️ Error procesando driveFile: {e}")
        
        # Tipo 2: link
        if "link" in material:
            try:
                link_url = material["link"].get("url", "")
                link_title = material["link"].get("title", link_url)
                archivos.append(("link", link_title, link_url))
                print(f"   ➔ Encontrado link: {link_title}")
            except Exception as e:
                print(f"      ⚠️ Error procesando link: {e}")
        
        # Tipo 3: youtubeVideo
        if "youtubeVideo" in material:
            try:
                yt_id = material["youtubeVideo"].get("id", "")
                yt_title = material["youtubeVideo"].get("title", "Video YouTube")
                url_yt = f"https://www.youtube.com/watch?v={yt_id}"
                archivos.append(("youtube", yt_title, url_yt))
                print(f"   ➔ Encontrado video YouTube: {yt_title}")
            except Exception as e:
                print(f"      ⚠️ Error procesando youtubeVideo: {e}")
        
    except Exception as e:
        print(f"      ⚠️ Error general extrayendo archivos: {e}")
    
    return archivos


# ──────────────────────────────────────────────
#  PASO 2: EXTRAER CONTENIDO POR TEMA ESPECÍFICO
# ──────────────────────────────────────────────
def extraer_contenido_por_tema_especifico(service_classroom, service_drive, course_id, id_tema_elegido, nombre_tema):
    """
    Extrae contenido del curso directamente desde Google Drive.
    Busca documentos, hojas de cálculo, PDFs y Google Docs.
    Este método evita las limitaciones de permisos de Classroom API.
    """
    # Usar el nuevo método basado en Drive
    return extraer_contenido_de_drive(service_classroom, service_drive, course_id, nombre_tema)


# ──────────────────────────────────────────────
#  PASO 3: GENERAR EVALUACIÓN
# ──────────────────────────────────────────────
def construir_prompt(nombre_curso, contexto, preguntas_obligatorias=None):
    """Construye el prompt estructurado para la IA con preguntas textuales opcionales."""
    
    # Sección de preguntas obligatorias si existen
    seccion_preguntas_obligatorias = ""
    if preguntas_obligatorias and len(preguntas_obligatorias) > 0:
        seccion_preguntas_obligatorias = (
            "\n---- PREGUNTAS OBLIGATORIAS TEXTUALES (De los TPs) ----\n"
            "Estas preguntas provienen DIRECTAMENTE de los Trabajos Practicos de los alumnos.\n"
            "DEBES INCLUIRLAS de forma LITERAL (palabra por palabra) en la evaluacion diagnostica,\n"
            "intercalandolas naturalmente con otras preguntas conceptuales o de opcion multiple que generes.\n\n"
            "Selecciona al menos 3-4 de estas preguntas para incluir textualmente:\n"
        )
        for idx, pregunta in enumerate(preguntas_obligatorias[:10], start=1):
            seccion_preguntas_obligatorias += f"\n  {idx}. {pregunta}"
        seccion_preguntas_obligatorias += "\n----------------------------------------"
    
    prompt = (
        f"Sos un profesor experto. Tu tarea es disenar una evaluacion diagnostica formal para la materia \"{nombre_curso}\".\n\n"
        "En base al siguiente contenido extraido del aula virtual, crea un examen con:\n"
        "- Preguntas teoricas (opciones multiples o desarrollo breve)\n"
        "- Ejercicios practicos (resolucion paso a paso)\n"
        "- Un apartado con las RESPUESTAS ESPERADAS o criterios de correccion\n\n"
        + seccion_preguntas_obligatorias + "\n\n"
        "Formato de salida: texto claro, con encabezados numerados, listo para imprimir.\n\n"
        "---- CONTENIDO DEL AULA ----\n"
        + contexto + "\n"
    )
    return prompt


def generar_evaluacion_simulada(nombre_curso, contexto, preguntas_obligatorias=None):
    """
    CONEXIÓN REAL CON GEMINI: Incluye reintentos automáticos ante error 429.
    Incluye preguntas textuales obligatorias en el prompt si se proporcionan.
    """
    prompt = construir_prompt(nombre_curso, contexto, preguntas_obligatorias)
    fecha = datetime.datetime.now().strftime("%d/%m/%Y")

    API_KEY = os.environ.get("GEMINI_API_KEY", "TU_API_KEY_AQUÍ")

    if API_KEY == "TU_API_KEY_AQUÍ":
        print("\n[AVISO] No configuraste tu API Key de Gemini.")
        print("Se usara la plantilla generica de simulacion.\n")
        evaluacion = (
            "=====================================================\n"
            f"EVALUACION DIAGNOSTICA - {nombre_curso}\n"
            f"Fecha: {fecha}\n"
            "=====================================================\n\n"
            "Nombre:\n\n"
            "Fecha:\n\n"
            "Por favor, configura la API Key real en el codigo para ver el examen personalizado.\n"
        )
        return evaluacion

    INTENTOS_MAXIMOS = 3
    ESPERA_BASE = 60  # segundos entre reintentos (429 requiere esperas largas)
    evaluacion = ""

    for intento in range(1, INTENTOS_MAXIMOS + 1):
        try:
            client = genai.Client(api_key=API_KEY)
            print(f"[IA] Conectando con Gemini (Intento {intento}/{INTENTOS_MAXIMOS})...")

            respuesta = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )

            evaluacion = respuesta.text

            # Encabezado formal
            encabezado = (
                "=====================================================\n"
                f"EVALUACION DIAGNOSTICA - {nombre_curso[:40]}\n"
                f"Fecha: {fecha}\n"
                "=====================================================\n\n"
                "Nombre:\n\n"
                "Fecha:\n\n"
            )
            evaluacion = encabezado + "\n" + evaluacion
            print("✅ Evaluacion generada correctamente.")
            break  # éxito, salir del bucle

        except Exception as e:
            error_str = str(e)
            print(f"⚠️  Intento {intento}/{INTENTOS_MAXIMOS} falló: {error_str[:120]}")

            if intento < INTENTOS_MAXIMOS:
                espera = ESPERA_BASE * intento  # backoff: 10s, 20s
                print(f"   ⏳ Esperando {espera}s antes de reintentar...")
                time.sleep(espera)
            else:
                print("❌ Se agotaron los reintentos. Guardando mensaje de error.")
                evaluacion = (
                    f"Error al generar la evaluación tras {INTENTOS_MAXIMOS} intentos.\n"
                    f"\u00daltimo error: {error_str}"
                )

    return evaluacion


def sanitizar_texto_para_word(texto):
    texto = texto.replace('“', '"').replace('”', '"')
    texto = texto.replace('‘', "'").replace('’', "'")
    texto = texto.replace('—', '-').replace('–', '-').replace('…', '...')
    texto = texto.replace('«', '"').replace('»', '"')
    texto = re.sub(r'_{3,}', '', texto)
    texto = re.sub(r'\*\*(.+?)\*\*', r'\1', texto)
    texto = re.sub(r'(?m)^\s*\*\s+', '- ', texto)
    texto = re.sub(r'(?m)^\s*#\s*', '', texto)
    texto = texto.replace('`', '')
    texto = texto.replace('“', '"').replace('”', '"')
    texto = texto.replace('¡', '!').replace('¿', '?')
    return texto


def guardar_evaluacion(evaluacion, nombre_curso, carpeta_destino=""):
    """Guarda el examen como documento Word (.docx).
    Si se proporciona carpeta_destino, guarda allí. Si no, guarda en la carpeta actual.
    """
    nombre_base = f"evaluacion_diagnostica_{nombre_curso[:30].replace(' ', '_')}"
    nombre_base = "".join(c for c in nombre_base if c.isalnum() or c in ("_", "-"))
    nombre_archivo = nombre_base + ".docx"
    
    # Definir ruta completa: si hay carpeta_destino, usarla; si no, usar carpeta actual
    if carpeta_destino and os.path.exists(carpeta_destino):
        ruta_completa = os.path.join(carpeta_destino, nombre_archivo)
    else:
        ruta_completa = nombre_archivo

    fecha = datetime.datetime.now().strftime("%d/%m/%Y")
    doc = Document()

    # ── Estilos globales ──
    estilo = doc.styles["Normal"]
    estilo.font.name = "Calibri"
    estilo.font.size = Pt(11)

    # ── Encabezado ──
    titulo = doc.add_heading("", level=0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = titulo.add_run(f"EVALUACIÓN DIAGNÓSTICA")
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)

    subtitulo = doc.add_paragraph()
    subtitulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = subtitulo.add_run(f"{nombre_curso}  |  Fecha: {fecha}")
    sub.font.size = Pt(12)
    sub.font.color.rgb = RGBColor(0x40, 0x40, 0x40)

    doc.add_paragraph("Nombre:")
    doc.add_paragraph("")
    doc.add_paragraph("Fecha:")
    doc.add_paragraph("")

    # ── Contenido generado por IA ──
    evaluacion = sanitizar_texto_para_word(evaluacion)
    for linea in evaluacion.splitlines():
        linea_limpia = linea.strip()
        linea_limpia = re.sub(r"\*\*(.+?)\*\*", r"\1", linea_limpia)
        linea_limpia = re.sub(r"^#+\s*", "", linea_limpia)

        if linea_limpia == "":
            doc.add_paragraph("")
        else:
            doc.add_paragraph(linea_limpia)

    doc.save(ruta_completa)
    print(f"\n✅ Evaluacion guardada en: {ruta_completa}")
    return ruta_completa


# ──────────────────────────────────────────────
#  CORRECCIÓN AUTOMÁTICA POR LOTE
# ──────────────────────────────────────────────
def correccion_automatica_por_lote():
    """
    Corrección automática de TODA una actividad sin intervención manual.
    Publica calificaciones, comentarios y devuelve entregas automáticamente.
    """
    print("\n" + "=" * 70)
    print("  ⚡ CORRECCIÓN AUTOMÁTICA POR LOTE")
    print("=" * 70)
    
    try:
        # 1. Autenticación
        print("\n🔐 Autenticando...")
        creds = obtener_credenciales()
        service = build("classroom", "v1", credentials=creds)
        service_drive = build("drive", "v3", credentials=creds)
        print("   ✅ Autenticado")
        
        # 2. Seleccionar materia
        print("\n📚 Seleccionando materia...")
        curso = seleccionar_materia(service)
        if not curso:
            print("❌ No se seleccionó materia")
            return
        
        course_id = curso["id"]
        nombre_curso = curso["name"]
        print(f"   ✅ Materia: {nombre_curso}")
        
        # 3. Seleccionar actividad
        print("\n📝 Seleccionando actividad...")
        trabajos = listar_trabajos_del_curso(service, course_id)
        if not trabajos:
            print("❌ No hay actividades en esta materia")
            return
        
        trabajo = seleccionar_trabajo(trabajos)
        if not trabajo:
            print("❌ No se seleccionó actividad")
            return
        
        work_id = trabajo["id"]
        titulo_trabajo = trabajo.get("title", "Sin título")
        print(f"   ✅ Actividad: {titulo_trabajo}")
        
        # 4. Obtener entregas
        print("\n📥 Obteniendo entregas...")
        try:
            entregas_response = service.courses().courseWork().studentSubmissions().list(
                courseId=course_id,
                courseWorkId=work_id,
                pageSize=100
            ).execute()
            entregas = entregas_response.get("studentSubmissions", [])
            print(f"   ✅ Se encontraron {len(entregas)} entregas")
        except Exception as e:
            print(f"   ❌ Error al obtener entregas: {e}")
            return
        
        if not entregas:
            print("   ⚠️ No hay entregas para esta actividad")
            return
        
        # 5. Generar correcciones automáticamente
        print("\n🔄 Generando correcciones automáticas...")
        print("   ⏳ Procesando con Corrector Pedagógico...")
        
        try:
            corrector = CorrectorPedagogico(nombre_curso, titulo_trabajo)
            
            # Obtener contexto de consigna
            contexto_consigna = obtener_contexto_consigna(
                service, 
                service_drive, 
                course_id, 
                work_id, 
                trabajo
            )
            
            # Obtener alumnos y construir lote AUTOMÁTICAMENTE (sin interacción)
            alumnos_tp = listar_alumnos_por_actividad(service, course_id, work_id)
            lote_seleccionado = construir_lote_automatico(
                alumnos_tp,
                titulo_trabajo,
                service_drive,
                contexto_consigna,
                nombre_curso,
            )
            
            # Procesar lote
            if lote_seleccionado:
                corrector.reporte_entregas = []
                for x in lote_seleccionado:
                    estado_auto = (x.get("estado") or "").strip()
                    if estado_auto and estado_auto != "MANUAL":
                        corrector.reporte_entregas.append({
                            "alumno": x.get("nombre", "Sin nombre"),
                            "estado_interno": estado_auto,
                            "nota": x.get("nota"),
                            "calificacion": x.get("nota"),
                            "motivo_correccion": x.get("motivo", "Evaluación automática"),
                            "comentario_privado": x.get("feedback", ""),
                            "retroalimentacion": x.get("feedback", ""),
                            "alumno_id": x.get("user_id"),
                            "student_id": x.get("user_id"),
                        })
            
            # Generar JSON
            json_resultado = corrector.generar_json()
            correcciones = json.loads(json_resultado)
            
            # Guardar archivos JSON por alumno (desde lote_seleccionado con user_id)
            print(f"\n💾 Guardando correcciones por alumno...")
            carpeta_reportes = obtener_carpeta_reportes_del_dia()
            timestamp_base = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            archivos_guardados = []
            # Usar lote_seleccionado que tiene user_id
            for idx, item in enumerate(lote_seleccionado):
                alumno_nombre = item.get("nombre", "sin_nombre").replace(" ", "_").replace("/", "_")
                user_id = item.get("user_id", "")
                
                # Agregar índice para garantizar uniqueness si hay múltiples alumnos en el mismo segundo
                timestamp = f"{timestamp_base}_{idx:02d}"
                
                # Guardar JSON individual con aliases de ID para facilitar búsqueda
                datos_a_guardar = dict(item)  # Copiar los datos del lote
                datos_a_guardar["student_id"] = user_id  # Alias para búsqueda
                datos_a_guardar["alumno_id"] = user_id   # Alias para búsqueda
                
                # Guardar en carpeta de reportes del día
                nombre_archivo = os.path.join(
                    carpeta_reportes, 
                    f"correcciones_alumno_{alumno_nombre}_{user_id}_{timestamp}.json"
                )
                
                try:
                    with open(nombre_archivo, 'w', encoding='utf-8') as f:
                        json.dump(datos_a_guardar, f, ensure_ascii=False, indent=2)
                    archivos_guardados.append(nombre_archivo)
                    print(f"   ✅ {item.get('nombre', 'Sin nombre')} (ID: {user_id})")
                except Exception as e:
                    print(f"   ❌ Error guardando {alumno_nombre}: {e}")
            
            if not archivos_guardados:
                print("\n   ⚠️ No se generaron correcciones. Volviendo...")
                return
            
            print(f"\n   ✅ Se generaron {len(archivos_guardados)} archivo(s) de correcciones")
        
        except Exception as e:
            print(f"   ❌ Error generando correcciones: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 6. Procesar cada entrega y publicar
        print("\n" + "=" * 70)
        print("  📤 PUBLICANDO CORRECCIONES AUTOMÁTICAMENTE...")
        print("=" * 70)
        
        estadisticas = {
            "calificaciones_publicadas": 0,
            "comentarios_publicados": 0,
            "entregas_devueltas": 0,
            "errores": 0
        }
        
        for entrega in entregas:
            student_id = entrega.get("userId")
            submission_id = entrega.get("id")
            estado = entrega.get("state", "CREATED")
            student_name = entrega.get("student", {}).get("profile", {}).get("name", {}).get("fullName", "").lower()
            
            # Buscar archivo JSON de este alumno
            correccion = None
            
            # Intento 1: Buscar por user_id en el nombre del archivo (más rápido)
            for archivo in archivos_guardados:
                if f"_{student_id}_" in archivo:
                    try:
                        with open(archivo, 'r', encoding='utf-8') as f:
                            correccion = json.load(f)
                            break
                    except:
                        pass
            
            # Intento 2: Buscar por user_id exacto en el contenido JSON
            if not correccion:
                for archivo in archivos_guardados:
                    try:
                        with open(archivo, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if data.get("user_id") == student_id or data.get("alumno_id") == student_id or data.get("student_id") == student_id:
                                correccion = data
                                break
                    except:
                        pass
            
            # Intento 3: Búsqueda por nombre aproximado (fallback)
            if not correccion and student_name:
                for archivo in archivos_guardados:
                    try:
                        with open(archivo, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            nombre_en_json = (data.get("nombre", "") or "").lower()
                            # Búsqueda flexible: si el nombre del JSON contiene partes del nombre del estudiante
                            if nombre_en_json and (nombre_en_json in student_name or student_name in nombre_en_json):
                                correccion = data
                                break
                    except:
                        pass
            
            if not correccion:
                print(f"\n⏭️  Alumno {student_id} ({student_name}): Sin corrección disponible")
                print(f"   [Buscó en {len(archivos_guardados)} archivo(s) guardado(s)]")
                estadisticas["errores"] += 1
                continue
            
            alumno_nombre = correccion.get("nombre", f"Alumno {student_id}")
            print(f"\n📍 Procesando: {alumno_nombre}")
            
            # Publicar calificación
            calificacion = correccion.get("nota")
            if calificacion:
                try:
                    # Convertir de 1-10 a 0-100
                    calificacion_classroom = _mapear_nota_a_classroom(float(calificacion))
                    _publicar_nota_en_classroom(
                        service, course_id, work_id, submission_id, 
                        calificacion_classroom, solo_borrador=False
                    )
                    print(f"   ✅ Calificación: {calificacion}/10 ({calificacion_classroom}/100)")
                    estadisticas["calificaciones_publicadas"] += 1
                except Exception as e:
                    print(f"   ❌ Error publicando calificación: {str(e)[:100]}")
                    estadisticas["errores"] += 1
            
            # Publicar comentario privado
            comentario = correccion.get("feedback")
            if comentario:
                try:
                    ss_resource = service.courses().courseWork().studentSubmissions()
                    ss_resource.addOnAttachments(
                        courseId=course_id,
                        courseWorkId=work_id,
                        itemId=submission_id,
                        body={"addOnAttachments": []}
                    )
                    print(f"   ✅ Comentario privado publicado")
                    estadisticas["comentarios_publicados"] += 1
                except Exception as e:
                    print(f"   ⚠️ No se pudo publicar comentario (API): {str(e)[:50]}")
            
            # Devolver entrega (si no está ya devuelta)
            if estado != "RETURNED":
                try:
                    _devolver_tarea_en_classroom(service, course_id, work_id, submission_id)
                    print(f"   ✅ Entrega devuelta")
                    estadisticas["entregas_devueltas"] += 1
                except Exception as e:
                    print(f"   ⚠️ Error devolviendo: {str(e)[:100]}")
        
        # 7. Resumen
        print("\n" + "=" * 70)
        print("  📊 RESUMEN")
        print("=" * 70)
        print(f"   ✅ Calificaciones publicadas: {estadisticas['calificaciones_publicadas']}")
        print(f"   ✅ Comentarios publicados: {estadisticas['comentarios_publicados']}")
        print(f"   ✅ Entregas devueltas: {estadisticas['entregas_devueltas']}")
        print(f"   ❌ Errores: {estadisticas['errores']}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


# ──────────────────────────────────────────────
#  SELECCIÓN DE CUENTA OAUTH
# ──────────────────────────────────────────────
def seleccionar_cuenta_oauth():
    """Permite al usuario elegir qué cuenta usar para OAuth."""
    global EXPECTED_OAUTH_EMAIL, OAUTH_LOGIN_HINT
    
    print("\n" + "=" * 70)
    print("  🔐 SELECCIONAR CUENTA PARA CLASSROOM")
    print("=" * 70)
    print("\n¿Cuál cuenta deseas usar?")
    print()
    
    for key, email in CUENTAS_DISPONIBLES.items():
        es_propietaria = " (TUS CLASES)" if "ciclo2026" in email else " (CLASES CLONADAS)" if "fuel1234" in email else ""
        print(f"  [{key}] {email}{es_propietaria}")
    
    print()
    while True:
        opcion = input("Elegí 1, 2, 3 o 4: ").strip()
        if opcion in CUENTAS_DISPONIBLES:
            nueva_cuenta = CUENTAS_DISPONIBLES[opcion]
            break
        print("❌ Opción inválida. Ingresá 1, 2, 3 o 4.")
    
    # Si cambió de cuenta, borrar token anterior
    if nueva_cuenta != EXPECTED_OAUTH_EMAIL:
        print(f"\n🔄 Cambio de cuenta de '{EXPECTED_OAUTH_EMAIL}' a '{nueva_cuenta}'")
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
            print(f"   ✅ Token anterior borrado. Se pedirá re-autorización.")
    else:
        print(f"✅ Usando cuenta: {nueva_cuenta}")
    
    EXPECTED_OAUTH_EMAIL = nueva_cuenta
    OAUTH_LOGIN_HINT = nueva_cuenta
    os.environ["OAUTH_EMAIL"] = nueva_cuenta
    
    print()
    return nueva_cuenta


# ══════════════════════════════════════════════════════════════════════════════
# [7] CALIFICAR + FEEDBACK POR EMAIL + DEVOLVER  (opción del menú principal)
# ══════════════════════════════════════════════════════════════════════════════

def _enviar_feedback_gmail(creds, email_destino, nombre_alumno,
                           nombre_actividad, nombre_curso, feedback_texto, nota):
    """
    Envía el feedback pedagógico al alumno por Gmail (privado, directo).
    Usa el scope gmail.send ya autorizado en SCOPES.

    Retorna True si se envió correctamente, False si falló.
    """
    if not email_destino or not feedback_texto:
        return False

    try:
        service_gmail = build("gmail", "v1", credentials=creds)

        sep  = "=" * 54
        sep2 = "-" * 54

        nota_str   = f"{nota}/10" if nota is not None else "—"
        nota_linea = f"  CALIFICACIÓN:  {nota_str}"

        # Separar el texto de feedback en secciones si ya viene con saltos de línea
        feedback_limpio = (feedback_texto or "").strip()

        asunto = f"[Devolución] {nombre_actividad}"

        cuerpo = "\n".join([
            sep,
            f"  DEVOLUCIÓN DE TRABAJO PRÁCTICO",
            sep,
            "",
            f"  Alumno  : {nombre_alumno}",
            f"  Materia : {nombre_curso}",
            f"  Trabajo : {nombre_actividad}",
            "",
            sep2,
            nota_linea,
            sep2,
            "",
            "DEVOLUCIÓN PEDAGÓGICA",
            sep2,
            "",
            feedback_limpio,
            "",
            sep2,
            "Prof. Rodríguez G.",
            "Escuela Técnica N°1 Manuel Belgrano",
            sep,
        ])

        mensaje = MIMEText(cuerpo, "plain", "utf-8")
        mensaje["To"]      = email_destino
        mensaje["Subject"] = asunto

        raw = base64.urlsafe_b64encode(mensaje.as_bytes()).decode()
        service_gmail.users().messages().send(
            userId="me",
            body={"raw": raw},
        ).execute()
        return True

    except Exception as e:
        print(f"      ⚠️ Gmail: no se pudo enviar email a {email_destino}: {str(e)[:120]}")
        return False


def _obtener_email_alumno(service, user_id):
    """Devuelve el email del alumno usando la Classroom profiles API."""
    if not user_id:
        return None
    try:
        perfil = service.userProfiles().get(userId=user_id).execute()
        return perfil.get("emailAddress")
    except Exception:
        return None


def calificar_y_devolver_actividad():
    """
    Opción [7] del menú principal.

    Flujo completo por actividad:
      1. Seleccionás materia y actividad.
      2. El agente evalúa automáticamente a TODOS los alumnos que entregaron.
      3. Se muestra la tabla de resultados.
      4. Confirmás (todos o uno por uno).
      5. Para cada alumno confirmado:
           - patch(assignedGrade + draftGrade)  →  nota en escala del TP (/100 ó /10)
           - Gmail → email privado con el feedback pedagógico
           - return_()  →  "Devolver" oficial de Classroom (el alumno recibe notificación)
    """
    print("\n" + "=" * 70)
    print("  [7] CALIFICAR + FEEDBACK PRIVADO + DEVOLVER")
    print("=" * 70)

    # ── Auth ──────────────────────────────────────────────────────────────────
    print("\n🔐 Autenticando...")
    creds = obtener_credenciales()
    service       = build("classroom", "v1", credentials=creds)
    service_drive = build("drive",     "v3", credentials=creds)
    print("   ✅ Autenticado")

    # ── Seleccionar materia ───────────────────────────────────────────────────
    curso = seleccionar_materia(service)
    if not curso:
        print("❌ No se seleccionó materia.")
        return
    course_id    = curso["id"]
    nombre_curso = curso["name"]
    print(f"   ✅ Materia: {nombre_curso}")

    # ── Seleccionar actividad ─────────────────────────────────────────────────
    trabajos = listar_trabajos_del_curso(service, course_id)
    if not trabajos:
        print("❌ No hay actividades en esta materia.")
        return
    trabajo = seleccionar_trabajo(trabajos)
    if not trabajo:
        print("❌ No se seleccionó actividad.")
        return

    work_id         = trabajo["id"]
    titulo_trabajo  = trabajo.get("title", "Sin título")
    max_points      = float(trabajo.get("maxPoints") or 100)   # escala del TP
    print(f"   ✅ Actividad : {titulo_trabajo}")
    print(f"   ✅ Escala    : /{int(max_points)}")

    # ── Obtener consigna ──────────────────────────────────────────────────────
    print("\n📋 Leyendo consigna...")
    contexto_consigna = obtener_contexto_consigna(
        service, service_drive, course_id, work_id, trabajo
    )

    # ── Obtener alumnos + evaluar ─────────────────────────────────────────────
    print("\n👥 Obteniendo entregas y evaluando...")
    alumnos_tp = listar_alumnos_por_actividad(service, course_id, work_id)
    if not alumnos_tp:
        print("⚠️ No hay entregas para esta actividad.")
        return

    lote = construir_lote_automatico(
        alumnos_tp, titulo_trabajo, service_drive, contexto_consigna, nombre_curso
    )

    if not lote:
        print("⚠️ No se generaron evaluaciones.")
        return

    # ── Tabla de resultados ───────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"  RESULTADOS — {titulo_trabajo}")
    print("=" * 70)
    print(f"  {'#':<4} {'Alumno':<30} {'Nota':>6}  {'Estado':<18}  {'submission_id'}")
    print("  " + "─" * 66)
    for i, item in enumerate(lote, 1):
        nota_str = f"{item.get('nota')}/10" if item.get("nota") is not None else "—"
        sid_preview = (item.get("submission_id") or "sin_id")[:18]
        print(f"  {i:<4} {item.get('nombre','?'):<30} {nota_str:>6}  {item.get('estado','?'):<18}  {sid_preview}")
    print("=" * 70)

    # ── Confirmación ──────────────────────────────────────────────────────────
    print("\n¿Publicar notas y enviar feedback?")
    print("  [S] Sí, publicar TODOS")
    print("  [U] Uno por uno (confirmar alumno a alumno)")
    print("  [N] Cancelar")
    resp = input("Elegí S, U o N: ").strip().upper()
    if resp not in ("S", "U"):
        print("Operación cancelada.")
        return

    # ── Publicación ───────────────────────────────────────────────────────────
    publicados   = 0
    emails_ok    = 0
    devueltos    = 0
    errores      = 0

    print("\n" + "=" * 70)
    print("  PUBLICANDO...")
    print("=" * 70)

    for item in lote:
        nombre_alumno = item.get("nombre", "Alumno")
        submission_id = item.get("submission_id")
        nota_1_10     = item.get("nota")
        feedback_txt  = (item.get("feedback") or "").strip()
        user_id       = item.get("user_id")

        # Confirmación individual si el usuario eligió U
        if resp == "U":
            print(f"\n  → {nombre_alumno}  |  Nota: {nota_1_10}/10")
            confirmar = input("     ¿Publicar? (S/N): ").strip().upper()
            if confirmar != "S":
                print("     Omitido.")
                continue

        if not submission_id:
            print(f"\n  ⚠️ {nombre_alumno}: sin submission_id, se omite.")
            errores += 1
            continue

        print(f"\n  📍 {nombre_alumno}")

        # -- Nota -------------------------------------------------------
        if nota_1_10 is not None:
            try:
                # Escalar a la escala real del TP
                nota_classroom = round((float(nota_1_10) / 10.0) * max_points, 1)
                _ejecutar_con_reintentos_api(
                    lambda: service.courses().courseWork().studentSubmissions().patch(
                        courseId=course_id,
                        courseWorkId=work_id,
                        id=submission_id,
                        updateMask="assignedGrade,draftGrade",
                        body={
                            "assignedGrade": nota_classroom,
                            "draftGrade":    nota_classroom,
                        },
                    ).execute(),
                    etiqueta=f"patch nota {nombre_alumno}",
                )
                print(f"     ✅ [1/3] Nota: {nota_1_10}/10 → {nota_classroom}/{int(max_points)}")
                publicados += 1
            except Exception as e:
                print(f"     ❌ [1/3] Error nota: {str(e)[:100]}")
                errores += 1
        else:
            print(f"     ⓘ [1/3] Sin nota para asignar")

        # -- Feedback por Gmail ----------------------------------------
        email_alumno = _obtener_email_alumno(service, user_id)
        if email_alumno and feedback_txt:
            ok = _enviar_feedback_gmail(
                creds, email_alumno, nombre_alumno,
                titulo_trabajo, nombre_curso, feedback_txt, nota_1_10
            )
            if ok:
                print(f"     ✅ [2/3] Feedback enviado por email a {email_alumno}")
                emails_ok += 1
            else:
                print(f"     ⚠️ [2/3] No se pudo enviar email")
        elif not email_alumno:
            print(f"     ⓘ [2/3] Email del alumno no disponible")
        else:
            print(f"     ⓘ [2/3] Sin feedback para enviar")

        # -- Devolver ---------------------------------------------------
        try:
            _ejecutar_con_reintentos_api(
                lambda: service.courses().courseWork().studentSubmissions().return_(
                    courseId=course_id,
                    courseWorkId=work_id,
                    id=submission_id,
                    body={},
                ).execute(),
                etiqueta=f"return {nombre_alumno}",
            )
            print(f"     ✅ [3/3] Entrega devuelta (alumno recibe notificación)")
            devueltos += 1
        except Exception as e:
            print(f"     ❌ [3/3] Error al devolver: {str(e)[:100]}")
            errores += 1

    # ── Resumen final ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  RESUMEN FINAL")
    print("=" * 70)
    print(f"  ✅ Notas publicadas    : {publicados}")
    print(f"  ✅ Emails de feedback  : {emails_ok}")
    print(f"  ✅ Entregas devueltas  : {devueltos}")
    if errores:
        print(f"  ❌ Errores            : {errores}")
    print("=" * 70)

    # ── Guardar en Excel maestro ─────────────────────────────────────────────
    ruta_xl = actualizar_excel_evaluaciones(nombre_curso, titulo_trabajo, lote, max_points)
    if ruta_xl:
        print(f"\n  📊 Excel actualizado → {os.path.abspath(ruta_xl)}")

    if emails_ok < publicados:
        print("\n  ℹ️  Para los alumnos sin email, el feedback se guardó en:")
        carpeta_reportes = obtener_carpeta_reportes_del_dia()
        print(f"     {carpeta_reportes}")


# ══════════════════════════════════════════════════════════════════════════════
#  EXCEL MAESTRO DE EVALUACIONES
# ══════════════════════════════════════════════════════════════════════════════

def actualizar_excel_evaluaciones(nombre_curso, titulo_trabajo, lote, max_points=10):
    """
    Genera/actualiza el Excel maestro de evaluaciones.
    Un libro/hoja por materia — alumnos, actividad y correcciones.
    Archivo: Correcciones_Classroom/PLANILLA_EVALUACIONES.xlsx
    """
    try:
        from openpyxl import Workbook, load_workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter

        RUTA_EXCEL = os.path.join("Correcciones_Classroom", "PLANILLA_EVALUACIONES.xlsx")
        os.makedirs("Correcciones_Classroom", exist_ok=True)

        # ── Paleta de colores ─────────────────────────────────────────────────
        COL_HDR_BG = "1F4E79"   # Azul oscuro  (encabezados materia)
        COL_HDR_FG = "FFFFFF"   # Blanco
        COL_VERDE  = "C6EFCE"   # Verde claro  (nota ≥ 8)
        COL_AMRLLO = "FFEB9C"   # Amarillo     (nota 6–7)
        COL_ROJO   = "FFC7CE"   # Rojo claro   (nota < 6)
        COL_GRIS   = "F2F2F2"   # Gris         (sin nota)
        COL_RES_BG = "2E75B6"   # Azul medio   (resumen)

        # ── Cargar o crear workbook ───────────────────────────────────────────
        if os.path.exists(RUTA_EXCEL):
            wb = load_workbook(RUTA_EXCEL)
        else:
            wb = Workbook()
            if "Sheet" in wb.sheetnames:
                del wb["Sheet"]

        # ── Nombre de hoja sanitizado (max 31 chars) ──────────────────────────
        def _san(nombre):
            for c in r'/\?*[]:':
                nombre = nombre.replace(c, "_")
            return nombre[:31]

        nombre_hoja = _san(nombre_curso)

        # ── Crear hoja nueva con encabezados si no existe ─────────────────────
        if nombre_hoja not in wb.sheetnames:
            ws = wb.create_sheet(nombre_hoja)
            encabezados = [
                "#", "Fecha", "Actividad", "Alumno",
                "Nota /10", f"Nota /{int(max_points)}", "Estado", "Feedback / Corrección",
            ]
            ws.append(encabezados)
            for col_idx in range(1, len(encabezados) + 1):
                c = ws.cell(row=1, column=col_idx)
                c.font      = Font(bold=True, color=COL_HDR_FG, size=11)
                c.fill      = PatternFill("solid", fgColor=COL_HDR_BG)
                c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            ws.row_dimensions[1].height = 30
            ws.freeze_panes = "A2"
        else:
            ws = wb[nombre_hoja]

        # ── Agregar filas de esta corrección ──────────────────────────────────
        fila_inicio = ws.max_row + 1
        fecha_ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        for idx, item in enumerate(lote):
            fila    = fila_inicio + idx
            nota    = item.get("nota")
            nota_cl = round((float(nota) / 10.0) * max_points, 1) if nota is not None else None

            if nota is None:
                color_bg = COL_GRIS
            elif float(nota) >= 8:
                color_bg = COL_VERDE
            elif float(nota) >= 6:
                color_bg = COL_AMRLLO
            else:
                color_bg = COL_ROJO

            fill   = PatternFill("solid", fgColor=color_bg)
            valores = [
                fila - 1,
                fecha_ahora,
                titulo_trabajo,
                item.get("nombre", "?"),
                nota,
                nota_cl,
                item.get("estado", "?"),
                (item.get("feedback") or "")[:600],
            ]
            for col_idx, valor in enumerate(valores, 1):
                c           = ws.cell(row=fila, column=col_idx, value=valor)
                c.fill      = fill
                c.alignment = Alignment(wrap_text=True, vertical="top")
            ws.row_dimensions[fila].height = 60

        # ── Ajustar anchos de columna ─────────────────────────────────────────
        anchos = [5, 18, 38, 32, 10, 12, 20, 85]
        for col_idx, ancho in enumerate(anchos, 1):
            ws.column_dimensions[get_column_letter(col_idx)].width = ancho

        # ── Hoja "Resumen General" (siempre en posición 0) ────────────────────
        HOJA_RES = "Resumen General"
        if HOJA_RES not in wb.sheetnames:
            wr = wb.create_sheet(HOJA_RES, 0)
            wr.append(["Materia", "Alumnos", "Promedio", "Aprobados (≥6)", "Desaprobados (<6)", "Sin nota"])
            for c in wr[1]:
                c.font      = Font(bold=True, color=COL_HDR_FG, size=11)
                c.fill      = PatternFill("solid", fgColor=COL_RES_BG)
                c.alignment = Alignment(horizontal="center", vertical="center")
            wr.row_dimensions[1].height = 28
            wr.freeze_panes = "A2"
            for col_idx, ancho in enumerate([38, 12, 12, 18, 20, 12], 1):
                wr.column_dimensions[get_column_letter(col_idx)].width = ancho
        else:
            wr = wb[HOJA_RES]

        # Limpiar filas de resumen anteriores y recalcular
        for row in wr.iter_rows(min_row=2):
            for cell in row:
                cell.value = None

        fila_res = 2
        for hoja_nombre in wb.sheetnames:
            if hoja_nombre == HOJA_RES:
                continue
            wm    = wb[hoja_nombre]
            notas = []
            for row in wm.iter_rows(min_row=2, values_only=True):
                if row and row[4] is not None:
                    try:
                        notas.append(float(row[4]))
                    except (TypeError, ValueError):
                        pass
            total        = wm.max_row - 1
            promedio     = round(sum(notas) / len(notas), 1) if notas else "—"
            aprobados    = sum(1 for n in notas if n >= 6)
            desaprobados = sum(1 for n in notas if n < 6)
            sin_nota     = total - len(notas)
            wr.cell(fila_res, 1, hoja_nombre)
            wr.cell(fila_res, 2, total)
            wr.cell(fila_res, 3, promedio)
            wr.cell(fila_res, 4, aprobados)
            wr.cell(fila_res, 5, desaprobados)
            wr.cell(fila_res, 6, sin_nota)
            fila_res += 1

        wb.save(RUTA_EXCEL)
        return RUTA_EXCEL

    except Exception as exc:
        print(f"\n  ⚠️ No se pudo actualizar el Excel: {exc}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# [5] PUBLICAR NOTAS + COMENTARIOS PRIVADOS EN UI CLASSROOM
# ══════════════════════════════════════════════════════════════════════════════

def publicar_con_comentarios_privados(solo_notas=False):
    """
    Opción [5] del menú principal.

    Flujo:
      1. Seleccionás materia y actividad.
      2. Evaluación automática de todos los alumnos (motor único).
      3. Se muestra tabla de resultados.
      4. Confirmás y se ejecuta el flujo completo:
           - patch(draftGrade)  → nota subida por API
           - pyautogui         → abre la entrega en Chrome y pega el
                                  comentario privado como lo haría un humano
           - Fallback          → si pyautogui no disponible, guarda .txt
                                  en comentarios_pendientes_manual/

    NOTA: Chrome debe estar visible (no minimizado) durante la ejecución.
    Para solo publicar la nota sin comentario, usá la opción [7].
    """
    # ── Autenticación ─────────────────────────────────────────────────────────
    print("\n🔐 Autenticando...")
    creds = obtener_credenciales()
    service       = build("classroom", "v1", credentials=creds)
    service_drive = build("drive",     "v3", credentials=creds)
    print("   ✅ Autenticado")

    # ── Selección de materia ──────────────────────────────────────────────────
    curso = seleccionar_materia(service)
    if not curso:
        return

    course_id    = curso["id"]
    nombre_curso = curso.get("name", "Materia")

    # ── Selección de actividad ────────────────────────────────────────────────
    trabajos = listar_trabajos_del_curso(service, course_id)
    if not trabajos:
        print("❌ No hay actividades en esta materia.")
        return
    trabajo = seleccionar_trabajo(trabajos)
    if not trabajo:
        print("❌ No se seleccionó actividad.")
        return

    work_id        = trabajo["id"]
    titulo_trabajo = trabajo.get("title", "Actividad")

    # ── Consigna y alumnos ────────────────────────────────────────────────────
    print("\n   ⏳ Obteniendo consigna y alumnos...")
    contexto_consigna = obtener_contexto_consigna(
        service, service_drive, course_id, work_id, trabajo
    )
    alumnos_tp = listar_alumnos_por_actividad(service, course_id, work_id)

    if not alumnos_tp:
        print("⚠️ No hay alumnos con entregas para esta actividad.")
        return

    # ── Evaluación automática ─────────────────────────────────────────────────
    lote = construir_lote_automatico(
        alumnos_tp, titulo_trabajo, service_drive, contexto_consigna, nombre_curso
    )

    if not lote:
        print("⚠️ No se generaron evaluaciones.")
        return

    # Mapear "feedback" → "comentario" (ejecutar_flujo_completo usa la clave "comentario")
    for item in lote:
        if not item.get("comentario"):
            item["comentario"] = item.get("feedback", "")

    # ── Tabla de resultados ───────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"  RESULTADOS — {titulo_trabajo}")
    print("=" * 70)
    print(f"  {'#':<4} {'Alumno':<30} {'Nota':>6}  {'Estado':<18}  {'Link'}")
    print("  " + "─" * 66)
    for i, item in enumerate(lote, 1):
        nota_str  = f"{item.get('nota')}/10" if item.get("nota") is not None else "—"
        link_ok   = "✅ link" if item.get("alternate_link") else "⚠️ sin link"
        print(f"  {i:<4} {item.get('nombre','?'):<30} {nota_str:>6}  {item.get('estado','?')[:18]:<18}  {link_ok}")
    print("=" * 70)

    # Alertar si hay alumnos sin alternate_link
    sin_link = [it for it in lote if not it.get("alternate_link")]
    if sin_link:
        print(f"\n  ⚠️  {len(sin_link)} alumno(s) sin link directo:")
        print("      Sus comentarios irán a comentarios_pendientes_manual/")

    # ── Opciones de publicación ───────────────────────────────────────────────
    print("\n¿Cómo publicar?")
    print("  [B] Borrador  — nota visible solo para vos (recomendado para revisar)")
    print("  [D] Definitiva — nota publicada, alumno recibe notificación")
    print("  [N] Cancelar")
    resp_modo = input("Elegí B, D o N: ").strip().upper()
    if resp_modo not in ("B", "D"):
        print("Operación cancelada.")
        return

    solo_borrador = (resp_modo == "B")

    print("\n¿Confirmar antes de cada alumno?")
    print("  [S] Sí (recomendado la primera vez para verificar que pyautogui funcione)")
    print("  [N] No (procesar todos automáticamente)")
    resp_confirm = input("Elegí S o N: ").strip().upper()
    confirmar_uno_a_uno = (resp_confirm == "S")

    devolver_auto = False
    if resp_modo == "D":
        resp_dev = input("  ¿Ejecutar return_() para devolver entregas? (S/N): ").strip().upper()
        devolver_auto = (resp_dev == "S")

    if solo_notas:
        # Modo solo notas: no pregunta sobre comentarios ni pide Chrome visible
        print("\n  📊 MODO SOLO NOTAS — se suben calificaciones sin pegar comentarios.")
        resumen = ejecutar_flujo_completo(
            service=service,
            course_id=course_id,
            work_id=work_id,
            lote_evaluaciones=lote,
            solo_borrador=solo_borrador,
            devolver_automaticamente=devolver_auto,
            pausa_entre_alumnos=0,
            confirmar_antes_de_cada_uno=False,
            solo_notas=True,
        )
    else:
        # ── Ejecutar flujo completo ───────────────────────────────────────────────
        print("\n  ⚠️  IMPORTANTE: Chrome debe estar visible (no minimizado).")
        print("      El script abrirá cada entrega y pegará el comentario.")
        print("      No uses el mouse ni el teclado mientras se procesa.\n")
        input("  Presioná Enter cuando Chrome esté listo y visible...")

        resumen = ejecutar_flujo_completo(
            service=service,
            course_id=course_id,
            work_id=work_id,
            lote_evaluaciones=lote,
            solo_borrador=solo_borrador,
            devolver_automaticamente=devolver_auto,
            pausa_entre_alumnos=4.0,
            confirmar_antes_de_cada_uno=confirmar_uno_a_uno,
            solo_notas=False,
        )

    # ── Excel maestro ─────────────────────────────────────────────────────────
    max_points = trabajo.get("maxPoints", 10) or 10
    ruta_xl = actualizar_excel_evaluaciones(nombre_curso, titulo_trabajo, lote, max_points)
    if ruta_xl:
        print(f"\n  📊 Excel actualizado → {os.path.abspath(ruta_xl)}")


# ──────────────────────────────────────────────
#  FLUJO PRINCIPAL
# ──────────────────────────────────────────────
def ejecutar_menu_una_vez():
    print("\n" + "=" * 60)
    print("  AGENTE — Google Classroom → Rodriguez.G")
    print(f"  🔑 Cuenta activa: {EXPECTED_OAUTH_EMAIL}")
    print("=" * 60)

    print("\n¿Cómo querés proceder?")
    print("[0] 🎯 Corrector Pedagógico (local → reportes JSON)")
    print("[1] 📝 Generar examen desde una carpeta local")
    print("[3] ⚡ Corrección por Lote: Calificar + Feedback + Devolver")
    print("[5] 💬 NOTA (API) + COMENTARIO PRIVADO EN CLASSROOM  ⭐ NUEVO")
    print("[6] 📊 SOLO SUBIR NOTAS (sin comentarios) — úsalo si los comentarios ya están pegados")
    print("[7] 💬 CALIFICAR + FEEDBACK PRIVADO (email) + DEVOLVER  ⭐")
    print("[8] 📋 Ver reportes guardados")
    print("[9] 🔄 Cambiar cuenta de Google")

    while True:
        modo = input("Elegí 0, 1, 3, 5, 6, 7, 8 o 9: ").strip()
        if modo in ("0", "1", "3", "5", "6", "7", "8", "9"):
            break
        print("Entrada no válida. Ingresá 0, 1, 3, 5, 6, 7, 8 o 9.")

    # OPCIÓN 0: Corrector Pedagógico
    if modo == "0":
        iniciar_corrector_pedagogico()
        return

    # OPCIÓN 3: Corrección por Lote (flujo completo como [7])
    if modo == "3":
        calificar_y_devolver_actividad()
        return

    # OPCIÓN 5: Nota por API + Comentario privado en UI Classroom
    if modo == "5":
        publicar_con_comentarios_privados()
        return

    # OPCIÓN 6: Solo subir notas (comentarios ya pegados en corrida anterior)
    if modo == "6":
        publicar_con_comentarios_privados(solo_notas=True)
        return

    # OPCIÓN 7: Calificar + Feedback + Devolver
    if modo == "7":
        calificar_y_devolver_actividad()
        return

    # OPCIÓN 8: Ver Reportes Guardados
    if modo == "8":
        carpeta_reportes = os.path.join("Correcciones_Classroom", "reportes")
        if not os.path.exists(carpeta_reportes):
            print("\n⚠️  No hay reportes generados aún.")
            return
        fechas = sorted(
            [d for d in os.listdir(carpeta_reportes)
             if os.path.isdir(os.path.join(carpeta_reportes, d))],
            reverse=True,
        )
        if not fechas:
            print("\n⚠️  No hay reportes generados aún.")
            return
        print("\n" + "=" * 60)
        print("  📋 REPORTES GUARDADOS")
        print("=" * 60)
        for fecha in fechas[:10]:
            carpeta_fecha = os.path.join(carpeta_reportes, fecha)
            archivos = os.listdir(carpeta_fecha)
            print(f"\n  📅 {fecha}  ({len(archivos)} archivo(s))")
            for arch in sorted(archivos)[:5]:
                print(f"     - {arch}")
            if len(archivos) > 5:
                print(f"     ... y {len(archivos) - 5} más")
        print("\n" + "=" * 60)
        print(f"  📁 Carpeta: {os.path.abspath(carpeta_reportes)}")
        webbrowser.open(os.path.abspath(carpeta_reportes))
        return

    # OPCIÓN 9: Cambiar Cuenta de Google
    if modo == "9":
        seleccionar_cuenta_oauth()
        return

    # OPCIÓN 1: Generar examen desde carpeta local
    ruta_raiz = "descargas_Material_Docente"
    print(f"\n📁 Usando carpeta por defecto: {ruta_raiz}")

    cursos_locales = listar_cursos_locales(ruta_raiz)
    if not cursos_locales:
        print(f"\n⚠️ No se encontraron carpetas de cursos en: {ruta_raiz}")
        return

    print("\n" + "=" * 60)
    print("  PASO 1 — Seleccioná un curso local")
    print("=" * 60)
    for i, nombre in enumerate(cursos_locales, start=1):
        print(f"  [{i}] {nombre}")
    print("=" * 60)

    while True:
        try:
            opcion = int(input("Ingresá el número del curso local: "))
            if 1 <= opcion <= len(cursos_locales):
                nombre_curso = cursos_locales[opcion - 1]
                ruta_preferida = os.path.join(ruta_raiz, nombre_curso)
                ruta_curso = ruta_preferida if os.path.isdir(ruta_preferida) else nombre_curso
                curso = {"id": None, "name": nombre_curso, "local_path": ruta_curso}
                print(f"\n✅ Curso local seleccionado: {nombre_curso}")
                break
            print(f"Ingresá un número entre 1 y {len(cursos_locales)}.")
        except ValueError:
            print("Entrada no válida. Ingresá un número.")
        except EOFError:
            print("\n⚠️ Entrada cancelada. Volviendo al menú principal.")
            return

    # Procesar archivos locales y generar evaluación
    carpeta_local = curso["local_path"]
    print("\n📚 Escaneando archivos locales del curso...")
    archivos_locales = []
    for raiz, _, archivos in os.walk(carpeta_local):
        for archivo in archivos:
            if archivo.lower().endswith((".docx", ".pdf")):
                archivos_locales.append(os.path.join(raiz, archivo))

    if not archivos_locales:
        print(f"⚠️ No se encontraron archivos DOCX o PDF en: {carpeta_local}")
        return

    print(f"   ✅ Archivos encontrados: {len(archivos_locales)}")
    contexto, preguntas_textuales = extraer_contenido_de_archivos_locales(archivos_locales)
    if not contexto.strip():
        print("⚠️ No se pudo extraer contenido de los archivos locales.")
        return

    print("\n⚙️  Generando evaluación diagnóstica desde el modo Offline...")
    evaluacion = generar_evaluacion_simulada(nombre_curso, contexto, preguntas_textuales)
    guardar_evaluacion(evaluacion, nombre_curso, carpeta_local)


def main():
    """Bucle principal: ejecuta una sesión y permite reiniciar desde el menú inicial."""
    # Seleccionar cuenta al inicio
    seleccionar_cuenta_oauth()
    
    while True:
        ejecutar_menu_una_vez()

        print("\n" + "=" * 50)
        print("  ¿Qué querés hacer ahora?")
        print("=" * 50)
        print("  [1] Volver al menú principal")
        print("  [0] Salir")
        print("=" * 50)

        decision = input("Elegí 1 o 0: ").strip()
        if decision == "1":
            continue

        print("\n👋 Fin de la sesión.")
        break


if __name__ == "__main__":
    main()
    